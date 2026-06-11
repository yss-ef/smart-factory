import paho.mqtt.client as mqtt
import json
import time
import logging

# Codes ANSI pour la coloration
CLR_RED    = "\033[91m"
CLR_GREEN  = "\033[92m"
CLR_YELLOW = "\033[93m"
CLR_BOLD   = "\033[1m"
CLR_END    = "\033[0m"

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

BROKER = "localhost"
PORT = 1883
TOPIC_STATS = "factory/counts"
TOPIC_ALERTS = "factory/alerts"

client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info(f"{CLR_GREEN}{CLR_BOLD}CONNECTÉ AU BROKER MQTT{CLR_END}")
    else:
        logging.error(f"{CLR_RED}ÉCHEC DE CONNEXION MQTT, CODE: {rc}{CLR_END}")

def on_disconnect(client, userdata, rc):
    logging.warning(f"{CLR_YELLOW}DÉCONNEXION MQTT - TENTATIVE DE RECONNEXION...{CLR_END}")
    try:
        client.reconnect()
    except Exception as e:
        logging.error(f"{CLR_RED}ERREUR RECONNEXION : {e}{CLR_END}")

client.on_connect = on_connect
client.on_disconnect = on_disconnect

def connect():
    try:
        client.connect(BROKER, PORT, keepalive=60)
        client.loop_start()
    except Exception as e:
        logging.error(f"{CLR_RED}IMPOSSIBLE DE SE CONNECTER AU BROKER : {e}{CLR_END}")

def send_counts(good, defective, total):
    payload = json.dumps({
        "good": good,
        "defective": defective,
        "total": total,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })
    client.publish(TOPIC_STATS, payload, qos=1)

def send_alert(defect_type, confidence):
    payload = json.dumps({
        "alert": "DEFECT_DETECTED",
        "type": defect_type,
        "confidence": round(confidence, 2),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })
    client.publish(TOPIC_ALERTS, payload, qos=2)
    logging.info(f"{CLR_RED}{CLR_BOLD}ALERTE ENVOYÉE : {defect_type.upper()} ({confidence:.2f}){CLR_END}")
