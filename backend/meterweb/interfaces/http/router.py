from fastapi import APIRouter

from meterweb.interfaces.http.api.v1.router import router as api_v1_router
from meterweb.interfaces.http.web.router import router as web_router

router = APIRouter()
router.include_router(web_router)
router.include_router(api_v1_router)
