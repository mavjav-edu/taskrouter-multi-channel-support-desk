import pytest
from app import create_app


@pytest.fixture
def client():
    return create_app().test_client()

def test_home(client):
    resp = client.get('/')
    assert resp.status_code == 200
    assert isinstance(resp.json, dict)
    assert resp.json.get('message', 'Hello Flask')

def test_home_bad_http_method(client):
    resp = client.post('/')
    assert resp.status_code == 405