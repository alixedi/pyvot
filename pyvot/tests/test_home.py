from starlette.testclient import TestClient
from pyvot.app import app

client = TestClient(app)

def test_home():
    response = client.get("/")
    assert response.status_code == 200
