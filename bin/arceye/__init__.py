from __future__ import print_function
import sys, os, datetime
import yaml
from serial import Serial, SerialException
from time import sleep

#
# Logging util
#

def loginfo(*msg):
    print("[%s] INFO: "%datetime.datetime.now(), *msg, file=sys.stderr)

def logerr(*msg):
    print("[%s] ERROR:"%datetime.datetime.now(), *msg, file=sys.stderr)


#
# Util
#
def toggle(value):
    if value:
        return False
    return True


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
        self.deadzone  = 1
        self.reverse   = False
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
        if value > self.pos_max:
            value = self.pos_max
        elif value < self.pos_min:
            value = self.pos_min
            loginfo("Set target: %s"%value)
        self.pid.setPoint(value)

    @property
    def target_rel(self):
        value = self.target
        if value == 0:
            return 0
        if value > 0:
            return (self.pos_min/value)
        return -(abs(self.pos_min)/abs(value))

    @target_rel.setter
    def target_rel(self, value):
        """Set a target as -1..1 range of the joints full motion."""
        if value == 0:
            self.target = 0
        elif value > 0:
            self.target = value * self.pos_max
        else:
            self.target = value * abs(self.pos_min)

    @property
    def error(self):
        return self.pid.getError()

    def toggle_active(self):
        """Turn the PID loop control on and off."""
        if self.active:
            self.activate()
        else:
            self.deactivate()
        return self.active

    def activate(self):
        self.active = True
        self.target = self.pos

    def deactivate(self):
        self.active = False
        self.command = 0
        self.target = 0

    def in_deadzone(self):
        if abs(self.error) < self.deadzone:
            return True
        return False

    def get_pwm(self):
        # Dont try to drive motors while breaking
        if self.brake_cmd:
            return 0
        pwm = abs(self.command)
        if pwm > self.pwm_limit:
            pwm = self.pwm_limit
        return pwm

    def get_direction(self):
        direc = 1
        if self.command < 0:
            direc = 0
        if self.reverse:
            direc = 1 if direc == 0 else 0
        return direc

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
            # Ignore negative commands under the min
            cmd = 0
        #elif self.in_deadzone():
        #    cmd = 0
        self.command = cmd

    def update_config(self, config):
        """Update with the new config, dict of dicts etc, return from yaml parse"""
        if config is None: return
        if config.has_key('pwm_limit'):
            self.pwm_limit = config['pwm_limit']
        if config.has_key('pos_center_raw'):
            self.pos_center_raw = config['pos_center_raw']
        if config.has_key('pos_max'):
            self.pos_max = config['pos_max']
        if config.has_key('pos_min'):
            self.pos_min = config['pos_min']
        if config.has_key('deadzone'):
            self.deadzone = config['deadzone']
        if config.has_key('reverse'):
            self.reverse = config['reverse']
        if config.has_key('p'):
            self.pid.setKp(config['p'])
        if config.has_key('i'):
            self.pid.setKi(config['i'])
        if config.has_key('d'):
            self.pid.setKd(config['d'])


class Target(object):
    def __init__(self, x, y, l):
        self.x = x
        self.y = y
        self.l = l

