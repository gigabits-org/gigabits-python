#!/usr/bin/env python3.7

# This file contains a Python implementation of the Arduino sketch 
# ESP32App.ino.  That sketch exercises a bunch of sensors and communicates with 
# the main server.

import paho.mqtt.client as mqtt
import random
import json
import time
import os
from decimal import *
import smbus
from dotenv import load_dotenv
load_dotenv()

# Here are some values that we don't want to bake into the source code.  
# They're held in environment variables instead.
# Note that these do NOT include the router's ssid and password.  The standard 
# method for booting a Raspberryt Pi connects to the router.  That's happens long 
# before we get here.

# MQTT is used to move data between a server and devices.
# Devices publish messages and an mqtt broker sends those messsages to entities 
# MQTT_PASSWORD provide basic authentation for the broker.
MQTT_BROKER=os.getenv('MQTT_BROKER')
MQTT_PORT=int(os.getenv('MQTT_PORT'))
MQTT_USERNAME=os.getenv('MQTT_USERNAME')
MQTT_PASSWORD=os.getenv('MQTT_PASSWORD')
MQTT_DEVKEY=os.getenv('MQTT_DEVKEY')

# Here are the routines used to setup and periodically read sensor data.
# The routines that carry out commands from the server are here too.
# Start by listing the sensors we'll use, their I2C addresses and their 
# sensorIndices.

# I2C addresses
HCPA_Addr = 0x28
PROXY_Addr = 0x39
#OLED_Addr = 0x3C
PCA_Addr = 0x40
ADC_Addr = 0x50
SOIL_Addr = 0x51
GAS_Addr = 0x52
MPL_Addr = 0x60
TSL_Addr = 0x49

# Gigabits sensor indices
HUMIDITY_SENSOR_IDX = "1"
TEMPERATURE_SENSOR_IDX = "2"
#OLED_INVERT_COMMAND_IDX = "3"
PRESSURE_SENSOR_IDX = "4"
GAS_SENSOR_IDX = "5"
SOIL_SENSOR_IDX = "6"
PROXY_SENSOR_IDX = "7"
VISIBLE_LIGHT_SENSOR_IDX = "8"
INFRARED_LIGHT_SENSOR_IDX = "9"


# On each cycle of gathering data, we put the current sensor value indexed by 
# the current sensorIndex into this dictionary.  At the end of a cycle of data 
# gathering, we convert the dictionary into a JSON object and return it to the 
# server.
sensorVals = {}

# This is the temperature and humidity sensor that's in the training board.
# Reference https://github.com/ControlEverythingCommunity/HCPA-5V-U3/blob/master/Python/HCPA_5V_U3.py

# The setup routine does nothing
#def setupHCPA():

# This routine gets the sensor data, converts it to sensible values and  
# stuffs it into sensorVals.  After all the sensors have been processed, 
# sensorVals is returned in one wad.
def sendHCPAData(sensorVals):
    print("Sending HCPA")

    #  Send the request or some data.  This initiates a measurent cycle.
    bus.write_byte(HCPA_Addr, 0x80)
    
    # Wait for the measurement cycle to complete
    time.sleep(0.5)
    
    # Get the next 4 bytes from the sensor
    # humidity msb, humidity lsb, cTemp msb, cTemp lsb
    data = bus.read_i2c_block_data(HCPA_Addr, 4)
    
    # Process the incoming data.  The MS two bits of humidity data are really 
    # status bits.  The example code ignores them so we do too.
    humidity = (((data[0] & 0x3F) * 256) + data[1]) / 16384.0 * 100.0
    cTemp = (((data[2] * 256) + (data[3] & 0xFC)) / 4) / 16384.0 * 165.0 - 40.0
    fTemp = (cTemp * 1.8) + 32
    
    print("humidity: {}".format(humidity))
    print("Temperature (deg C): {}".format(cTemp))
    print("Temperature (deg F): {}".format(fTemp))
    # store the humidity and temperature into sensorVals dict
    sensorVals[HUMIDITY_SENSOR_IDX] = round(humidity, 5)
    sensorVals[TEMPERATURE_SENSOR_IDX] = round(fTemp, 5)

# Setup the pressure sensor.
# Note that the compensation variables A0, B1, B2 and C12 are effectively
# global inside this file
A0 = 0.0
B1 = 0.0
B2 = 0.0
C12 = 0.0

# Calculate the compensation coefficients in the setup routine.
def setupMPL():
    
    global A0
    global B1
    global B2
    global C12
    
    # MPL115A2 address, 0x60(96)
    # Reading Coefficents for compensation
    # Read data back from 0x04(04), 8 bytes
    # A0 MSB, A0 LSB, B1 MSB, B1 LSB, B2 MSB, B2 LSB, C12 MSB, C12 LSB
    data = bus.read_i2c_block_data(MPL_Addr, 0x04, 8)
    
    # Convert the data to floating points
    A0 = (data[0] * 256 + data[1]) / 8.0
    B1 = (data[2] * 256 + data[3])
    if B1 > 32767 :
        B1 -= 65536
    B1 = B1 / 8192.0
    B2 = (data[4] * 256 + data[5])
    if B2 > 32767 :
        B2 -= 65536
    B2 = B2 / 16384.0
    C12 = ((data[6] * 256 + data[7]) / 4) / 4194304.0
    
    print("in setupMPL:  A0: %f, B1: %f, B2: %f, C12: %f" %(A0, B1, B2, C12))

