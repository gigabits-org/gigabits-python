Gigabits gets revenue from software, not hardware.  To maximize revenue, Gigabits software should run on as many popular processors as possible.  Gigabits uses two classes of software - server software and sensor/actuator control software.  The server software is written to run on virtually any generic processor, so we don't have to do anything to make it portable.  The control processors are the "Things" in "Internet of Things".  IoT installations typically have many control processors, so they must be cheap and reliable.  Arduino and Raspberry Pi are popular families of control processors.

This is a repository of Python control software.  It was written to support Raspberry Pi processors.  It belongs to the gigabits-org organization on GitHub.  The code reads raw sensor values and writes raw actuator values.  For example, a sensor may tell the server that a room is too hot.  In response, the server may tell an actuator to turn on a fan.

Commands from the server may arrive at any time.  They should be executed when they arrive.  Status, like temperature or humidity, should periodically be sent to the server.

The code uses MQTT to subscribe to commands and publish status.  MQTT is platform-independent.  This lets us compose MQTT messages in Python on a control processor and read them in Go on a server.

The Python routines that control the sensor and actuator devices are copied from examples found on the NCD website when possible.  If there is no Python code for a sensor or actuator, we'll use the device's datasheet and relevant example code as inspiration.

A routine named dummydevice.py shows how MQTT is implemented in Python.  We only need to substitute code that reads/writes real data for the synthetic data used in dummydevice.py.

The Arduino equivalent of this repository is gigabits-arduino.  We will use it as a reference.  The example code in gigabits-arduino/examples/ESP32DemoApp is especially useful.
