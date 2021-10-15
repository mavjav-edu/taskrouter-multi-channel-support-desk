import pytest
from flask.testing import FlaskClient
from app import app


@pytest.fixture
def client():
    return app.test_client()


def test_home(client: FlaskClient):
    """should be a successful GET request"""
    resp = client.get('/')
    assert resp.status_code == 200
    assert isinstance(resp.json, dict)
    assert resp.json.get('message', 'Hello Flask')


def test_home_bad_http_method(client: FlaskClient):
    """should return a Method Not Allowed response"""
    resp = client.post('/')
    assert resp.status_code == 405