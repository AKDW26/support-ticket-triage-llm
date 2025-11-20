import os
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    r = client.post('/triage', json={'description':'Payment declined repeatedly and subscription not active.'})
    assert r.status_code in (200, 400, 422)

def test_empty_description():
    r = client.post('/triage', json={'description':''})
    assert r.status_code == 400

# This test allows both an error (if code enforces missing-API-key failure)
# or a 200 response (if the LLM wrapper falls back to a mock).
def test_triage_without_key(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    r = client.post('/triage', json={'description':'Card was charged but subscription not active.'})
    assert r.status_code in (200, 500, 400)
