"""
Health Route — GET /health
"""

from fastapi import APIRouter
from app.schemas import HealthResponse
from app.ml import models_loaded, get_dataset
from app.database import get_connection

router = APIRouter(tags=["System"])


@router.get("/health", response_model=HealthResponse)
def health_check():
    """Check system health: models, dataset, database."""
    db_ok = False
    try:
        conn = get_connection()
        conn.execute("SELECT 1")
        conn.close()
        db_ok = True
    except Exception:
        pass

    dataset_rows = 0
    try:
        dataset_rows = len(get_dataset())
    except Exception:
        pass

    return HealthResponse(
        status="healthy" if models_loaded() and db_ok else "degraded",
        models_loaded=models_loaded(),
        dataset_rows=dataset_rows,
        db_connected=db_ok,
    )
