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
    def __init__(self, name = "ArcEye", config_file=None):
        self.config_file = config_file
        self.name        = name
        self.frame       = 0
        self.done        = False
        self.show_help   = False
        self.eye         = ArcEye()
        self.screen      = None

    def init(self):
        # Start the gui
        loginfo("GUI Init - %s"%self.name)
        pygame.init()
        pygame.display.set_caption(self.name)
        self.screen = pygame.display.set_mode( (320,620) )
        self.screen.fill((0, 0, 0))
        self.guitxt = GuiText(self.screen)
        #loginfo("Fonts: %s"%pygame.font.get_fonts())
        self.guitxt.font("droidsansmono", 14)
        self.eye.load_config(self.config_file)

    def run(self):
        while not self.done:
            self.frame += 1
            # Read eye status
            self.eye.read_status()
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
            else:
                self.handle_keys_pressed(keys)
            # Update the eye and it's joints (runs their pids)
            self.eye.update()
            # Update the display
            self.display()
            pygame.display.flip()

    def handle_event(self, event):
        pass

    def handle_keys_pressed(self, keys):
        pass

    def display(self):
        pass

