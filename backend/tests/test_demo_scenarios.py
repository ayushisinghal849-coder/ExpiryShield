from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_five_demo_scenarios_return_distinct_action_outcomes():
    expected = {
        "transfer-opportunity": "TRANSFER",
        "urgent-discount": "DISCOUNT",
        "fefo-rotation": "FEFO",
        "bundle-opportunity": "BUNDLE",
        "remote-store": "FEFO",
    }
    for scenario_id, action in expected.items():
        loaded = client.post(f"/demo-scenarios/{scenario_id}/load")
        assert loaded.status_code == 200
        assert loaded.json()["batches_loaded"] == 3
        analysis = client.post("/analyze")
        assert analysis.status_code == 200
        assert analysis.json()["total_batches"] == 3
        recommendations = client.get("/recommend")
        assert recommendations.status_code == 200
        assert recommendations.json()
        assert recommendations.json()[0]["action_type"] == action
