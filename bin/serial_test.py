#!/usr/bin/env python

from serial import Serial
from time import sleep

ser = Serial('/dev/ttyUSB0', 9600)
sleep(3) # wait for the board to reset

print "start"
print "write"
ser.write("hello\n")
print "read"
line = ser.readline()
print "GOT %s"%line

print "write world..."
ser.write("world\n")
print "read"
line = ser.readline()
print "GOT %s"%line
line = ser.readline()
print "GOT %s"%line

cmd = ""
while not cmd == "q":
    cmd = raw_input(">> ")
    ser.write(cmd+"\n")
    out = ser.readline()
    out = ser.readline()
    print out 

