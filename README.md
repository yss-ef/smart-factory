# Smart factory: AI quality control

The smart factory is a real-time edge computing system designed for automated
quality control in manufacturing environments. It uses computer vision to
detect product defects and provides a dashboard for monitoring production
statistics.

## Features

- Real-time detection: Uses YOLOv8 for high-speed defect detection.
- Hardware integration: Designed for Raspberry Pi and Picamera2.
- Messaging: Publishes production statistics to an MQTT broker.
- Dashboard: Features a Flask-based web interface for real-time production
  metrics.
- Logging: Maintains persistent records of detections in CSV format.

## Project structure

- `src/detect.py`: Main detection loop and camera interface.
- `src/dashboard.py`: Flask web server for the visualization dashboard.
- `src/mqtt_client.py`: Shared MQTT logic for data transmission.
- `models/`: Directory for trained YOLO models.
- `logs/`: CSV logs for production history.

## Setup

Follow these steps to configure the system:

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd smart-factory
   ```
2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the system:
   - Start the MQTT broker.
   - Run the detector: `python src/detect.py`
   - Run the dashboard: `python src/dashboard.py`

## Dashboard

The dashboard is accessible at `http://localhost:5000` by default.

## License

This project is licensed under the MIT License.
