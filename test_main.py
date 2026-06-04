from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_create_transaction():
    response = client.post("/transactions", json={
        "description": "AMAZON ORDER",
        "amount": 49.99
    })
    assert response.status_code == 201
    assert response.json()["category"] == "Shopping"
    assert response.json()["description"] == "AMAZON ORDER"

def test_create_transaction_empty_description():
    response = client.post("/transactions", json={
        "description": "",
        "amount": 49.99
    })
    assert response.status_code == 422

def test_create_transaction_negative_amount():
    response = client.post("/transactions", json={
        "description": "UBER TRIP",
        "amount": -10
    })
    assert response.status_code == 422

def test_get_transactions():
    response = client.get("/transactions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_transaction_not_found():
    response = client.get("/transactions/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Transaction not found"

def test_delete_transaction_not_found():
    response = client.delete("/transactions/99999")
    assert response.status_code == 404