class ArcEye(object):
    """
    Object representing a complete eye, which it connects to over the serial
    link to the arduino. Recieves status and sends commands. Manages a set of
    Joint objects for the yaw, pitch and lid joints.
    """
    def __init__(self, port="/dev/ttyUSB0", config_file=None):
        self.port   = port
        self.is_connected = False
        self.retry_connect_timeout = 123
        self._retry_connect_count = self.retry_connect_timeout
        self.status = None
        self.command_rate = 1
        self.last_cmd = ""
        self.yaw    = Joint("yaw")
        self.pitch  = Joint("pitch")
        self.lid    = Joint("lid")
        self.bat_volt1 = 0
        self.bat_volt2 = 0

        self.config = {}
        self.config_file = None
        self.config_st_mtime = 0
        self.config_rate = 100
        if config_file:
           self.load_config(config_file)

        self.frame = 0
        self.target = None

    def all_joints(self):
        return (self.yaw, self.pitch, self.lid)

    def connect(self):
        """
        Try to connect to the board. Throws if problems.
        Note that the class auto connects on the first status read, handling
        errors and re-connect logic, so you don't normally need to call this
        direct.
        """
        self.is_connected = False
        self._retry_connect_count = self.retry_connect_timeout
        self.ser = Serial(self.port, 115200)
        self.is_connected = True
        sleep(3) # wait for the board to reset
        loginfo("Connected to %s"%self.port)
        return True

    def read_status(self):
        if not self.is_connected: return
        try:
            status = self.ser.readline()
            # yaw,pitch,lid,battery
            status = status.strip()
            values = status.split(',')
            if not len(values) == 5:
                raise Exception("Got wrong number (%s not 5) of values in status (%s), ignoring."%(len(values),status))
            self.status = status
            self.yaw.set_pos_raw(float(values[0]))
            self.pitch.set_pos_raw(float(values[1]))
            self.lid.set_pos_raw(float(values[2]))
            self.bat_volt1 = float(values[3])
            self.bat_volt2 = float(values[4])
        except SerialException as e:
            self.is_connected = False
            logerr("Serial exception (retry in %s): %s"%(self.retry_connect_timeout,e))
        except Exception as e:
            logerr(e)

    def send_commands(self):
        if not self.is_connected: return
        cmd = ""
        cmd = "%s,%s,%s,%s,%s,%s,%s,%s,%s\n"%(
            self.yaw.get_pwm(), self.yaw.get_direction(), self.yaw.get_brake_cmd(),
            self.pitch.get_pwm(), self.pitch.get_direction(), self.pitch.get_brake_cmd(),
            self.lid.get_pwm(), self.lid.get_direction(), self.lid.get_brake_cmd(),
                )
        try:
            self.ser.write(cmd)
        except SerialException as e:
            self.is_connected = False
            logerr("Serial exception (retry in %s): %s"%(self.retry_connect_timeout,e))
        except Exception as e:
            logerr(e)
        self.last_cmd = cmd

    def update(self):
        self.frame += 1
        try:
            if not self.is_connected:
                self._retry_connect_count -= 1
                if self._retry_connect_count < 0:
                    return self.connect()

            if self.target:
                if self.target.x is not None:
                    loginfo("TARGET! %s"%self.target.x)
                    self.yaw.target_rel = self.target.x
                if self.target.y is not None:
                    self.pitch.target_rel = self.target.y
                if self.target.l is not None:
                    self.lid.target_rel = self.target.l
                self.target = None

            for j in self.all_joints():
                j.update()

            if self.command_rate == 1 or self.frame % self.command_rate == 0:
                self.send_commands()

            # avoid lots of stat calls
            if self.config_file and self.config_rate > 0 and self.frame % self.config_rate == 0:
                if os.stat(self.config_file).st_mtime > self.config_st_mtime:
                    self.reload_config()
        except SerialException as e:
            logerr("Serial exception (retry in %s): %s"%(self.retry_connect_timeout,e))
        except Exception as e:
            logerr(e)

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
        if config is None:
            return
        if config.has_key('port'):
            self.port = config['port']
        if config.has_key('command_rate'):
            self.command_rate = config['command_rate']
        # Joints
        if config.has_key('yaw'):
            self.yaw.update_config(config['yaw'])
        if config.has_key('pitch'):
            self.pitch.update_config(config['pitch'])
        if config.has_key('lid'):
            self.lid.update_config(config['lid'])

    def activate(self):
        for j in self.all_joints():
            j.activate()

    def deactivate(self):
        for j in self.all_joints():
            j.deactivate()

    def stop(self):
        for j in self.all_joints():
            j.command = 0
            j.active = False
            j.target = None

    def go_to(self, x=None, y=None, l=None):
        loginfo("Goto %s,%s,%s"%(x,y,l))
        self.target = Target(x,y,l)

class Robot(object):
    """The complete robot, with both eyes."""
    def __init__(self, config1=None, config2=None):
        self.config1   = config1
        self.config2   = config2
        self.eye1      = None
        self.eye2      = None
        if self.config1:
            self.eye1 = ArcEye(config_file=self.config1)
        if self.config2:
            self.eye2 = ArcEye(config_file=self.config2)
            if self.eye1.port == self.eye2.port:
                logerr("Eye2 on same port as eye1")
                self.eye2 = None

    def read_status(self):
        if self.eye1:
            self.eye1.read_status()
        if self.eye2:
            self.eye2.read_status()

    def update(self):
        if self.eye1:
            self.eye1.update()
        if self.eye2:
            self.eye2.update()

    def stop(self):
        if self.eye1: self.eye1.stop()
        if self.eye2: self.eye2.stop()

    def zero_target(self):
        for j in self.eye1.all_joints(): j.target = 0
        for j in self.eye2.all_joints(): j.target = 0

