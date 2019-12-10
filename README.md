This is a repository that holds a Python version of the code that runs on devices like MKR1000, ESP32 or 
Raspberry Pi.  It is owned by the gigabits-org organization.  The code reads raw sensor values and writes raw actuator values.  For example, a sensor may tell the server that a room is too hot.  In response, the server may tell an actuator to turn on a fan.

Gigabits gets revenue from from software, not hardware.  To maximize revenue, Gigabits software should run on as many processors as possible.  The routines in this repository are functionally equivalent to routines written in Arduino C++ in the gigabits-arduino repository.  As more processors are certified for use in Gigabits, more 

Commands from the server may arrive at any time.  They should be executed when they arrive.  Status, like temperature or humidity, should periodically be sent to the server.

The code uses MQTT to subscribe to commands and publish status.  MQTT is platform-independent.  This lets us compose MQTT messsages in Python on a device and read them in Go on a server.

The Python routines that control the sensor and actuator devices is copied from examples found on the NCD website when possible.  If there is no Python code for a sensor or actuator
