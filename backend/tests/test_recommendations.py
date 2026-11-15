import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.batch import Batch
from app.seed.demo_data import seed_database

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_db():
    seed_database()

def test_recommendation_and_approval_workflow():
    # 1. Fetch recommendations
    res = client.get("/recommend")
    assert res.status_code == 200
    recs = res.json()
    assert len(recs) > 0

    transfer_rec = [r for r in recs if r["action_type"] == "TRANSFER" and "Milk Powder" in r["product_name"]][0]
    rec_id = transfer_rec["id"]

    # Check unapproved complete is rejected
    fail_comp = client.post("/complete", json={"recommendation_id": rec_id})
    assert fail_comp.status_code == 400

    # 2. Approve recommendation
    approve_res = client.post("/approve", json={"recommendation_id": rec_id, "approved_by": "Regional Manager"})
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "APPROVED"

    # Check source inventory before transfer
    db = SessionLocal()
    batch_before = db.query(Batch).filter(Batch.id == transfer_rec["batch_id"]).first()
    qty_before = batch_before.quantity
    db.close()

    # 3. Complete transfer
    comp_res = client.post("/complete", json={"recommendation_id": rec_id})
    assert comp_res.status_code == 200
    assert comp_res.json()["execution_status"] == "COMPLETED"

    # Verify inventory was decreased at source
    db = SessionLocal()
    batch_after = db.query(Batch).filter(Batch.id == transfer_rec["batch_id"]).first()
    assert batch_after.quantity == qty_before - transfer_rec["recommended_quantity"]

    # Verify duplicate completion is rejected
    dup_res = client.post("/complete", json={"recommendation_id": rec_id})
    assert dup_res.status_code == 400
    assert "Duplicate" in dup_res.json()["detail"] or "already" in dup_res.json()["detail"]
    db.close()
