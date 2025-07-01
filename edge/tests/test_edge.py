import pytest
from edge.edge import app

# Setup: reset global state before each test
def setup_function():
    import edge.edge as edge_module
    edge_module.client_models.clear()
    edge_module.personalized_models.clear()
    edge_module.local_model = None
    edge_module.global_model = None

@pytest.fixture
def client():
    app.config['TESTING'] = True
    return app.test_client()

def test_receive_from_client(client):
    data = {"client": "Client A", "model": {"slope": 2, "intercept": 5}}
    res = client.post('/receive_from_client', json=data)
    assert res.status_code == 200
    assert res.get_json()['status'] == 'model received'

def test_send_to_cloud_without_clients(client):
    res = client.post('/send_to_cloud')
    assert res.status_code == 400
    assert 'error' in res.get_json()

def test_send_to_cloud_with_clients(client):
    client.post('/receive_from_client', json={
        "client": "Client A",
        "model": {"slope": 3, "intercept": 7}
    })

    res = client.post('/send_to_cloud')
    assert res.status_code in [200, 500]  # 500 if cloud not running
    data = res.get_json()
    if res.status_code == 200:
        assert 'status' in data
    else:
        assert 'error' in data

def test_receive_global(client):
    # Send client model and trigger aggregation
    client.post('/receive_from_client', json={
        "client": "Client A",
        "model": {"slope": 2, "intercept": 5}
    })
    client.post('/send_to_cloud')  # Sets local_model

    # Send global model
    res = client.post('/receive_global', json={
        "model": {"slope": 2.5, "intercept": 4.5},
        "mixing_param": 0.2
    })

    assert res.status_code == 200
    data = res.get_json()
    assert data['status'] == 'global received'
    assert 'shared_personalized_model' in data
    model = data['shared_personalized_model']
    assert 'slope' in model
    assert 'intercept' in model

def test_receive_global_fails_without_local_model(client):
    import edge.edge as edge_module
    edge_module.local_model = None  # Properly unset local_model

    res = client.post('/receive_global', json={
        "model": {"slope": 2.5, "intercept": 4.5},
        "mixing_param": 0.2
    })

    assert res.status_code == 400
    data = res.get_json()
    assert 'error' in data
