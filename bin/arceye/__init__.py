from __future__ import print_function
import sys, os
import yaml
from serial import Serial, SerialException
from time import sleep

#
# Logging util
#

def loginfo(*msg):
    print("INFO:", *msg)

def logerr(*msg):
    print("ERROR:", *msg, file=sys.stderr)


# The recipe gives simple implementation of a Discrete
# Proportional-Integral-Derivative (PID) controller. PID controller gives output
# value for error between desired reference input and measurement feedback to
# minimize error value.
# More information: http://en.wikipedia.org/wiki/PID_controller
# cnr437@gmail.com
#
#######	Example	#########
#
# p=PID(3.0,0.4,1.2)
# p.setPoint(5.0)
# while True:
#      pid = p.update(measurement_value)
class PID:
    """
    Discrete PID control
    """

    def __init__(self, P=1.0, I=0.0, D=1.0, Derivator=0, Integrator=0, Integrator_max=500, Integrator_min=-500):

        self.Kp=P
        self.Ki=I
        self.Kd=D
        self.Derivator=Derivator
        self.Integrator=Integrator
        self.Integrator_max=Integrator_max
        self.Integrator_min=Integrator_min

        self.set_point=0.0
        self.error=0.0

    def update(self,current_value):
        """
        Calculate PID output value for given reference input and feedback
        """

        self.error = self.set_point - current_value

        self.P_value = self.Kp * self.error
        self.D_value = self.Kd * ( self.error - self.Derivator)
        self.Derivator = self.error

        self.Integrator = self.Integrator + self.error

        if self.Integrator > self.Integrator_max:
            self.Integrator = self.Integrator_max
        elif self.Integrator < self.Integrator_min:
            self.Integrator = self.Integrator_min

        self.I_value = self.Integrator * self.Ki

        PID = self.P_value + self.I_value + self.D_value

        return PID

    def setPoint(self,set_point):
        """
        Initilize the setpoint of PID
        """
        self.set_point = set_point
        self.Integrator=0
        self.Derivator=0

    def setIntegrator(self, Integrator):
        self.Integrator = Integrator

    def setDerivator(self, Derivator):
        self.Derivator = Derivator

    def setKp(self,P):
        self.Kp=P

    def setKi(self,I):
        self.Ki=I

    def setKd(self,D):
        self.Kd=D

    def getPoint(self):
        return self.set_point

    def getError(self):
        return self.error

    def getIntegrator(self):
        return self.Integrator

    def getDerivator(self):
        return self.Derivator


class Joint(object):
    """A single joint on the eye (yaw, pitch, lid), covers sensor and motor."""
    def __init__(self, name):
        self.name      = name
        self.command   = 0
        self.pwm_limit = 255
        self.pos       = 0
        self.pos_raw   = 0
        # Basically the calibration.
        # @TODO - Shortcut to set this from the current value.
        self.pos_center_raw = 0
        self.pos_min   = -100
        self.pos_max   = 100
        self.brake_cmd = 0
        self.active    = False
        self.pid       = PID()

    def set_pos_raw(self, v):
        self.pos_raw = v
        self.pos = v - self.pos_center_raw

    @property
    def target(self):
        return self.pid.getPoint()

    @target.setter
    def target(self, value):
        self.pid.setPoint(value)

    @property
    def error(self):
        return self.pid.getError()

    def toggle_active(self):
        """Turn the PID loop control on and off."""
        if self.active:
            self.active = False
            self.command = 0
        else:
            self.active = True
        return self.active

    def get_pwm(self):
        # Dont try to drive motors while breaking
        if self.brake_cmd:
            return 0
        pwm = abs(self.command)
        if pwm > self.pwm_limit:
            pwm = self.pwm_limit
        return pwm

    def get_direction(self):
        if self.command < 0:
            return 0
        return 1

    def get_brake_cmd(self):
        if self.brake_cmd:
            return 1
        return 0

    def update(self):
        if not self.active:
            return
        cmd = self.pid.update(self.pos)
        if self.pos >= self.pos_max and cmd > 0:
            # Ignore positive commands over the max
            cmd = 0
        elif self.pos <= self.pos_min and cmd < 0:
            cmd = 0
        self.command = cmd


