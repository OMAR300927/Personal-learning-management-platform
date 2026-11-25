from fastapi import APIRouter


router = APIRouter()


@router.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Return a lightweight response used to verify API availability."""
    return {"status": "ok"}
