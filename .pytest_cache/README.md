# Personalized Hierarchical Federated Learning (HierFAVG) with Docker

Welcome to the implementation of a **Personalized Hierarchical Federated Learning (HierFAVG)** system using **Flask**, **MongoDB**, and **Docker**. This project models real-world federated learning pipelines with independent clients, hierarchical aggregation (client → edge → cloud), and personalized model updates.

---

## 🔍 Overview

This architecture simulates real-world distributed ML systems. It features:

* **Client Nodes (A, B, C, D)** with their own data and local models
* **Edge Nodes (1, 2)** that aggregate models from clients beneath them
* **Cloud Node** that aggregates models from edges and redistributes a global model
* **Personalization** at each client using a mixing parameter (default 0.2 global, 0.8 local)

```
Client A, B ➔ Edge 1
Client C, D ➔ Edge 2
         Edge 1 & 2 ➔ Cloud
```

---

## 🚀 Getting Started

### Prerequisites

* Docker & Docker Compose
* Python 3.10+ (for running tests locally)

### Clone & Build

```bash
git clone https://github.com/yourusername/hierarchical-fl.git
cd hierarchical-fl
docker-compose up --build
```

---

## 🌎 Accessing the UI

| Component | URL                                            |
| --------- | ---------------------------------------------- |
| Client A  | [http://localhost:5001](http://localhost:5001) |
| Client B  | [http://localhost:5003](http://localhost:5003) |
| Client C  | [http://localhost:5005](http://localhost:5005) |
| Client D  | [http://localhost:5007](http://localhost:5007) |
| Edge 1    | [http://localhost:5009](http://localhost:5009) |
| Edge 2    | [http://localhost:5011](http://localhost:5011) |
| Cloud     | [http://localhost:5013](http://localhost:5013) |

---

## 🎓 How It Works

1. **Clients** start with their baseline models.
2. Each client periodically sends their model to their assigned **Edge**.
3. **Edge nodes** average client models and send them to the **Cloud**.
4. **Cloud node** computes a global model and sends it back to all edges.
5. **Edge nodes** personalize the global model for each client using:

   ```
   personalized_model = 0.8 * local_model + 0.2 * global_model
   ```
6. Clients receive their updated personalized models and update their UI + DB.

---

## 💡 Features

*  Flask-based microservices for client, edge, cloud
*  Dockerized containers
*  MongoDB-based model persistence
*  Real-time dashboards using Plotly
*  Periodic automated model exchange
*  Configurable via environment variables
*  Pytest-powered unit testing for all components

---

## 📂 MongoDB Storage

Each client persists their models in MongoDB:

```
db: federated_db
collection: <client_name>_models
```

Mongo runs as a service in Docker and is used by all clients.

---

## 🛠️ Configuration

### Client ENV

```
CLIENT_NAME=client_a
CLIENT_PORT=5001
EDGE_HOST=edge1
EDGE_PORT=5009
MONGO_URI=mongodb://mongo:27017/
```

### Edge ENV

```
EDGE_NAME=edge1
EDGE_PORT=5009
CLOUD_HOST=cloud
CLOUD_PORT=5013
```

### Cloud ENV

```
CLOUD_NAME=cloud
CLOUD_PORT=5013
```

---

## 🔧 Testing

Run all tests with:

```bash
pytest
```

Each service has its own tests:

* `client/tests/`
* `edge/tests/`
* `cloud/tests/`

---

##  Future Enhancements

* ⭐ Differential privacy
* ⭐ TLS/HTTPS + Authentication
* ⭐ TensorFlow model integration
* ⭐ Kubernetes deployment

---

## 👤 Contributors

* Darpan Maurya

---

## 📄 License

This project is licensed under the **MIT License**.

---

## 🔗 References

* Ma et al., "ESPerHFL: Hierarchical FL with Personalization," *Journal of Cloud Computing*, 2024.
* Flower Framework (for FL inspiration)
* Docker, Flask, PyMongo, Pytest
