from app.api.inventory import router as inventory_router
from app.api.stores import router as stores_router
from app.api.analysis import router as analysis_router
from app.api.recommendations import router as recommendations_router
from app.api.approvals import router as approvals_router
from app.api.analytics import router as analytics_router

__all__ = [
    "inventory_router",
    "stores_router",
    "analysis_router",
    "recommendations_router",
    "approvals_router",
    "analytics_router",
]
