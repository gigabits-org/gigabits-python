#!/usr/bin/env python

import paho.mqtt.client as mqtt
import random
import json
import time
import os
from dotenv import load_dotenv
load_dotenv()

MQTT_BROKER=os.getenv('MQTT_BROKER')
MQTT_PORT=int(os.getenv('MQTT_PORT'))
MQTT_USERNAME=os.getenv('MQTT_USERNAME')
MQTT_PASSWORD=os.getenv('MQTT_PASSWORD')

def on_connect(client, data, flags, result):
    print('client connected')

def on_disconnect(client, data, status):
    print('client disconnected')

def on_publish(client, data, mid):
    print('published ', str(mid))

def on_message(client, userdata, msg):
    data = msg.payload.decode()
    print("Message received: "+ data)

    command = json.loads(data)

    resp = {
        str(command["si"]): str(command["c"])
    }

    data = json.dumps(resp)

    r = client.publish("device/%s/records"%(devKey), payload=data, qos=0, retain=False)
    print(r)

def sendStatus():
    print("Sending...")
    infoResponse = {
        "1": random.randint(0, 100),
        "2": random.randint(0, 100),
        "4": random.randint(0, 100),
        "5": random.randint(0, 100),
        "6": random.randint(0, 100),
        "7": random.randint(0, 100),
        "8": random.randint(0, 100),
    }

    data = json.dumps(infoResponse)

    r = client.publish("device/%s/records"%(devKey), payload=data, qos=0, retain=False)
    print(r)


    # infoResponse = {
        # "1": random.randint(0, 100),
        # "2": random.randint(0, 200),
        # "3": random.randint(0, 10000),
    # }

    # data = json.dumps(infoResponse)

    # r = client.publish("device/%s/records"%(devKey2), payload=data, qos=0, retain=False)
    # print(r)

activeStatus = [False, False, False, False]
devKey = "Iur8LTvFvR75kcJAMdzr3EJ"
client = mqtt.Client(client_id="dummyDevice")
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message
client.on_publish = on_publish

print("Connecting to {}".format(MQTT_BROKER))

client.connect(MQTT_BROKER, MQTT_PORT)
client.subscribe('server/%s/command'%(devKey), 1)

client.loop_start()

while True:
    sendStatus()
    time.sleep(3)
