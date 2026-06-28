import json
from paho.mqtt import client as mqtt
from influxdb import InfluxDBClient

influx = InfluxDBClient(host="localhost", port=8086, database="env")

def on_connect(client, userdata, flags, rc, properties=None):
    print("MQTT connected", rc)
    client.subscribe("home/+/+/state")

def on_message(client, userdata, msg):
    try:
        _, location, node_id, _ = msg.topic.split("/")
        payload = json.loads(msg.payload)
        fields = {k: float(v) for k, v in payload.items() if isinstance(v, (int, float))}
        if not fields:
            return
        influx.write_points([{
            "measurement": "environment",
            "tags": {"location": location, "node": node_id},
            "fields": fields,
        }])
        print(location, node_id, fields)
    except Exception as e:
        print("drop:", e, msg.topic, msg.payload[:80])

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect("localhost", 1883, 60)
client.loop_forever()