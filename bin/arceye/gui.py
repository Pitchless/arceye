from __future__ import print_function
import sys, os, datetime
import yaml
from time import sleep
from threading import Thread
from arceye import *
import pygame

# This is a simple pygame class that will help us print to the screen
class GuiText(object):
    def __init__(self, screen, text_color=(0,255,0), font=None):
        self.reset()
        self.screen     = screen
        self._font      = pygame.font.Font(None, 20) if not font else font
        self.text_color = text_color

    def text(self, textString):
        textBitmap = self._font.render(textString, True, self.text_color)
        self.screen.blit(textBitmap, [self.x, self.y])
        self.y += self.line_height

    def reset(self):
        self.x = 10
        self.y = 10
        self.line_height = 15

    def indent(self):
        self.x += 10

    def unindent(self):
        self.x -= 10

    def color(self,r,g,b):
        self.text_color = (r,g,b)

    def font(self,name,size=12):
        self._font = pygame.font.Font(pygame.font.match_font(name), size)

    def boolean(self, name, value, col_true=(0,255,0), col_false=(255,0,0)):
        old_col = self.text_color
        if col_true:
            self.text_color = col_true
        if not value:
            self.text_color = col_false
        self.text("%s: %s"%(name, value))
        self.text_color = old_col


class GuiBase(object):
    def __init__(self, name = "ArcEye", w=640, h=640, config1=None, config2=None, argv=sys.argv):
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
        self.screen = pygame.display.set_mode( (self.w,self.h) )
        self.screen.fill((0, 0, 0))
        self.guitxt = GuiText(self.screen)
        #loginfo("Fonts: %s"%pygame.font.get_fonts())
        self.guitxt.font("droidsansmono", 14)

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
            self.frame += 1
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
            self.guitxt.color(0,255,0)
            if self.show_help:
                self._display_help()
            else:
                self.display_header()
                self.display()
            pygame.display.flip()

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
        self.guitxt.text("ArcEye (%s) Frame:%s"%(sys.argv[0], self.frame))
        self.guitxt.text("")

    def display_eye(self, eye):
        self.guitxt.color(255,255,0)
        self.guitxt.text("EYE %s %s"%(eye.port,eye.config_file))
        self.guitxt.boolean("Connected", eye.is_connected)
        if eye.bat_volt1 < 18: # over
            self.guitxt.color(255,0,0)
        if eye.bat_volt1 < 14: # normal
            self.guitxt.color(0,255,0)
        if eye.bat_volt1 < 11: # under
            self.guitxt.color(255,123,0)
        self.guitxt.text("Battery Volt 1: %s"%eye.bat_volt1)
        if eye.bat_volt2 < 18: # over
            self.guitxt.color(255,0,0)
        if eye.bat_volt2 < 14: # normal
            self.guitxt.color(0,255,0)
        if eye.bat_volt2 < 11: # under
            self.guitxt.color(255,123,0)
        self.guitxt.text("Battery Volt 2: %s"%eye.bat_volt2)
        self.guitxt.indent()
        for j in eye.all_joints():
            self.guitxt.color(255,255,0)
            self.guitxt.text(j.name.upper())
            self.guitxt.color(0,255,0)
            self.guitxt.indent()
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
            self.guitxt.text("Deadzone: %s"%j.deadzone)
            self.guitxt.text("P:%s I:%s D:%s"%(j.pid.Kp, j.pid.Ki, j.pid.Kd))
            self.guitxt.unindent()
            self.guitxt.unindent()
        self.guitxt.color(0,180,0)
        self.guitxt.text("")
        self.guitxt.text("Status %s"%eye.status)
        self.guitxt.text("Command %s"%eye.last_cmd)

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
