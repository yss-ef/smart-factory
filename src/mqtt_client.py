import paho.mqtt.client as mqtt
import json
import time

BROKER = "localhost"
PORT = 1883
TOPIC = "factory/counts"

client = mqtt.Client()

def connect():
    client.connect(BROKER, PORT)
    client.loop_start()
    print("MQTT connecté ✅")

def send_counts(good, defective, total):
    payload = json.dumps({
        "good": good,
        "defective": defective,
        "total": total,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })
    client.publish(TOPIC, payload)
