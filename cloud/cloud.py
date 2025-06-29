from flask import Flask, request, jsonify, render_template_string
import os
import requests

app = Flask(__name__)

CLOUD_NAME = os.environ.get("CLOUD_NAME", "cloud")
CLOUD_PORT = int(os.environ.get("CLOUD_PORT", 9000))

EXPECTED_EDGES = ["edge1", "edge2"]
edge_models = {}
global_model = None
mixing_param = 0.2


# --------- Helper: Compute and Broadcast Global Model ---------
def compute_global_model():
    total_slope = sum(m['slope'] for m in edge_models.values())
    total_intercept = sum(m['intercept'] for m in edge_models.values())
    return {
        "slope": round(total_slope / len(edge_models), 4),
        "intercept": round(total_intercept / len(edge_models), 4)
    }


def send_global_model_to_edge(edge, model, mixing_param):
    try:
        edge_host = os.environ.get(f"{edge.upper()}_HOST", "localhost")
        edge_port = int(os.environ.get(f"{edge.upper()}_PORT", 8000))
        url = f"http://{edge_host}:{edge_port}/receive_global"
        print(f"[CLOUD] Sending global model to {edge} at {url}")
        res = requests.post(url, json={"model": model, "mixing_param": mixing_param})
        print(f"[CLOUD] Response from {edge}: {res.status_code}")
    except Exception as e:
        print(f"[CLOUD] Error sending to {edge}: {e}")


def broadcast_global_model():
    global global_model, edge_models
    global_model = compute_global_model()
    print(f"[CLOUD] Global model computed: {global_model}")

    for edge in EXPECTED_EDGES:
        send_global_model_to_edge(edge, global_model, mixing_param)

    # Reset edge models for next round
    edge_models = {}


# --------- Flask Routes ---------
@app.route('/receive_from_edge', methods=['POST'])
def receive_from_edge():
    data = request.json
    edge = data['edge']
    model = data['model']
    edge_models[edge] = model
    print(f"[CLOUD] Received model from {edge}: {model}")

    if len(edge_models) == len(EXPECTED_EDGES):
        print("[CLOUD] All edge models received. Computing global model.")
        broadcast_global_model()

    return jsonify({
        "status": "model received",
        "current_count": len(edge_models),
        "waiting_for": list(set(EXPECTED_EDGES) - set(edge_models))
    })


@app.route('/')
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Cloud Node</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
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
            h1, h2 {
                margin-top: 20px;
            }
            ul {
                background: rgba(0, 0, 0, 0.5);
                padding: 15px;
                border-radius: 10px;
                list-style: none;
            }
            li {
                margin-bottom: 10px;
            }
            p {
                background: rgba(0, 0, 0, 0.5);
                padding: 10px;
                border-radius: 8px;
                display: inline-block;
            }
        </style>
    </head>
    <body>
        <h1>Cloud Node</h1>

        {% if global_model %}
            <h2>Global Model: y = {{ global_model.slope }}x + {{ global_model.intercept }}</h2>
        {% else %}
            <p>Global model not computed yet.</p>
        {% endif %}

        <p>Mixing Parameter: {{ mixing_param }}</p>

        <div id="graph" style="width:100%; max-width:700px; height:400px;"></div>

        {% if global_model %}
        <script>
            let x = Array.from({length: 10}, (_, i) => i);
            let global_y = x.map(xi => {{ global_model.slope }} * xi + {{ global_model.intercept }});

            let data = [
                {
                    x: x,
                    y: global_y,
                    type: 'scatter',
                    mode: 'lines+markers',
                    name: 'Global Model',
                    line: {color: 'green'}
                }
            ];

            Plotly.newPlot('graph', data);
        </script>
        {% endif %}
    </body>
    </html>
    """, edge_models=edge_models, global_model=global_model, mixing_param=mixing_param)





if __name__ == '__main__':
    app.run(host='0.0.0.0', port=CLOUD_PORT)
