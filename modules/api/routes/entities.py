from fastapi import APIRouter, HTTPException
from modules.persistence.local_storage import LocalStorage

router = APIRouter()
storage = LocalStorage()

@router.get("/entity/{entity_id}")
def get_entity(entity_id: str):
    records = storage.get_records_by_entity(entity_id)

    if not records:
        raise HTTPException(status_code=404, detail="Entity not found")

    return {
        "entity_id": entity_id,
        "records": records
    }