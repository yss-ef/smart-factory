# Smart Factory - AI Quality Control

A real-time edge computing system for automated quality control in a manufacturing environment. This project uses computer vision to detect product defects and provides a real-time dashboard for monitoring production stats.

## 🚀 Features

- **Real-time Detection**: Uses YOLOv8 (via Ultralytics) for high-speed defect detection.
- **Hardware Integration**: Designed to work with Raspberry Pi and Picamera2.
- **Messaging**: Publishes production stats (good vs. defective) to an MQTT broker.
- **Dashboard**: A Flask-based web interface to visualize production metrics in real-time.
- **Logging**: Keeps a persistent record of all detections in CSV format.

## 📂 Project Structure

- `src/detect.py`: Main detection loop and camera interface.
- `src/dashboard.py`: Flask web server for the visualization dashboard.
- `src/mqtt_client.py`: Shared MQTT logic for sending/receiving data.
- `models/`: Directory for trained YOLO models (e.g., `best.pt`).
- `logs/`: CSV logs for production history.

## 🛠️ Setup

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd smart-factory
   ```

2. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: For CPU-only environments, use `--extra-index-url https://download.pytorch.org/whl/cpu`.*

4. **Run the system**:
   - Start the MQTT broker (e.g., Mosquitto).
   - Run the detector: `python src/detect.py`
   - Run the dashboard: `python src/dashboard.py`

## 📊 Dashboard
The dashboard will be available at `http://localhost:5000` by default.

## 📝 License
MIT
