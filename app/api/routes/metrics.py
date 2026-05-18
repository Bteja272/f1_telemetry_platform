from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.services.metrics_service import MetricsService

router = APIRouter(prefix="/metrics", tags=["Metrics"])
metrics_service = MetricsService()


@router.get("/system")
def get_system_metrics(db: Session = Depends(get_db)):
    return metrics_service.get_system_metrics(db)