# client/app.py
from flask import Flask, request, jsonify, render_template_string
import os
import requests
import threading
import time

app = Flask(__name__)

CLIENT_NAME = os.environ.get("CLIENT_NAME", "client_x")
CLIENT_PORT = int(os.environ.get("CLIENT_PORT", 5001))
EDGE_HOST = os.environ.get("EDGE_HOST", "edge")
EDGE_PORT = int(os.environ.get("EDGE_PORT", 8000))
EDGE_URL = f"http://{EDGE_HOST}:{EDGE_PORT}"

BASELINE_MODEL = {
    "slope": float(os.environ.get("BASELINE_SLOPE", 0)),
    "intercept": float(os.environ.get("BASELINE_INTERCEPT", 0))
}
personalized_model = {"slope": None, "intercept": None}

@app.route('/init', methods=['GET'])
def initialize():
    return jsonify({"client": CLIENT_NAME, "baseline_model": BASELINE_MODEL})

@app.route('/send_to_edge', methods=['POST'])
def send_to_edge():
    try:
        res = requests.post(f"{EDGE_URL}/receive_from_client", json={
            "client": CLIENT_NAME,
            "model": BASELINE_MODEL
        })
        return jsonify({"status": "sent", "response": res.json()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/receive_personalized', methods=['POST'])
def receive_personalized():
    global personalized_model
    data = request.json
    personalized_model = data.get("model", {})
    print(f"[{CLIENT_NAME}]  Received personalized model: {personalized_model}")
    return jsonify({"status": "received", "personalized_model": personalized_model})

@app.route('/')
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{{client_name}}</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body 
            {
                background-image: url('/static/background.png');
                background-size: cover;
                background-repeat: no-repeat;
                background-attachment: fixed;
                font-family: Arial, sans-serif;
                color: white;
                text-shadow: 1px 1px 3px black;
            }
            h1, h2, h3 
            {
            margin-top: 20px;
            }

            form 
            {
                background: rgba(0, 0, 0, 0.5);
                padding: 20px;
                border-radius: 10px;
                display: inline-block;
            }

            input[type="submit"] 
            {
                padding: 5px 10px;
            }
        </style>
    </head>
    <body>
        <h1>{{client_name}}</h1>
        <h2>Baseline Model: y = {{baseline.slope}}x + {{baseline.intercept}}</h2>
        {% if personalized.slope is not none %}
            <h2>Personalized Model: y = {{personalized.slope}}x + {{personalized.intercept}}</h2>
        {% else %}
            <h2>Personalized Model: Not received yet</h2>
        {% endif %}

        <div id="graph" style="width:100%; max-width:700px; height:400px;"></div>

        <script>
            let x = Array.from({length: 10}, (_, i) => i);  // x = [0,1,2,...,9]
            let baseline_y = x.map(xi => {{ baseline.slope }} * xi + {{ baseline.intercept }});

            {% if personalized.slope is not none %}
                let personalized_y = x.map(xi => {{ personalized.slope }} * xi + {{ personalized.intercept }});
            {% else %}
                let personalized_y = [];
            {% endif %}

            let data = [
                {
                    x: x,
                    y: baseline_y,
                    type: 'scatter',
                    mode: 'lines',
                    name: 'Baseline Model',
                    line: {color: 'blue'}
                },
                {
                    x: x,
                    y: personalized_y,
                    type: 'scatter',
                    mode: 'lines',
                    name: 'Personalized Model',
                    line: {color: 'red'}
                }
            ];

            Plotly.newPlot('graph', data);
        </script>
    </body>
    </html>
    """, client_name=CLIENT_NAME, baseline=BASELINE_MODEL, personalized=personalized_model)


def send_model_on_startup():
    time.sleep(2)
    while(1):
        try:
            print(f"[{CLIENT_NAME}]  Sending baseline model to edge...")
            res = requests.post(f"{EDGE_URL}/receive_from_client", json={
                "client": CLIENT_NAME,
                "model": BASELINE_MODEL
            })
            print(f"[{CLIENT_NAME}]  Sent model. Edge responded: {res.status_code}")
        except Exception as e:
            print(f"[{CLIENT_NAME}]  Startup send failed: {e}")

if __name__ == '__main__':
    threading.Thread(target=send_model_on_startup).start()
    app.run(host='0.0.0.0', port=CLIENT_PORT)
