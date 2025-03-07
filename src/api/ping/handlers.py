from fastapi import APIRouter, Request

router = APIRouter()


def validate_link(link: str) -> None:
    pass


@router.get("/ping", response_model=None)
async def ping_handler(
    _: Request,
) -> dict[str, str]:
    return {"pong": "ok"}
