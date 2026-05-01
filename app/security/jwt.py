import jwt
from jwt import PyJWTError

from app.core.config import settings

ALGORITHM = "HS256"


class InvalidTokenError(Exception):
    pass


class TokenPayload:
    def __init__(self, user_id: int, org_id: int, permissions: list[str]):
        self.user_id = user_id
        self.org_id = org_id
        self.permissions = permissions


def decode_token(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        org_id = payload.get("org_id")
        permissions = payload.get("permissions", [])
        token_type = payload.get("type")

        if not user_id or not org_id or token_type != "access":
            raise InvalidTokenError("Invalid token payload")

        return TokenPayload(user_id=user_id, org_id=org_id, permissions=permissions)
    except PyJWTError:
        raise InvalidTokenError("Invalid or expired token")
