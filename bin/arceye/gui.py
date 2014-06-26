from __future__ import print_function
import sys, os, datetime
import yaml
from time import sleep
from datetime import datetime
from threading import Thread
from random import random, randint
from arceye import *
import pygame

# This is a simple pygame class that will help us print to the screen
class GuiText(object):
    def __init__(self, screen, text_color=(0,255,0), font=None):
        self.reset()
        self.screen     = screen
        self._font      = pygame.font.Font(None, 20) if not font else font
        self.text_color = text_color
    
    def br(self):
        self.y += self.line_height
        return self

    def text(self, textString, nl=True):
        textBitmap = self._font.render(textString, True, self.text_color)
        self.screen.blit(textBitmap, [self.x, self.y])
        if nl:
            self.y += self.line_height
        else:
            self.x += textBitmap.get_width()
        return self

    def reset(self):
        self.x = 10
        self.y = 10
        self.line_height = 15
        return self

    def indent(self):
        self.x += 10
        return self

    def unindent(self):
        self.x -= 10
        return self

    def color(self,r,g,b):
        self.text_color = (r,g,b)
        return self

    def font(self,name,size=12):
        self._font = pygame.font.Font(pygame.font.match_font(name), size)
        return self
    
    def integer(self, name, value):
        self.text("%s: %s"%(name,int(value)))
        return self

    def boolean(self, name, value, col_true=(0,255,0), col_false=(255,0,0)):
        old_col = self.text_color
        if col_true:
            self.text_color = col_true
        if not value:
            self.text_color = col_false
        self.text("%s: %s"%(name, value))
        self.text_color = old_col
        return self


