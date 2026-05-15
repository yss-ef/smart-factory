from flask import Flask, render_template_string, jsonify
import paho.mqtt.client as mqtt
import json

app = Flask(__name__)

latest = {"good": 0, "defective": 0, "total": 0, "timestamp": "-"}
history = []

# ── MQTT ────────────────────────────────────────────
def on_message(client, userdata, msg):
    global latest
    data = json.loads(msg.payload)
    latest = data
    history.append(data)
    if len(history) > 50:   # garde les 50 derniers
        history.pop(0)

mqttc = mqtt.Client()
mqttc.on_message = on_message
mqttc.connect("localhost", 1883)
mqttc.subscribe("factory/counts")
mqttc.loop_start()

# ── HTML Dashboard ───────────────────────────────────
HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta http-equiv="refresh" content="2">
  <title>Smart Factory Dashboard</title>
  <style>
    body { font-family: Arial; background: #1a1a2e; color: white; text-align: center; padding: 40px; }
    h1   { color: #00d4ff; }
    .cards { display: flex; justify-content: center; gap: 30px; margin: 40px 0; }
    .card  { background: #16213e; border-radius: 15px; padding: 30px 50px; }
    .card h2 { font-size: 3em; margin: 0; }
    .good { border-top: 4px solid #00ff88; }
    .bad  { border-top: 4px solid #ff4444; }
    .total{ border-top: 4px solid #00d4ff; }
    .ts   { color: #888; margin-top: 30px; }
    table { margin: 20px auto; border-collapse: collapse; width: 60%; }
    th, td { padding: 8px 16px; border: 1px solid #333; }
    th { background: #16213e; color: #00d4ff; }
  </style>
</head>
<body>
  <h1>🏭 Smart Factory Dashboard</h1>
  <div class="cards">
    <div class="card good">
      <p>✅ Good</p>
      <h2 id="good">{{ data.good }}</h2>
    </div>
    <div class="card bad">
      <p>❌ Defective</p>
      <h2 id="def">{{ data.defective }}</h2>
    </div>
    <div class="card total">
      <p>📦 Total</p>
      <h2 id="total">{{ data.total }}</h2>
    </div>
  </div>
  <p class="ts">Dernière mise à jour : {{ data.timestamp }}</p>

  <h3>Historique</h3>
  <table>
    <tr><th>Timestamp</th><th>Good</th><th>Defective</th><th>Total</th></tr>
    {% for h in history %}
    <tr>
      <td>{{ h.timestamp }}</td>
      <td style="color:#00ff88">{{ h.good }}</td>
      <td style="color:#ff4444">{{ h.defective }}</td>
      <td>{{ h.total }}</td>
    </tr>
    {% endfor %}
  </table>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML, data=latest, history=list(reversed(history)))

@app.route("/data")
def data():
    return jsonify(latest)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
