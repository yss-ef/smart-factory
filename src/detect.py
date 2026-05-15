import cv2
import sys
import os
import csv
import time
from datetime import datetime
from picamera2 import Picamera2
from ultralytics import YOLO
sys.path.append(os.path.dirname(__file__))
from mqtt_client import connect, send_counts

# ── Config ──────────────────────────────────────────
MODEL_PATH = "models/best.pt"
LOG_PATH   = "logs/production.csv"
CONF       = 0.5
IMG_SIZE   = 416
SEND_EVERY = 5   # envoie MQTT toutes les 5 détections
# ────────────────────────────────────────────────────

model = YOLO(MODEL_PATH)
connect()

# Init caméra
picam = Picamera2()
config = picam.create_preview_configuration(
    main={"size": (IMG_SIZE, IMG_SIZE), "format": "RGB888"}
)
picam.configure(config)
picam.start()
time.sleep(1)

# Init CSV log
with open(LOG_PATH, "a", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["timestamp", "label", "confidence"])

counts = {"good": 0, "defective": 0}
total  = 0

print("🚀 Détection démarrée — Ctrl+C pour arrêter")

try:
    while True:
        # Capture frame
        frame = picam.capture_array()

        # Inférence
        results = model(frame, conf=CONF, imgsz=IMG_SIZE, verbose=False)[0]

        for box in results.boxes:
            cls   = int(box.cls[0])
            label = model.names[cls]
            conf  = float(box.conf[0])

            # Normalise label → good / defective
            if label in ("good", "no_defect"):
                key = "good"
            else:
                key = "defective"

            counts[key] += 1
            total        += 1

            # Log CSV
            with open(LOG_PATH, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    label,
                    f"{conf:.2f}"
                ])

            print(f"[{key.upper()}] {label} ({conf:.2f}) "
                  f"| Good: {counts['good']} "
                  f"| Defective: {counts['defective']}")

        # Envoie MQTT périodiquement
        if total % SEND_EVERY == 0 and total > 0:
            send_counts(counts["good"], counts["defective"], total)

        time.sleep(0.1)

except KeyboardInterrupt:
    print(f"\n✅ Session terminée")
    print(f"   Good     : {counts['good']}")
    print(f"   Defective: {counts['defective']}")
    print(f"   Total    : {total}")
    picam.stop()
