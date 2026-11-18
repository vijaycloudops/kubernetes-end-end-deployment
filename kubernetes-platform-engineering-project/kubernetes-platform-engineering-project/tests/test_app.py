from app.app import app

def test_home_returns_application_message():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert response.json["application"] == "platform-demo"

def test_health_endpoint():
    client = app.test_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["status"] == "healthy"

def test_ready_endpoint():
    client = app.test_client()
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json["status"] == "ready"
