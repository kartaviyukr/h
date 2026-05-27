from fastapi import FastAPI

from app import __version__
from app.api import health
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version=__version__)
    app.include_router(health.router)
    return app


app = create_app()