def sendMPLData(sensorVals):
    print("Sending pressure data ...")
  
    print("in sendMPLData, A0: %f, B1: %f, B2: %f, C12: %f" %(A0, B1, B2, C12))
   
    # MPL115A2 address, 0x60(96)
    # Send Pressure measurement command, 0x12(18)
    #       0x00(00)    Start conversion
    bus.write_byte_data(0x60, 0x12, 0x00)
    
    time.sleep(0.5)
    
    # MPL115A2 address, 0x60(96)
    # Read data back from 0x00(00), 4 bytes
    # pres MSB, pres LSB, temp MSB, temp LSB
    data = bus.read_i2c_block_data(0x60, 0x00, 4)
    
    # Convert the data to 10-bits  Note that we calculate the temperature,
    # then discard it after using it for compensation
    print("data[0]: %d, data[1]: %d, data[2]: %d, data[3]: %d" %(data[0], 
        data[1], data[2], data[3]))
    pres = ((data[0] * 256) + (data[1] & 0xC0)) / 64
    temp = ((data[2] * 256) + (data[3] & 0xC0)) / 64
    
    print("pres: %d, temp: %d" %(pres, temp))
    
    print("A0: %d, B1: %d, C12: %d, temp: %d, pres: %f, B2: %f, temp: %f" %(A0, 
    B1, C12, temp, pres, B2, temp))
    
    # Calculate pressure compensation
    presComp = A0 + (B1 + C12 * temp) * pres + B2 * temp
    
    print("presComp: %f" %(presComp))
    
    # Convert the data
    pressure = (65.0 / 1023.0) * presComp + 50
    
    print("Pressure: {}".format(pressure))
    # store the pressure into sensorVals dict
    sensorVals[PRESSURE_SENSOR_IDX] = round(pressure, 5);

# There's nothing for the setup routine to set up, so proceed to sending a 
# sample back to the server.
# This is from https://github.com/ControlEverythingCommunity/ADC121C021/blob/master/Arduino/ADC121C021.ino
def setupGas(sensorVals):

    # Select configuration register, 0x02(02)
    #       0x20(32)    Automatic conversion mode enabled
    bus.write_byte_data(GAS_Addr, 0x02, 0x20)
    
    time.sleep(0.5)
    
def sendGasData(sensorVals):
    print("Sending Gas")
    
    # Read data back from 0x00(00), 2 bytes
    # raw_adc MSB, raw_adc LSB
    data = bus.read_i2c_block_data(GAS_Addr, 0x00, 2)
    
    # Convert the data to 12-bits
    raw_adc = (data[0] & 0x0F) * 256 + data[1]
    
    # store the gas measurement into sensorVals dict
    print("Gas: {}".format(raw_adc))
    sensorVals[GAS_SENSOR_IDX] = round(raw_adc, 5)
    
def setupSoilData(sensorVals):

    # Select configuration register, 0x02(02)
    #       0x20(32)    Automatic conversion mode enabled
    bus.write_byte_data(SOIL_Addr, 0x02, 0x20)
    
    time.sleep(0.5)
    
def sendSoilData(sensorVals):
    print("Sending Soil")
    
    # Read data back from 0x00(00), 2 bytes
    # raw_adc MSB, raw_adc LSB
    data = bus.read_i2c_block_data(SOIL_Addr, 0x00, 2)
    
    # Convert the data to 12-bits
    raw_adc = (data[0] & 0x0F) * 256 + data[1]
    
    # store the soil measurement into sensorVals dict
    print("Soil: {}".format(raw_adc))
    sensorVals[SOIL_SENSOR_IDX] = round(raw_adc, 5)


# Set up the proximity detector.
def setupProximity(sensorVals):
    print("Sending Proximity")
    
    # Select the ENABLE register, 0x00(0), with command register 0x80(128)
    #       0x0D(14)    Power on, Wait enabled, Proximity enabled
    bus.write_byte_data(PROXY_Addr, 0x00 | 0x80, 0x0D)
    
    #  Select proximity time control register, 0x02(2), with command register 0x80(128)
    #       0xFF(255)   Time = 2.73 ms
    bus.write_byte_data(PROXY_Addr, 0x02 | 0x80, 0xFF)
    
    # Select wait time register 0x03(03), with command register, 0x80(128)
    #       0xFF(255)   Time - 2.73ms
    bus.write_byte_data(PROXY_Addr, 0x03 | 0x80, 0xFF)
    
    # Select pulse count register, 0x0E(14), with command register 0x80(128)
    #       0x20(32)    Pulse count = 32
    bus.write_byte_data(PROXY_Addr, 0x0E | 0x80, 0x20)

    # Select control register, 0x0F(15), with command register 0x80(128)
    #       0x20(32)    Proximity uses CH1 diode
    bus.write_byte_data(PROXY_Addr, 0x0F | 0x80, 0x20)

    time.sleep(0.8)