class GuiBase(object):
    def __init__(self, name = "ArcEye", w=640, h=640, config1=None, config2=None, argv=sys.argv):
        self.progname   = os.path.basename(sys.argv[0])
        self.start_time = datetime.datetime.now()
        self.now        = self.start_time
        if len(argv) > 1:
            config1 = argv[1]
        if len(argv) > 2:
            config2 = argv[2]
        self.config1   = config1
        self.config2   = config2
        self.eyes      = Robot(config1=config1, config2=config2)
        self.eye1      = self.eyes.eye1
        self.eye2      = self.eyes.eye2
        self.name      = name
        self.frame     = 0
        self.w         = w
        self.h         = h
        self.done      = False
        self.show_help = False
        self.screen    = None
        self.thread    = None

    def init(self):
        # Start the gui
        loginfo("GUI Init - %s"%self.name)
        pygame.init()
        pygame.display.set_caption(self.name)
        pygame.key.set_repeat(20,20)
        self.screen = pygame.display.set_mode( (self.w,self.h) )
        self.screen.fill((0, 0, 0))
        self.guitxt = GuiText(self.screen)
        #loginfo("Fonts: %s"%pygame.font.get_fonts())
        self.guitxt.font("droidsansmono", 14)
        self.now = datetime.datetime.now()

    def run(self, thread=False):
        if not thread:
            return self._run()

    def start(self):
        """Run on a thread, returns and GUI runs async. Thread in self.thread."""
        if self.eyes.eye1:
            self.eyes.eye1.run()
        if self.eyes.eye2:
            self.eyes.eye2.run()
        self.thread = Thread(target=self.run)
        return self.thread.start()

    def run(self):
        """Run the GUI, blocks until self.done is True."""
        while not self.done:
            self.frame  += 1
            self.now     = datetime.datetime.now()
            self.up_time = self.now - self.start_time
            # Check for gui events
            for event in pygame.event.get(): # User did something
                if event.type == pygame.QUIT: # If user clicked close
                    self.done=True # Flag that we are done so we exit this loop
                else:
                    self.handle_event(event)
            # Keyboard shortcuts
            keys = pygame.key.get_pressed()
            if keys[pygame.K_ESCAPE]:
                self.done = True
            elif keys[pygame.K_F1]:
                self.show_help = toggle(self.show_help)
            else:
                self.handle_keys_pressed(keys)
            # Update the display
            self.screen.fill((0,0,0))
            self.guitxt.reset()
            self.guitxt.font("droidsansmono", 14)
            self.guitxt.color(0,255,0)
            if self.show_help:
                self._display_help()
            else:
                self.display_header()
                self.display()
            pygame.display.flip()
        self.quit()

    def quit(self):
        self.done = True
        pygame.display.quit()

    def display(self):
        pass

    def _display_help(self):
        self.guitxt.color(255,255,0)
        self.guitxt.text("**** Arcself.eye ***")
        self.guitxt.text("")
        self.guitxt.text("ESC - Quit")
        self.guitxt.text("F1  - Show/hide this help")
        self.guitxt.text("")
        self.display_help()

    def handle_event(self, event):
        pass

    def handle_keys_pressed(self, keys):
        pass

    def display(self):
        pass

    def display_header(self):
        hours, remainder = divmod(self.up_time.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.guitxt.color(200,200,0).text("%s - %s - Frame:%s Now:%s Start:%s Up:%s:%s.%s"%(
            self.name, self.progname, self.frame,
            self.now.strftime("%H:%m.%S"), self.start_time.strftime("%H:%m.%S"),
            hours, minutes, seconds
            ))
        self.guitxt.text("")

    def display_eye(self, eye):
        self.guitxt.font("droidsansmono", 13)
        self.guitxt.color(255,255,0)
        self.guitxt.text("EYE %s %s"%(eye.port,eye.config_file))
        self.guitxt.color(0,255,0)
        self.guitxt.boolean("Connected", eye.is_connected)
        self.guitxt.integer("Frame", eye.frame)
        old_x = self.guitxt.x
        self.guitxt.color(0,255,0)
        self.guitxt.text("Battery: ", nl=False)
        if eye.bat_volt1 < 18: # over
            self.guitxt.color(255,0,0)
        if eye.bat_volt1 < 14: # normal
            self.guitxt.color(0,255,0)
        if eye.bat_volt1 < 11: # under
            self.guitxt.color(255,123,0)
        self.guitxt.text("Volt1:%s "%eye.bat_volt1, nl=False)
        if eye.bat_volt2 < 18: # over
            self.guitxt.color(255,0,0)
        if eye.bat_volt2 < 14: # normal
            self.guitxt.color(0,255,0)
        if eye.bat_volt2 < 11: # under
            self.guitxt.color(255,123,0)
        self.guitxt.text("Volt2:%s"%eye.bat_volt2)
        self.guitxt.x = old_x
        for j in eye.all_joints():
            self.guitxt.color(255,255,0)
            self.guitxt.text(j.name.upper())
            self.guitxt.indent()
            self.guitxt.color(0,255,0)
            if j.pos > j.pos_max or j.pos < j.pos_min:
                self.guitxt.color(255,0,0)
            self.guitxt.text("Pos raw: " + str(j.pos_raw))
            self.guitxt.text("Position: %s (%s..%s)"%(j.pos, j.pos_min, j.pos_max))
            self.guitxt.color(0,255,0)
            self.guitxt.text("Command: %s"%j.command)
            self.guitxt.text("PWM: %s Dir:%s (Rev:%s)"%(
                j.get_pwm(),j.get_direction(), j.reverse))
            self.guitxt.boolean("Brake", j.brake_cmd,
                    col_true=(0,255,0), col_false=(0,100,0))
            self.guitxt.color(0,255,0) if j.active else self.guitxt.color(0,100,0)
            self.guitxt.text("Active: %s"%j.active)
            self.guitxt.indent()
            self.guitxt.text("Target: %s"%j.target)
            self.guitxt.text("Error: %s"%j.error)
            #self.guitxt.text("Deadzone: %s"%j.deadzone)
            self.guitxt.text("P:%s I:%s D:%s"%(j.pid.Kp, j.pid.Ki, j.pid.Kd))
            self.guitxt.unindent()
            self.guitxt.unindent()
            self.guitxt.color(0,180,0)
        self.guitxt.font("droidsansmono", 10).br().text("Stat:%s Cmd:%s"%(eye.status, eye.last_cmd))


class GuiDemo(GuiBase):
    def init(self):
        super(GuiDemo, self).init()
        self.name = "ArcEye Demo"

    def handle_keys_pressed(self, keys):
        # Stop!
        if keys[pygame.K_SPACE]:
            self.eyes.deactivate()
        elif keys[pygame.K_0]:
            self.eyes.zero_target()

        # Controllers on/off
        elif keys[pygame.K_1]:
            self.eye1.yaw.toggle_active()
        elif keys[pygame.K_2]:
            self.eye1.pitch.toggle_active()
        elif keys[pygame.K_3]:
            self.eye1.lid.toggle_active()
        elif keys[pygame.K_4]:
            self.eye2.yaw.toggle_active()
        elif keys[pygame.K_5]:
            self.eye2.pitch.toggle_active()
        elif keys[pygame.K_6]:
            self.eye2.lid.toggle_active()

    def display_help(self):
        self.guitxt.text("TODO")

    def display(self):
        # Update the display
        if self.eye1:
            self.display_eye(self.eye1)
        if self.eye2:
            self.guitxt.y = 40
            self.guitxt.x = 300
            self.display_eye(self.eye2)
            self.guitxt.x = 10


class ArcEyePuppet(GuiDemo):
    def __init__(self, *args, **kw):
        super(ArcEyePuppet, self).__init__(*args, **kw)
        self._wink1_thread = None
        self._wink2_thread = None
        self._blink_thread = None
        self._random_thread = None
        self._is_random = False
        self.target = Target(0,0,None)
        self.min_blink_time = 2
        self.max_blink_time = 30
        # Percentage of blinks that are winks
        self.wink_percent = 0.1

    def handle_event(self, event):
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_w:
                self.wink1()
            elif event.key == pygame.K_e:
                self.wink2()
            elif event.key == pygame.K_b:
                self.blink()
            elif event.key == pygame.K_0:
                self.target = Target(0,0,0)
            elif event.key == pygame.K_r:
                if self._is_random:
                    self.stop_random()
                else:
                    self.start_random()
        if event.type == pygame.KEYDOWN:
            new_target = False
            if event.key == pygame.K_UP:
                self.target.y = clamp(self.target.y + 0.01)
                new_target = True
            if event.key == pygame.K_DOWN:
                self.target.y = clamp(self.target.y - 0.01)
                new_target = True
            if event.key == pygame.K_RIGHT:
                self.target.x = clamp(self.target.x + 0.01)
                new_target = True
            if event.key == pygame.K_LEFT:
                self.target.x = clamp(self.target.x - 0.01)
                new_target = True

            if new_target:
                self.eyes.go_to(self.target.x, self.target.y)

    def start_random(self):
        loginfo("Start random")
        if self._random_thread is not None and self._random_thread.is_alive():
            return True
        self._is_random = True
        self._random_thread = Thread(target=self._random)
        return self._random_thread.start()

    def stop_random(self):
        loginfo("Stop random")
        self._is_random = False

    def _random(self):
        while self._is_random and not self.done:
            if random() <= self.wink_percent:
                if randint(1,2) == 1:
                    self.wink1(wait=True)
                else:
                    self.wink2(wait=True)
            else:
                self.blink(wait=True)
            blink_time = randint(self.min_blink_time, self.max_blink_time)
            loginfo("Next blink in %s"%blink_time)
            for i in range(0,blink_time):
                if not self._is_random or self.done: return
                sleep(1)

    def wink1(self, wait=False):
        if self._wink1_thread is not None and self._wink1_thread.is_alive():
            return False
        self._wink1_thread = Thread(target=self._wink1)
        self._wink1_thread.start()
        if wait:
            self._wink1_thread.join()

    def wink2(self, wait=False):
        if self._wink2_thread is not None and self._wink2_thread.is_alive():
            return False
        self._wink2_thread = Thread(target=self._wink2)
        self._wink2_thread.start()
        if wait:
            self._wink2_thread.join()

    def _wink1(self):
        if not self.eyes.eye1: return
        loginfo("Wink1")
        self._wink(self.eyes.eye1)
        loginfo("Wink1 Done")

    def _wink2(self):
        if not self.eyes.eye2: return
        loginfo("Wink2")
        self._wink(self.eyes.eye2)
        loginfo("Wink2 Done")

    def _wink(self, eye):
        eye.go_to(l=0.7)
        sleep(2)
        eye.go_to(l=0.9)
        #sleep(3)
        sleep(3 + randint(0,2))
        eye.go_to(l=0.4)
        sleep(2)
        eye.go_to(l=0.2)
        sleep(1)
        eye.go_to(l=0.0)
        sleep(2)

    def blink(self, wait=False):
        if self._blink_thread is not None and self._blink_thread.is_alive():
            return False
        self._blink_thread = Thread(target=self._blink)
        self._blink_thread.start()
        if wait:
            self._blink_thread.join()

    def _blink(self):
        loginfo("Blink")
        t1 = Thread(target=self._wink1)
        t2 = Thread(target=self._wink2)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        loginfo("Blink Done")

