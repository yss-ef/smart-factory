from flask import Flask, render_template_string, jsonify
import paho.mqtt.client as mqtt
import json
import logging
from datetime import datetime

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

app = Flask(__name__)

# État global enrichi
stats = {"good": 0, "defective": 0, "total": 0, "last_update": "-"}
alerts_log = []
history_series = {"timestamps": [], "good": [], "defective": []}

# ── MQTT ────────────────────────────────────────────
def on_message(client, userdata, msg):
    global stats, alerts_log
    try:
        data = json.loads(msg.payload)
        
        if msg.topic == "factory/counts":
            stats["good"] = data["good"]
            stats["defective"] = data["defective"]
            stats["total"] = data["total"]
            stats["last_update"] = data["timestamp"]
            
            # Mise à jour des séries temporelles (max 30 points)
            history_series["timestamps"].append(data["timestamp"].split(" ")[1])
            history_series["good"].append(data["good"])
            history_series["defective"].append(data["defective"])
            
            if len(history_series["timestamps"]) > 30:
                history_series["timestamps"].pop(0)
                history_series["good"].pop(0)
                history_series["defective"].pop(0)
        
        elif msg.topic == "factory/alerts":
            alert_entry = {
                "type": data["type"].upper(),
                "conf": f"{data['confidence']*100:.0f}%",
                "time": data["timestamp"].split(" ")[1],
                "id": datetime.now().timestamp()
            }
            alerts_log.insert(0, alert_entry)
            if len(alerts_log) > 15:
                alerts_log.pop()

    except Exception as e:
        logging.error(f"Erreur traitement MQTT : {e}")

mqttc = mqtt.Client()
mqttc.on_message = on_message
mqttc.connect("localhost", 1883)
mqttc.subscribe([("factory/counts", 0), ("factory/alerts", 0)])
mqttc.loop_start()

