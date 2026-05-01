from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.logging_config import organization_id_ctx, user_id_ctx
from app.exceptions.custom_exceptions import UnauthorizedException
from app.security.jwt import InvalidTokenError, decode_token

security = HTTPBearer(auto_error=False)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials or not credentials.credentials:
        raise UnauthorizedException("Authorization header missing")

    if credentials.scheme.lower() != "bearer":
        raise UnauthorizedException("Invalid authentication scheme")

    try:
        current_user = decode_token(credentials.credentials)
        user_id_ctx.set(current_user.user_id)
        organization_id_ctx.set(current_user.org_id)
        return current_user
    except InvalidTokenError:
        raise UnauthorizedException("Invalid or expired token")
