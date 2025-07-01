import pytest
from cloud.cloud import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    return app.test_client()


def test_receive_from_edge_success(client):
    # Valid payload
    data = {"edge": "edge1", "model": {"slope": 3.0, "intercept": 1.0}}
    res = client.post('/receive_from_edge', json=data)
    assert res.status_code == 200
    json_data = res.get_json()
    assert 'status' in json_data
    assert json_data['status'] == 'model received'
    assert json_data['current_count'] >= 1


def test_receive_from_edge_missing_model(client):
    # Missing 'model' key
    data = {"edge": "edge1"}
    res = client.post('/receive_from_edge', json=data)
    assert res.status_code == 400
    assert res.get_json()['error'] == 'Invalid payload'


def test_receive_from_edge_missing_edge(client):
    # Missing 'edge' key
    data = {"model": {"slope": 1.0, "intercept": 2.0}}
    res = client.post('/receive_from_edge', json=data)
    assert res.status_code == 400
    assert res.get_json()['error'] == 'Invalid payload'


def test_receive_from_edge_empty_payload(client):
    # Empty request body
    res = client.post('/receive_from_edge', json={})
    assert res.status_code == 400
    assert res.get_json()['error'] == 'Invalid payload'


def test_receive_from_edge_wrong_type(client):
    # Send string instead of dict
    res = client.post('/receive_from_edge', data="not json", content_type='application/json')
    assert res.status_code == 400
    assert res.get_json()['error'] == 'Invalid payload'