# ── Dashboard HTML/JS ────────────────────────────────
HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Factory | Control Center</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0f172a;
            --surface: #1e293b;
            --surface-light: #334155;
            --accent: #38bdf8;
            --success: #22c55e;
            --danger: #ef4444;
            --warning: #f59e0b;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --border: #334155;
            --font-main: 'Inter', sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
        }

        * { box-sizing: border-box; }
        body { 
            font-family: var(--font-main); 
            background: var(--bg); 
            color: var(--text-primary); 
            margin: 0; 
            padding: 0;
            overflow-x: hidden;
        }

        /* Header */
        header {
            background: rgba(15, 23, 42, 0.8);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid var(--border);
            padding: 1rem 2rem;
            position: sticky;
            top: 0;
            z-index: 100;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
            font-weight: 700;
            letter-spacing: -0.5px;
            font-size: 1.25rem;
        }
        .logo span { color: var(--accent); }

        .status-badge {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(34, 197, 94, 0.1);
            color: var(--success);
            padding: 6px 12px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            border: 1px solid rgba(34, 197, 94, 0.2);
        }
        .pulse {
            width: 8px;
            height: 8px;
            background: var(--success);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7); }
            70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(34, 197, 94, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
        }

        /* Main Layout */
        main { padding: 2rem; max-width: 1400px; margin: 0 auto; }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .stat-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            transition: transform 0.2s;
        }
        .stat-card:hover { transform: translateY(-2px); border-color: var(--surface-light); }
        .stat-card h3 { color: var(--text-secondary); font-size: 0.875rem; font-weight: 500; margin: 0 0 0.75rem 0; text-transform: uppercase; letter-spacing: 0.05em; }
        .stat-card .value { font-family: var(--font-mono); font-size: 2rem; font-weight: 600; margin: 0; }

        /* Yield Progress */
        .yield-wrap { margin-top: 1rem; }
        .yield-bar-bg { background: var(--border); height: 6px; border-radius: 3px; overflow: hidden; }
        .yield-bar-fill { background: var(--success); height: 100%; transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1); }

        /* Content Grid */
        .content-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 1.5rem;
        }

        @media (max-width: 1024px) { .content-grid { grid-template-columns: 1fr; } }

        .panel {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
        }
        .panel h2 { font-size: 1.125rem; margin: 0 0 1.5rem 0; color: var(--text-secondary); display: flex; align-items: center; gap: 10px; }

        /* Alerts List */
        .alert-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px;
            border-radius: 8px;
            background: rgba(255, 68, 68, 0.05);
            border: 1px solid rgba(255, 68, 68, 0.1);
            margin-bottom: 0.75rem;
            animation: slideIn 0.3s ease-out;
        }
        @keyframes slideIn { from { transform: translateX(20px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
        
        .alert-type { font-weight: 700; color: var(--danger); font-size: 0.875rem; flex-grow: 1; }
        .alert-conf { font-family: var(--font-mono); font-size: 0.75rem; color: var(--text-secondary); }
        .alert-time { color: var(--text-secondary); font-size: 0.75rem; }

        /* Scrollbar */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: var(--bg); }
        ::-webkit-scrollbar-thumb { background: var(--surface-light); border-radius: 4px; }
    </style>
</head>
<body>
    <header>
        <div class="logo">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M2 20h20"></path><path d="M5 20V8l7-4 7 4v12"></path><path d="M9 20v-4h6v4"></path></svg>
            SMART<span>FACTORY</span>
        </div>
        <div class="status-badge">
            <div class="pulse"></div>
            LIVE MONITORING
        </div>
    </header>

    <main>
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Conformes</h3>
                <p class="value" id="val-good" style="color: var(--success);">0</p>
            </div>
            <div class="stat-card">
                <h3>Défauts</h3>
                <p class="value" id="val-bad" style="color: var(--danger);">0</p>
            </div>
            <div class="stat-card">
                <h3>Total</h3>
                <p class="value" id="val-total">0</p>
            </div>
            <div class="stat-card">
                <h3>Qualité (Yield)</h3>
                <p class="value" id="val-yield">0%</p>
                <div class="yield-wrap">
                    <div class="yield-bar-bg"><div id="yield-bar" class="yield-bar-fill" style="width: 0%"></div></div>
                </div>
            </div>
        </div>

        <div class="content-grid">
            <div class="panel">
                <h2>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
                    Flux de Production
                </h2>
                <canvas id="prodChart" height="220"></canvas>
            </div>
            <div class="panel">
                <h2>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
                    Défauts Récents
                </h2>
                <div id="alerts-list" style="max-height: 400px; overflow-y: auto;">
                    <!-- Alerts list items -->
                </div>
            </div>
        </div>
    </main>

    <script>
        // Chart configuration
        const ctx = document.getElementById('prodChart').getContext('2d');
        const prodChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Conformes',
                        data: [],
                        borderColor: '#22c55e',
                        backgroundColor: 'rgba(34, 197, 94, 0.05)',
                        fill: true,
                        tension: 0.4,
                        borderWidth: 3,
                        pointRadius: 0
                    },
                    {
                        label: 'Défauts',
                        data: [],
                        borderColor: '#ef4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.05)',
                        fill: true,
                        tension: 0.4,
                        borderWidth: 3,
                        pointRadius: 0
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { intersect: false, mode: 'index' },
                plugins: { 
                    legend: { display: false }
                },
                scales: {
                    x: { 
                        ticks: { color: '#94a3b8', font: { size: 10 } }, 
                        grid: { display: false } 
                    },
                    y: { 
                        ticks: { color: '#94a3b8', font: { size: 10 } }, 
                        grid: { color: '#334155', borderDash: [5, 5] },
                        beginAtZero: true
                    }
                }
            }
        });

        function update() {
            $.getJSON('/api/data', function(data) {
                // Update Numeric Values
                $('#val-good').text(data.stats.good.toLocaleString());
                $('#val-bad').text(data.stats.defective.toLocaleString());
                $('#val-total').text(data.stats.total.toLocaleString());
                
                let yield = data.stats.total > 0 ? (data.stats.good / data.stats.total * 100).toFixed(1) : 0;
                $('#val-yield').text(yield + '%');
                $('#yield-bar').css('width', yield + '%');

                // Update Chart
                prodChart.data.labels = data.series.timestamps;
                prodChart.data.datasets[0].data = data.series.good;
                prodChart.data.datasets[1].data = data.series.defective;
                prodChart.update('none');

                // Update Alerts with slideIn animation only for new ones
                let alertHtml = "";
                data.alerts.forEach(a => {
                    alertHtml += `
                        <div class="alert-item">
                            <div class="alert-type">${a.type}</div>
                            <div class="alert-conf">${a.conf}</div>
                            <div class="alert-time">${a.time}</div>
                        </div>
                    `;
                });
                $('#alerts-list').html(alertHtml);
            });
        }

        setInterval(update, 1000);
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/api/data")
def api_data():
    return jsonify({
        "stats": stats,
        "series": history_series,
        "alerts": alerts_log
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
