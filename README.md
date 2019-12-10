This is a repository that holds a Python version of the code that runs on devices like MKR1000, ESP32 or 
Raspberry Pi.  It is owned by the gigabits-org organization.  The code reads raw sensor values and writes raw actuator values.  For example, a sensor may tell the server that a room is too hot.  In response, the server may tell an actuator to turn on a fan.

Commands from the server may arrive at any time.  They should be executed when they arrive.  Status, like temperature or humidity, should periodically be sent to the server.

The code uses MQTT to subscribe to commands and publish status.  MQTT is platform-independent.  This lets us compose MQTT messsages in Python on a device and read them in Go on a server.
