import os
import secrets
from fastapi import Header, HTTPException, status

_WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")


def verify_webhook_secret(x_webhook_secret: str | None = Header(default=None)) -> None:
    if not _WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="WEBHOOK_SECRET not configured on server",
        )
    if not x_webhook_secret or not secrets.compare_digest(x_webhook_secret, _WEBHOOK_SECRET):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing webhook secret",
        )
