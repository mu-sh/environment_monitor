# main.py - outdoor weather node (ESP32 / MicroPython)
# Publishes temperature, pressure, humidity as JSON to MQTT every PUBLISH_S.
# Topic schema: home/<location>/<node_id>/state   (matches as-built README)
# Sensor: genuine BME280 (chip ID 0x60), I2C address auto-detected (0x76/0x77).

import time
import json
import network
from machine import I2C, Pin
from umqtt.simple import MQTTClient
import bme280

# ----- CONFIG (set these) ---------------------------------------------------
WIFI_SSID   = "YOUR_SSID"
WIFI_PASS   = "YOUR_PASSWORD"
BROKER      = "192.168.x.x"      # Pi running Mosquitto
LOCATION    = "garden"           # <location> in the topic
NODE_ID     = "weather"          # <node_id> in the topic
PUBLISH_S   = 15                 # publish interval, seconds
SCL_PIN     = 22
SDA_PIN     = 21
# ---------------------------------------------------------------------------

TOPIC = "home/{}/{}/state".format(LOCATION, NODE_ID).encode()


def connect_wifi():
    w = network.WLAN(network.STA_IF)
    w.active(True)
    if not w.isconnected():
        print("WiFi: connecting...")
        w.connect(WIFI_SSID, WIFI_PASS)
        while not w.isconnected():
            time.sleep(0.5)
    print("WiFi:", w.ifconfig()[0])
    return w


def make_sensor():
    i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN))
    found = i2c.scan()
    addr = 0x76 if 0x76 in found else 0x77 if 0x77 in found else None
    if addr is None:
        raise RuntimeError("No BME280 on I2C bus, scan={}".format(found))
    print("BME280 at", hex(addr))
    return bme280.BME280(i2c=i2c, address=addr)


def connect_mqtt():
    c = MQTTClient(NODE_ID, BROKER)
    c.connect()
    print("MQTT: connected to", BROKER)
    return c


def main():
    connect_wifi()
    bme = make_sensor()
    client = connect_mqtt()

    while True:
        t, p, h = bme.read_compensated_data()
        payload = {
            "temperature": round(t / 100, 1),     # degC
            "pressure":    round(p / 25600, 1),    # hPa
            "humidity":    round(h / 1024, 1),     # %RH
        }
        msg = json.dumps(payload)

        try:
            client.publish(TOPIC, msg)
            print("pub", TOPIC.decode(), msg)
        except Exception as e:
            # retry the connection on publish failure, then carry on
            print("publish failed:", e, "- reconnecting")
            try:
                client = connect_mqtt()
            except Exception as e2:
                print("reconnect failed:", e2)

        time.sleep(PUBLISH_S)


main()
