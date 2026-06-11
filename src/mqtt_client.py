import paho.mqtt.client as mqtt
import json
import time
import logging
import os
import ssl

# Codes ANSI pour la coloration
CLR_RED    = "\033[91m"
CLR_GREEN  = "\033[92m"
CLR_YELLOW = "\033[93m"
CLR_BOLD   = "\033[1m"
CLR_END    = "\033[0m"

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# --- CONFIGURATION MQTT SECURE ---
BROKER = os.getenv("MQTT_BROKER", "localhost")
PORT = int(os.getenv("MQTT_PORT", 8883)) # Port standard pour MQTT over TLS
TOPIC_STATS = "factory/counts"
TOPIC_ALERTS = "factory/alerts"

# Chemins vers les certificats (à configurer en prod)
CA_CERT = "certs/ca.crt"
CLIENT_CERT = "certs/client.crt"
CLIENT_KEY = "certs/client.key"

client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info(f"{CLR_GREEN}{CLR_BOLD}CONNECTÉ AU BROKER MQTT (SÉCURISÉ){CLR_END}")
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
        # Activation TLS si le certificat CA existe
        if os.path.exists(CA_CERT):
            logging.info(f"{CLR_GREEN}Activation du chiffrement TLS...{CLR_END}")
            client.tls_set(ca_certs=CA_CERT, 
                           certfile=CLIENT_CERT if os.path.exists(CLIENT_CERT) else None,
                           keyfile=CLIENT_KEY if os.path.exists(CLIENT_KEY) else None,
                           cert_reqs=ssl.CERT_REQUIRED,
                           tls_version=ssl.PROTOCOL_TLSv1_2)
            # Désactiver la vérification du hostname si on utilise "localhost" ou des IPs sans DNS
            client.tls_insecure_set(True) 
        else:
            logging.warning(f"{CLR_YELLOW}CERTIFICATS NON TROUVÉS - CONNEXION NON CHIFFRÉE (NON RECOMMANDÉ){CLR_END}")
            global PORT
            PORT = 1883 # Repli sur le port standard non sécurisé pour le dev

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

