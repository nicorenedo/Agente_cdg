from fastapi import FastAPI
from fastapi.testclient import TestClient

# App básica para testing
app = FastAPI()

@app.get("/")
def root():
    return {"status": "test_ok"}

@app.get("/health") 
def health():
    return {"status": "healthy"}

client = TestClient(app)

def test_basic_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "test_ok"

def test_basic_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