class ArcEye(object):
    """
    Object representing a complete eye, which it connects to over the serial
    link to the arduino. Recieves status and sends commands. Manages a set of
    Joint objects for the yaw, pitch and lid joints.
    """
    def __init__(self, port="/dev/ttyUSB0", config_file=None):
        self.port   = port
        self.status = None
        self.last_cmd = ""
        self.yaw    = Joint("yaw")
        self.pitch  = Joint("pitch")
        self.lid    = Joint("lid")
        self.bat_volt = 0

        self.config = {}
        self.config_file = None
        self.config_st_mtime = 0
        self.config_rate = 200
        if config_file:
           self.load_config(config_file)

        self.frame = 0


    def all_joints(self):
        return (self.yaw, self.pitch, self.lid)

    def connect(self):
        try:
            self.ser = Serial(self.port, 115200)
        except SerialException as e:
            logerr("Failed to connect to arduino serial. Is it plugged in?\n", e)
            return False
        sleep(3) # wait for the board to reset
        loginfo("Connected to %s"%self.port)
        return True

    def read_status(self):
        try:
            # yaw,pitch,lid,battery
            status = self.ser.readline()
            status = status.strip()
            values = status.split(',')
            if not len(values) == 4:
                raise Exception("Got wrong number (%s not 3) of values in status (%s), ignoring."%(len(values),status))
            self.status = status
            self.yaw.set_pos_raw(float(values[0]))
            self.pitch.set_pos_raw(float(values[1]))
            self.lid.set_pos_raw(float(values[2]))
            self.bat_volt = float(values[3])
        except Exception as e:
            logerr(e)

    def send_commands(self):
        cmd = ""
        cmd = "%s,%s,%s,%s,%s,%s,%s,%s,%s\n"%(
            self.yaw.get_pwm(), self.yaw.get_direction(), self.yaw.get_brake_cmd(),
            self.pitch.get_pwm(), self.pitch.get_direction(), self.pitch.get_brake_cmd(),
            self.lid.get_pwm(), self.lid.get_direction(), self.lid.get_brake_cmd(),
                )
        self.ser.write(cmd)
        self.last_cmd = cmd

    def update(self):
        self.frame += 1
        for j in self.all_joints():
            j.update()
        # avoid lots of stat calls
        if self.config_file and self.config_rate > 0 and self.frame % self.config_rate == 0:
            if os.stat(self.config_file).st_mtime > self.config_st_mtime:
                self.reload_config()

    def load_config(self, config_file):
        """Load config from a (yaml) config file."""
        try:
            config = yaml.load(file(config_file))
            self.update_config(config)
            # Only update if config loaded and updated ok
            self.config = config
            self.config_file = config_file
            self.config_st_mtime = os.stat(config_file).st_mtime
        except Exception as e:
            logerr("Failed to load config file:%s - %s"%(config_file,e))
        else:
            loginfo("Loaded config file:%s"%config_file)

    def reload_config(self):
        """Reload the current config file."""
        if not self.config_file: return
        return self.load_config(self.config_file)

    def update_config(self, config):
        """Update with the new config, dict of dicts etc, return from yaml parse"""
        if config is None: return
        if config.has_key('yaw'):
            sub_config = config['yaw']
            if sub_config.has_key('pwm_limit'):
                self.yaw.pwm_limit = sub_config['pwm_limit']
            if sub_config.has_key('pos_center_raw'):
                self.yaw.pos_center_raw = sub_config['pos_center_raw']
            if sub_config.has_key('pos_max'):
                self.yaw.pos_max = sub_config['pos_max']
            if sub_config.has_key('pos_min'):
                self.yaw.pos_min = sub_config['pos_min']
            if sub_config.has_key('p'):
                self.yaw.pid.setKp(sub_config['p'])
            if sub_config.has_key('i'):
                self.yaw.pid.setKi(sub_config['i'])
            if sub_config.has_key('d'):
                self.yaw.pid.setKd(sub_config['d'])
        if config.has_key('pitch'):
            sub_config = config['pitch']
            if sub_config.has_key('pwm_limit'):
                self.pitch.pwm_limit = sub_config['pwm_limit']
            if sub_config.has_key('pos_center_raw'):
                self.pitch.pos_center_raw = sub_config['pos_center_raw']
            if sub_config.has_key('pos_max'):
                self.pitch.pos_max = sub_config['pos_max']
            if sub_config.has_key('pos_min'):
                self.pitch.pos_min = sub_config['pos_min']
            if sub_config.has_key('p'):
                self.pitch.pid.setKp(sub_config['p'])
            if sub_config.has_key('i'):
                self.pitch.pid.setKi(sub_config['i'])
            if sub_config.has_key('d'):
                self.pitch.pid.setKd(sub_config['d'])
        if config.has_key('lid'):
            sub_config = config['lid']
            if sub_config.has_key('pwm_limit'):
                self.lid.pwm_limit = sub_config['pwm_limit']
            if sub_config.has_key('pos_center_raw'):
                self.lid.pos_center_raw = sub_config['pos_center_raw']
            if sub_config.has_key('pos_max'):
                self.lid.pos_max = sub_config['pos_max']
            if sub_config.has_key('pos_min'):
                self.lid.pos_min = sub_config['pos_min']
            if sub_config.has_key('p'):
                self.lid.pid.setKp(sub_config['p'])
            if sub_config.has_key('i'):
                self.lid.pid.setKi(sub_config['i'])
            if sub_config.has_key('d'):
                self.lid.pid.setKd(sub_config['d'])


