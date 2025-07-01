# client/app.py
from flask import Flask, request, jsonify, render_template_string,redirect,url_for
import os
import requests
import threading
import time
from pymongo import MongoClient

app = Flask(__name__)

CLIENT_NAME = os.environ.get("CLIENT_NAME", "client_x")
CLIENT_PORT = int(os.environ.get("CLIENT_PORT", 5001))
EDGE_HOST = os.environ.get("EDGE_HOST", "edge")
EDGE_PORT = int(os.environ.get("EDGE_PORT", 8000))
EDGE_URL = f"http://{EDGE_HOST}:{EDGE_PORT}"


# Add this function at the top
def get_model_collection():
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://mongo:27017/")
    client_name = os.environ.get("CLIENT_NAME", "client_x")
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client["federated_db"]
    return db[f"{client_name}_models"]


try:
    model_collection = get_model_collection()
    last_model_doc = model_collection.find_one(sort=[("timestamp", -1)])
except Exception as e:
    print(f"MongoDB not available: {e}")
    model_collection = None
    last_model_doc = None

if last_model_doc:
    BASELINE_MODEL = {
        "slope": last_model_doc["model"]["slope"],
        "intercept": last_model_doc["model"]["intercept"]
    }
else:
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
    new_model = data.get("model", {})

    if personalized_model != new_model:
        print(f"[{CLIENT_NAME}]  New personalized model received: {new_model}")
        personalized_model = new_model

        try:
            collection = get_model_collection() 
            collection.insert_one({
                "timestamp": time.time(),
                "model": personalized_model
            })
        except Exception as e:
            print(f"[{CLIENT_NAME}] MongoDB insert failed: {e}")
    else:
        print(f"[{CLIENT_NAME}]  Received personalized model: {personalized_model}")

    return jsonify({"status": "received", "personalized_model": personalized_model})


@app.route('/update', methods=['POST'])
def update():
    slope = float(request.form['slope'])
    intercept = float(request.form['intercept'])
    BASELINE_MODEL['slope'] = slope
    BASELINE_MODEL['intercept'] = intercept
    return redirect(url_for('index'))

@app.route('/')
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{{client_name}}</title>
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
                margin: 0;
                padding: 0;
            }
            .container {
                display: flex;
                flex-direction: row;
                justify-content: space-between;
                padding: 20px;
            }
            .left, .right {
                width: 48%;
            }
            .left {
                background: rgba(0, 0, 0, 0.5);
                padding: 20px;
                border-radius: 10px;
            }
            .right {
                background: rgba(0, 0, 0, 0.4);
                padding: 20px;
                border-radius: 10px;
            }
            input[type="text"], input[type="submit"] {
                margin: 10px 0;
                padding: 5px;
                width: 100%;
                border-radius: 5px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <!-- LEFT HALF: Model Info and Graph -->
            <div class="left">
                <h1>{{client_name}}</h1>
                <h2>Baseline Model: y = {{baseline.slope}}x + {{baseline.intercept}}</h2>
                {% if personalized.slope is not none %}
                    <h2>Personalized Model: y = {{personalized.slope}}x + {{personalized.intercept}}</h2>
                {% else %}
                    <h2>Personalized Model: Not received yet</h2>
                {% endif %}

                <div id="graph" style="width:100%; height:400px;"></div>

                <script>
                    let x = Array.from({length: 10}, (_, i) => i);
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
            </div>

            <!-- RIGHT HALF: Parameter Change Form -->
            <div class="right">
                <h2>Update Baseline Model Parameters</h2>
                <form method="POST" action="/update">
                    <label for="slope">Slope:</label>
                    <input type="text" id="slope" name="slope" placeholder="Enter new slope" required>

                    <label for="intercept">Intercept:</label>
                    <input type="text" id="intercept" name="intercept" placeholder="Enter new intercept" required>

                    <input type="submit" value="Update Model">
                </form>
            </div>
        </div>
    </body>
    </html>
    """, client_name=CLIENT_NAME, baseline=BASELINE_MODEL, personalized=personalized_model)

def send_model_on_startup():
    time.sleep(2)
    try:
        print(f"[{CLIENT_NAME}]  Sending baseline model to edge...")
        res = requests.post(f"{EDGE_URL}/receive_from_client", json={
            "client": CLIENT_NAME,
            "model": BASELINE_MODEL
        })
        print(f"[{CLIENT_NAME}]  Sent model. Edge responded: {res.status_code}")
    except Exception as e:
        print(f"[{CLIENT_NAME}]  Startup send failed: {e}")
        
def auto_send_periodically():
    while True:
        try:
            send_model_on_startup()  # Your actual logic
        except Exception as e:
            print(f"Error in send_model_on_startup{e}")
        time.sleep(80)  # 80 sec interval between calls

if __name__ == '__main__':
    threading.Thread(target=auto_send_periodically,daemon=True).start()
    app.run(host='0.0.0.0', port=CLIENT_PORT)
