# main.py - ESP32 BMP280 -> MQTT environmental node
# Publishes temperature + pressure as JSON to the Pi broker.
# (BMP280 has no humidity sensor, so humidity is intentionally dropped.)

# ============ EDIT THESE ============
WIFI_SSID = "VM4122388"        # must be a 2.4GHz network - ESP32 can't see 5GHz
WIFI_PASS = "h9hyYcpzvjrb"
MQTT_HOST = "192.168.0.92"           # your Pi's IP (the one that returned the 204)
LOCATION  = "living-room"
NODE_ID   = "esp32-01"
INTERVAL  = 15                      # seconds between readings
# ====================================

import json, time, network
from machine import I2C, Pin
from umqtt.simple import MQTTClient
import bme280   # robert-hh integer driver; drives BMP280 too (humidity reads 0)

def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("wifi: connecting to", WIFI_SSID)
        wlan.connect(WIFI_SSID, WIFI_PASS)
        t0 = time.time()
        while not wlan.isconnected():
            if time.time() - t0 > 20:
                raise RuntimeError("wifi connect timeout - check SSID/pass and 2.4GHz")
            time.sleep(0.5)
    print("wifi: connected", wlan.ifconfig()[0])

def find_sensor(i2c):
    found = i2c.scan()
    print("i2c scan:", [hex(a) for a in found])
    for addr in (0x76, 0x77):
        if addr in found:
            return addr
    raise RuntimeError("no BMP280 found on I2C - check wiring (checked 0x76/0x77)")

def main():
    wifi_connect()

    i2c = I2C(0, scl=Pin(22), sda=Pin(21))
    addr = find_sensor(i2c)
    print("sensor at", hex(addr))
    sensor = bme280.BME280(i2c=i2c, address=addr)

    topic = "home/{}/{}/state".format(LOCATION, NODE_ID)
    client = MQTTClient(NODE_ID, MQTT_HOST, keepalive=60)
    client.connect()
    print("mqtt: connected ->", MQTT_HOST)
    print("publishing to", topic)

    while True:
        t, p, _ = sensor.read_compensated_data()   # h ignored: BMP280 has no humidity
        payload = {
            "temperature": round(t / 100, 2),       # degC
            "pressure":    round(p / 25600, 2),      # hPa
        }
        try:
            client.publish(topic, json.dumps(payload))
            print("pub", payload)
        except OSError as e:
            print("publish failed, reconnecting:", e)
            try:
                client.connect()
            except OSError:
                pass
        time.sleep(INTERVAL)

main()
