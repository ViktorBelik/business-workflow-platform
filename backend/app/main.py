from fastapi import FastAPI

from backend.app.api.health import router as health_router
from backend.app.core.config import settings

app = FastAPI(
    title=settings.app_name,
)

app.include_router(health_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": settings.app_name}
