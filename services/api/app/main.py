from fastapi import FastAPI

from app import __version__
from app.api import auth, health, menu, pricing, profile
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version=__version__)
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(profile.router)
    app.include_router(menu.router)
    app.include_router(pricing.router)
    return app


app = create_app()
