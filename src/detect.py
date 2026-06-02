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
IMG_SIZE   = 320
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
if not os.path.exists(os.path.dirname(LOG_PATH)):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

with open(LOG_PATH, "a", newline="") as f:
    writer = csv.writer(f)
    if os.path.getsize(LOG_PATH) == 0:
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

        # Logique: Si un défaut est détecté -> Defective. Sinon -> Good.
        if len(results.boxes) > 0:
            key = "defective"
            # On logue le défaut le plus probable
            top_box = results.boxes[0]
            label   = model.names[int(top_box.cls[0])]
            conf    = float(top_box.conf[0])
            print(f"[DEFECT] {label} detected ({conf:.2f})")
        else:
            key = "good"
            label = "OK"
            conf = 1.0
            print("[SAFE] PCB quality OK")

        counts[key] += 1
        total += 1

        # Log CSV
        with open(LOG_PATH, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                label,
                f"{conf:.2f}"
            ])

        # Envoie MQTT périodiquement
        if total % SEND_EVERY == 0:
            send_counts(counts["good"], counts["defective"], total)

        time.sleep(0.1)

except KeyboardInterrupt:
    print(f"\n✅ Session terminée")
    print(f"   Good     : {counts['good']}")
    print(f"   Defective: {counts['defective']}")
    print(f"   Total    : {total}")
    picam.stop()
