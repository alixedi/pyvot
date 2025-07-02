import pytest
from pathlib import Path
from starlette.testclient import TestClient
from pyvot.app import app, UPLOAD_DIR, SECRET_URL

client = TestClient(app)

@pytest.fixture(autouse=True, scope='function')
def cleanup_files():
    yield
    Path(UPLOAD_DIR / 'test.csv').unlink(missing_ok=True)


def test_home():
    response = client.get(f"/{SECRET_URL}")
    assert response.status_code == 200

def test_upload():
    client.post(f"/{SECRET_URL}", files={"file": ("test.csv", "col1,col2\n1,2\n3,4")})
    response = client.get("/test")
    assert response.status_code == 200
    assert "col1" in response.text
    assert "col2" in response.text
    assert "1" in response.text
    assert "2" in response.text
    assert "3" in response.text
    assert "4" in response.text

def test_pivot():
    client.post(f"/{SECRET_URL}", files={"file": ("test.csv", "col1,col2\n1,2\n3,4")})
    response = client.get("/test?row=col1&col=col2&val=col1&agg=count")
    assert response.status_code == 200
    assert "col1" in response.text
    assert "col2" in response.text
    assert "count" in response.text

def test_get_csv_non_existent():
    response = client.get("/nonexistent.csv")
    assert response.status_code == 404

def test_upload():
    response = client.post(f"/{SECRET_URL}", files={"file": ("test.csv", "col1,col2\n1,2\n3,4")})
    assert response.status_code == 200
    file_path = UPLOAD_DIR / 'test.parquet'
    assert file_path.exists()

def test_upload_nofile():
    response = client.post(f"/{SECRET_URL}")
    assert response.status_code == 400

def test_upload_emptyfile():
    response = client.post(f"/{SECRET_URL}", files={"file": ("test.csv", "")})
    assert response.status_code == 200
    assert 'File is empty.' in response.text

def test_upload_existing():
    response = client.post(f"/{SECRET_URL}", files={"file": ("test.csv", "col1,col2\n1,2\n3,4")})
    assert response.status_code == 200
    response = client.post(f"/{SECRET_URL}", files={"file": ("test.csv", "col1,col2\n1,2\n3,4")})
    assert response.status_code == 200
    assert 'File already exists.' in response.text