def sendProximityData(sensorVals):
    print("Sending proximity data ...")
    
    # Read data back from 0x18(57) with command register 0x80(128), 2 bytes
    # Proximity lsb, Proximity msb
    data = bus.read_i2c_block_data(PROXY_Addr, 0x18 | 0x80, 2)

    # Convert the data
    proximity = data[1] * 256 + data[0]

    # store the proximity measurement into sensorVals dict
    print("Proximity: {}".format(proximity))
    sensorVals[PROXY_SENSOR_IDX] = round(proximity, 5)


# Reference: https://github.com/ControlEverythingCommunity/TSL2561/blob/master/Python/TSL2561.py
def setupTSL(sensorVals):

    # Select control register, 0x00(00) with command register, 0x80(128)
    #       0x03(03)    Power ON mode
    bus.write_byte_data(TSL_Addr, 0x00 | 0x80, 0x03)

    # Select timing register, 0x01(01) with command register, 0x80(128)
    #       0x02(02)    Nominal integration time = 402ms
    bus.write_byte_data(TSL_Addr, 0x01 | 0x80, 0x02)

    time.sleep(0.5)

def sendTSLData(sensorVals):
    # Read data back from 0x0C(12) with command register, 0x80(128), 2 bytes
    # ch0 LSB, ch0 MSB
    data = bus.read_i2c_block_data(TSL_Addr, 0x0C | 0x80, 2)

    # Read data back from 0x0E(14) with command register, 0x80(128), 2 bytes
    # ch1 LSB, ch1 MSB
    data1 = bus.read_i2c_block_data(TSL_Addr, 0x0E | 0x80, 2)

    # Convert the data
    ch0 = data[1] * 256 + data[0]
    ch1 = data1[1] * 256 + data1[0]

    # post the current Visible and IR lux values
    print("Visible Light: {}".format(ch0 - ch1))
    print("Infrared Light: {}".format(ch1))
    sensorVals[VISIBLE_LIGHT_SENSOR_IDX] = round((ch0 - ch1), 5)
    sensorVals[INFRARED_LIGHT_SENSOR_IDX] = round(ch1, 5)

# declare the canonical Raspberry Pi routines.

def on_connect(client, data, flags, result):
    print('client connected result: '+connack_string(result))

def on_disconnect(client, data, rc):
    if rc != 0:
        print('client disconnected unexpectedly')

def on_publish(client, data, mid):
    print('published ', str(mid))
    print("---------------------------  Data was published ------------------")

def on_message(client, userdata, msg):
    data = msg.payload.decode()
    print("Message received: "+ data)

    command = json.loads(data)

    resp = {
        str(command["si"]): str(command["c"])
    }

    data = json.dumps(resp)

    r = client.publish("device/%s/records"%(MQTT_DEVKEY), payload=data, qos=0, retain=False)
    print(r)

def sendStatus(sensorVals):
    print("Sending...")
    
    # gather all the sensor data into sensorVals
    sendHCPAData(sensorVals)
    sendMPLData(sensorVals)
    # sendGasData(sensorVals)
    # sendSoilData(sensorVals)
    # sendProximityData(sensorVals)
    # sendTSLData(sensorVals)

    # convert the sensorVals dictionary to a JSON Object
    data = json.dumps(sensorVals, separators=(',', ':'))
    
    # DEBUG
    print(sensorVals)
    print("device/%s/records"%(MQTT_DEVKEY))
    print(data)

    # publish that data.
    # Calling reconnect every time want to publish a message seem pretty
    # kludgy, but it seems to work.  Maybe?
    client.reconnect()
    mmi = client.publish("device/%s/records"%(MQTT_DEVKEY), payload=data, 
    qos=2, retain=False)
    print("Result of attempting to publish sensorVals: %s"%(mqtt.error_string(mmi.rc)))
    if mmi.is_published :
        print("Data was published")
    else :
        print("Data was not published")
    
# Here's where execution starts.  Get an MQTT client.  We'll use it to
# send sensor data and receive commands.
# This is an insecure system.  

client = mqtt.Client(client_id="Gigibits")
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message
client.on_publish = on_publish

# set up the numeric precision
getcontext().prec = 5

print("Connecting to {}".format(MQTT_BROKER))
print("Using devkey {}".format(MQTT_DEVKEY))

breakpoint()
client.connect(MQTT_BROKER, MQTT_PORT)
print("returned from connect")
client.subscribe('server/%s/command'%(MQTT_DEVKEY), 1)
print("returned from subscribe")

# setup all the sensors and actuators.
# Get the bus that we'll use to read sensor data
bus = smbus.SMBus(1)
print("returned from smbus")

setupMPL()
#setupGas()
#setupSoilData()
#setupProximity()
#setupTSL()

print("Returned from setup")

# Loop through all the sensors.
client.loop_start()

while True:
    sendStatus(sensorVals)
    # clear sensorVals so we won't get confused next time
    sensorVals = {}

    time.sleep(10)
    
