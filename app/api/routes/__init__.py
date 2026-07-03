from fastapi import APIRouter

from app.api.routes import auth, dashboard, health, members, owners, public, sessions

router = APIRouter()
router.include_router(health.router)
router.include_router(auth.router)
router.include_router(dashboard.router)
router.include_router(sessions.router)
router.include_router(members.router)
router.include_router(owners.router)
router.include_router(public.router)
