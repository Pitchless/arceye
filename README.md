arceye
======

The Eyes!

arceye-demo-3 - the demo you guys built on the river bank.

arceye-demo-4 - looks a bit like demo 3, you can edit the sameway, difference
                is that it will randomly wink and blink so you can just script
                eye motions.

Puppet. r - turns the random wink/blink on and off.

Auto Run
--------

The bin/auto_run file is used on the pi at startup. Edit this to set the demo
to launch.

When run this way it will log out put to /home/pi/arceye.log.
If it starts having problems can look in there. Use:
  cat /home/pi/arceye.log
to see it all or:
  less /home/pi/arceye.log
to be able to see what is in the log.

To test changes to the auto run, just run in like the arceye programs. e.g.
  cd arceye
  ./bin/auto_start

Versions
--------
These are git tags.

* Ansible play to setup the pi.
* Keep alive in command for arduino.

v0.7 - 13th June 2014

* Better threads, proper shutdown fixed.
* Puppet.

v0.6 - 12th June 2014

* Minimal viable installation!
* Single application for both eyes.
    * Threads.
* Demos.
* BUG: Hard to shutdown, need to kill -9

v0.5 - 11th June 2014

* The last one eye version.

v0.4 - 5th June 2014

* DEBUG option to not include LCD code.
* Config file with auto re-load
* Short status message on serial.
* Higher baud rate.
* Help screen (F1).
* Font for gui.

v0.3 - Basic PID control.

v0.2 - Refactor of Eye python commander code.

v0.1 - Initial working hack for joystick control.
