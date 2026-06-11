import cv2
import sys
import os
import csv
import time
import logging
from datetime import datetime
# Codes ANSI
CLR_RED    = "\033[91m"
CLR_GREEN  = "\033[92m"
CLR_YELLOW = "\033[93m"
CLR_BOLD   = "\033[1m"
CLR_END    = "\033[0m"

try:
    from picamera2 import Picamera2
except ImportError:
    from camera_mock import Picamera2
    print(f"{CLR_YELLOW}PICAMERA2 NON DÉTECTÉ - MODE SIMULATION ACTIVÉ{CLR_END}")
from ultralytics import YOLO

sys.path.append(os.path.dirname(__file__))
from mqtt_client import connect, send_counts, send_alert

# ── Configuration ─────────────────────────────────────
MODEL_PATH = "models/best.pt"
LOG_PATH   = "logs/production.csv"
CONF       = 0.5
IMG_SIZE   = 320
SEND_STATS_EVERY = 5 
GPIO_SIGNAL_PIN  = 18 # Pin simulée pour le signal électrique
# ──────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def init_camera():
    try:
        picam = Picamera2()
        config = picam.create_preview_configuration(
            main={"size": (IMG_SIZE, IMG_SIZE), "format": "RGB888"}
        )
        picam.configure(config)
        picam.start()
        logging.info(f"{CLR_GREEN}CAMÉRA INITIALISÉE{CLR_END}")
        return picam
    except Exception as e:
        logging.error(f"{CLR_RED}ERREUR CAMÉRA : {e}{CLR_END}")
        return None

# Simulation GPIO
def trigger_electric_signal(duration=0.5):
    logging.info(f"{CLR_YELLOW}{CLR_BOLD}SIGNAL ÉLECTRIQUE : ACTIVÉ (GPIO {GPIO_SIGNAL_PIN}){CLR_END}")
    time.sleep(duration)
    logging.info(f"{CLR_YELLOW}SIGNAL ÉLECTRIQUE : DÉSACTIVÉ{CLR_END}")

# Init Modèle
try:
    model = YOLO(MODEL_PATH)
except Exception as e:
    logging.error(f"{CLR_RED}ERREUR CHARGEMENT MODÈLE : {e}{CLR_END}")
    sys.exit(1)

connect()
picam = init_camera()

# Init Logs
if not os.path.exists(os.path.dirname(LOG_PATH)):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

if not os.path.exists(LOG_PATH) or os.path.getsize(LOG_PATH) == 0:
    with open(LOG_PATH, "w", newline="") as f:
        csv.writer(f).writerow(["timestamp", "label", "confidence"])

counts = {"good": 0, "defective": 0}
total  = 0

logging.info(f"{CLR_GREEN}{CLR_BOLD}SYSTÈME DE DÉTECTION PRÊT{CLR_END}")

try:
    while True:
        if picam is None:
            logging.warning(f"{CLR_YELLOW}TENTATIVE DE RECONNEXION CAMÉRA DANS 5S...{CLR_END}")
            time.sleep(5)
            picam = init_camera()
            continue

        try:
            frame = picam.capture_array()
        except Exception as e:
            logging.error(f"{CLR_RED}ÉCHEC CAPTURE FRAME : {e}{CLR_END}")
            picam = None
            continue

        results = model(frame, conf=CONF, imgsz=IMG_SIZE, verbose=False)[0]

        # Logique de détection
        if len(results.boxes) > 0:
            key = "defective"
            top_box = results.boxes[0]
            label   = model.names[int(top_box.cls[0])]
            conf    = float(top_box.conf[0])
            
            # ACTIONS IMMÉDIATES
            send_alert(label, conf)
            trigger_electric_signal(0.3)
        else:
            key = "good"
            label = "OK"
            conf = 1.0

        counts[key] += 1
        total += 1

        # Log CSV
        try:
            with open(LOG_PATH, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), label, f"{conf:.2f}"])
        except Exception as e:
            logging.error(f"{CLR_RED}ERREUR ÉCRITURE LOG : {e}{CLR_END}")

        # Stats périodiques
        if total % SEND_STATS_EVERY == 0:
            send_counts(counts["good"], counts["defective"], total)

        time.sleep(0.05) # Fluidité

except KeyboardInterrupt:
    logging.info("Interruption manuelle détectée")
finally:
    if picam:
        picam.stop()
    logging.info("Système arrêté proprement")
