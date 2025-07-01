import pytest
from unittest.mock import patch, MagicMock
from client.client import app, BASELINE_MODEL

@pytest.fixture
def client():
    app.config['TESTING'] = True
    return app.test_client()

def test_init(client):
    res = client.get('/init')
    assert res.status_code == 200
    data = res.get_json()
    assert 'client' in data
    assert 'baseline_model' in data
    assert isinstance(data['baseline_model'], dict)

@patch("client.client.requests.post")
def test_send_to_edge(mock_post, client):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"status": "model received"}

    res = client.post('/send_to_edge')
    assert res.status_code == 200
    data = res.get_json()
    assert data['status'] == 'sent'
    assert 'response' in data

@patch("client.client.get_model_collection")
def test_receive_personalized(mock_get_model_collection, client):
    mock_model_collection = MagicMock()
    mock_model_collection.insert_one = MagicMock()
    mock_get_model_collection.return_value = mock_model_collection

    test_model = {"model": {"slope": 1.5, "intercept": 3.2}}
    res = client.post('/receive_personalized', json=test_model)
    assert res.status_code == 200
    data = res.get_json()
    assert data['status'] == 'received'
    mock_model_collection.insert_one.assert_called_once()

@patch("client.client.get_model_collection")
def test_receive_personalized_same_model_skips_insert(mock_get_model_collection, client):
    # First insert model
    mock_model_collection = MagicMock()
    mock_get_model_collection.return_value = mock_model_collection

    model_data = {"model": {"slope": 1.2, "intercept": 4.0}}
    client.post('/receive_personalized', json=model_data)

    # Try to send same model again
    res = client.post('/receive_personalized', json=model_data)
    assert res.status_code == 200
    assert 'status' in res.get_json()
    # Should only insert once even after 2 calls
    assert mock_model_collection.insert_one.call_count == 1

def test_update(client):
    res = client.post('/update', data={'slope': '3.14', 'intercept': '2.71'}, follow_redirects=True)
    assert res.status_code == 200
    assert BASELINE_MODEL['slope'] == 3.14
    assert BASELINE_MODEL['intercept'] == 2.71

def test_index_page(client):
    res = client.get('/')
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Baseline Model" in html
    assert str(BASELINE_MODEL['slope']) in html
    assert str(BASELINE_MODEL['intercept']) in html

