from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.seed.scenarios import SCENARIOS, load_scenario

router = APIRouter(prefix="/demo-scenarios", tags=["Demo Scenarios"])

@router.get("")
def list_demo_scenarios():
    return SCENARIOS

@router.post("/{scenario_id}/load")
def apply_demo_scenario(scenario_id: str, db: Session = Depends(get_db)):
    try:
        return load_scenario(db, scenario_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Could not load scenario: {exc}")
