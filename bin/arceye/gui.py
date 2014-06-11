from __future__ import print_function
import sys, os, datetime
import yaml
from time import sleep
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


class GuiBase(object):
    def __init__(self, name = "ArcEye", w=320, h=620, config1=None, config2=None):
        self.config1   = config1
        self.config2   = config1
        self.name      = name
        self.frame     = 0
        self.w         = w
        self.h         = h
        self.done      = False
        self.show_help = False
        self.eye1      = ArcEye(config_file=self.config1)
        self.eye2      = ArcEye(config_file="arse")
        self.screen    = None

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

    def run(self):
        while not self.done:
            self.frame += 1
            # Read eye status
            self.eye1.read_status()
            self.eye2.read_status()
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
            # Update the eye and it's joints (runs their pids)
            self.eye1.update()
            self.eye2.update()
            # Update the display
            self.screen.fill((0,0,0))
            self.guitxt.reset()
            self.guitxt.color(255,255,0)
            if self.show_help:
                self._display_help()
            else:
                self.display_header()
                self.display()
            pygame.display.flip()

    def _display_help(self):
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
        self.guitxt.text("Frame: %s"%self.eye1.frame)

    def display_eye(self, eye):
        self.guitxt.text("Eye")
        self.guitxt.text("Connected: %s"%eye.is_connected)
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
            self.guitxt.text(j.name)
            self.guitxt.color(0,255,0)
            self.guitxt.indent()
            if j.pos > j.pos_max or j.pos < j.pos_min:
                self.guitxt.color(255,0,0)
            self.guitxt.text("Pos raw: " + str(j.pos_raw))
            self.guitxt.text("Position: %s (%s..%s)"%(j.pos, j.pos_min, j.pos_max))
            self.guitxt.color(0,255,0)
            self.guitxt.text("Command: %s"%j.command)
            self.guitxt.text("PWM: %s Dir:%s Reverse:%s"%(
                j.get_pwm(),j.get_direction(), j.reverse))
            self.guitxt.text("Brake: %s"%j.brake_cmd)
            self.guitxt.color(0,255,0) if j.active else self.guitxt.color(0,100,0)
            self.guitxt.text("Active: %s"%j.active)
            self.guitxt.indent()
            self.guitxt.text("Target: %s"%j.target)
            self.guitxt.text("Error: %s"%j.error)
            self.guitxt.text("Deadzone: %s"%j.deadzone)
            self.guitxt.text("P:%s I:%s D:%s"%(j.pid.Kp, j.pid.Ki, j.pid.Kd))
            self.guitxt.unindent()
            self.guitxt.unindent()
        self.guitxt.color(0,255,0)
        self.guitxt.text("Status %s"%eye.status)
        self.guitxt.text("Command %s"%eye.last_cmd)
