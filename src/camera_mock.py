import numpy as np
import time

class Picamera2:
    def __init__(self):
        print("MOCK: Caméra initialisée (Simulation)")
        self.running = False

    def create_preview_configuration(self, **kwargs):
        return {}

    def configure(self, config):
        pass

    def start(self):
        self.running = True
        print("MOCK: Flux caméra démarré")

    def stop(self):
        self.running = False
        print("MOCK: Flux caméra arrêté")

    def capture_array(self):
        # Simule une image aléatoire (RGB 320x320)
        # Parfois on simule un défaut (en changeant un pixel ou juste par probabilité)
        time.sleep(0.1)
        return np.random.randint(0, 255, (320, 320, 3), dtype=np.uint8)
