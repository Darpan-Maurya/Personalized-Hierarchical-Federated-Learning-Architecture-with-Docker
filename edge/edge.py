from flask import Flask, request, jsonify, render_template_string
import os
import requests
import threading
import time

app = Flask(__name__)

EDGE_NAME = os.environ.get("EDGE_NAME", "edge_x")
EDGE_PORT = int(os.environ.get("EDGE_PORT", 8000))
CLOUD_HOST = os.environ.get("CLOUD_HOST", "cloud")
CLOUD_PORT = int(os.environ.get("CLOUD_PORT", 9000))
CLOUD_URL = f"http://{CLOUD_HOST}:{CLOUD_PORT}"

# Mapping of client display names to their Docker hostnames and ports
CLIENT_PORT_MAP = {
    "Client A": ("client_a", 5001),
    "Client B": ("client_b", 5003),
    "Client C": ("client_c", 5005),
    "Client D": ("client_d", 5007),
}

client_models = {}
local_model = None
global_model = None
personalized_models = {}
mixing_param = 0.2  # Can be overwritten by cloud


@app.route('/receive_from_client', methods=['POST'])
def receive_from_client():
    data = request.json
    client = data.get('client')
    model = data.get('model')
    if not client or not model:
        return jsonify({"error": "Missing client or model"}), 400

    client_models[client] = model
    print(f"[{EDGE_NAME}]  Received model from {client}: {model}")
    return jsonify({"status": "model received"})


@app.route('/send_to_cloud', methods=['POST'])
def send_to_cloud():
    return aggregate_and_send_to_cloud()


def aggregate_and_send_to_cloud():
    global local_model
    if not client_models:
        return jsonify({"error": "No client models to aggregate"}), 400

    total_slope = sum(m.get('slope', 0) for m in client_models.values())
    total_intercept = sum(m.get('intercept', 0) for m in client_models.values())
    count = len(client_models)

    local_model = {
        "slope": round(total_slope / count, 4),
        "intercept": round(total_intercept / count, 4)
    }

    print(f"[{EDGE_NAME}]  Sending local model to cloud: {local_model}")
    try:
        res = requests.post(f"{CLOUD_URL}/receive_from_edge", json={
            "edge": EDGE_NAME,
            "model": local_model
        })
        print(f"[{EDGE_NAME}]  Cloud responded: {res.json()}")
        return jsonify({"status": "sent", "cloud_response": res.json()})
    except Exception as e:
        print(f"[{EDGE_NAME}]  Failed to send to cloud: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/receive_global', methods=['POST'])
def receive_global():
    global global_model, personalized_models
    data = request.json
    global_model = data.get("model")
    mixing = data.get("mixing_param", mixing_param)

    if not global_model:
        return jsonify({"error": "Missing global model"}), 400

    print(f"[{EDGE_NAME}]  Received global model: {global_model} with mixing {mixing}")

    if not local_model:
        return jsonify({"error": "Local model not available"}), 400

    # Mix global and local model for all clients
    slope = round((1 - mixing) * local_model.get("slope", 0) + mixing * global_model.get("slope", 0), 4)
    intercept = round((1 - mixing) * local_model.get("intercept", 0) + mixing * global_model.get("intercept", 0), 4)
    shared_model = {"slope": slope, "intercept": intercept}

    personalized_models = {}
    for client_name in client_models.keys():
        personalized_models[client_name] = shared_model
        try:
            host, port = CLIENT_PORT_MAP.get(client_name, (None, None))
            if not host or not port:
                print(f"[{EDGE_NAME}]  No mapping for client {client_name}")
                continue
            client_url = f"http://{host}:{port}/receive_personalized"
            res = requests.post(client_url, json={"model": shared_model})
            print(f"[{EDGE_NAME}]  Sent personalized model to {client_name} ({host}:{port}): {res.status_code}")
        except Exception as e:
            print(f"[{EDGE_NAME}]  Failed to send to {client_name}: {e}")

    return jsonify({
        "status": "global received",
        "shared_personalized_model": shared_model
    })


@app.route('/')
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{{ edge_name }}</title>
        <style>
            body {
                background-image: url('/static/background.png');
                background-size: cover;
                background-repeat: no-repeat;
                background-attachment: fixed;
                font-family: Arial, sans-serif;
                color: white;
                text-shadow: 1px 1px 3px black;
                padding: 20px;
            }

            h1, h2, h3 {
                margin-top: 20px;
            }

            ul {
                background: rgba(0, 0, 0, 0.5);
                padding: 15px;
                border-radius: 10px;
                list-style-type: none;
            }

            li {
                margin-bottom: 10px;
            }

            p, h2, h3 {
                background: rgba(0, 0, 0, 0.5);
                padding: 10px;
                border-radius: 8px;
                display: inline-block;
            }
        </style>
    </head>
    <body>
        <h1>📡 {{ edge_name }}</h1>
        <h2>🔧 Mixing Parameter: {{ mixing }}</h2>

        {% if local_model %}
            <h3>📈 Local Aggregated Model: y = {{local_model.slope}}x + {{local_model.intercept}}</h3>
        {% else %}
            <h3>📉 No local model yet.</h3>
        {% endif %}

        {% if global_model %}
            <h3>🌍 Global Model: y = {{global_model.slope}}x + {{global_model.intercept}}</h3>
        {% else %}
            <h3>🌐 No global model yet.</h3>
        {% endif %}

        {% if personalized_models %}
            <h3>🧬 Personalized Models:</h3>
            <ul>
            {% for client, model in personalized_models.items() %}
                <li>{{client}}: y = {{model.slope}}x + {{model.intercept}}</li>
            {% endfor %}
            </ul>
        {% else %}
            <h3>🚫 No personalized models yet.</h3>
        {% endif %}
    </body>
    </html>
    """, edge_name=EDGE_NAME, mixing=mixing_param, local_model=local_model, global_model=global_model, personalized_models=personalized_models)

def auto_send_to_cloud():
    time.sleep(4)
    if client_models:
        print(f"[{EDGE_NAME}] ⏳ Auto-aggregating client models")
        try:
            res = requests.post(f"http://localhost:{EDGE_PORT}/send_to_cloud")
            print(f"[{EDGE_NAME}] Aggregation result: {res.json()}")
        except Exception as e:
            print(f"[{EDGE_NAME}]  Auto-send failed: {e}")
    else:
        print(f"[{EDGE_NAME}]  No client models at startup.")

def auto_send_periodically():
    while True:
        try:
            auto_send_to_cloud()  # Your actual logic
        except Exception as e:
            print(f"Error in auto_send_to_cloud: {e}")
        time.sleep(80)  

if __name__ == '__main__':
    threading.Thread(target=auto_send_periodically,daemon=True).start()
    app.run(host='0.0.0.0', port=EDGE_PORT)
