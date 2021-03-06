jopi-mpd
========

Control MPD on raspberry pi, on top of Adafruit's LCD plate lib

This simple and short program allows to display information from MPD, do some basic actions (prev / next / select playlist...) for Adafruit's LCD plate hardware and Raspberry Pi.

See also: http://learn.adafruit.com/adafruit-16x2-character-lcd-plus-keypad-for-raspberry-pi/overview


INSTALLATION STEPS:
* Follow steps described on https://learn.adafruit.com/adafruit-16x2-character-lcd-plus-keypad-for-raspberry-pi/usage
* Create a "playlists" folder in /var/lib/mpd/music/WEBRADIO , 
  where you would put any playlist or radio "pls" files you want ; 
  or alternatively, if you want to use another folder, 
  just change the variable named "playlistRelPath" in jopi-mpd.py
* You can try now by running _sudo ./jopi-mpd.py_
* If you want to start jopi-mpd automatically at startup:
  * Declare it as a service, by copying <jopi-mpd path>/init.d/jopi-mpd to /etc/init.d
    * You may have to manually edit this file: 
      change variable "DAEMON" to match the path of your jopi-mpd installation 
      (currently it's "DAEMON=/home/pi/jopi-mpd/$NAME.py")
  * And then make it autostarts: sudo update-rc.d jopi-mpd defaults
* To stop jopi-mpd cleanly just do a 
  _touch /var/lock/stop-jopi-mpd_
