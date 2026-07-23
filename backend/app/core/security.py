"""密码哈希与 JWT 访问令牌工具。"""

from datetime import UTC, datetime, timedelta

import jwt
from jwt import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import settings
from app.core.exceptions import AuthenticationError


password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """使用 Argon2 对密码进行不可逆哈希。"""

    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """校验明文密码是否匹配已保存哈希。"""

    return password_hash.verify(password, hashed_password)


def create_access_token(user_id: int) -> str:
    """为指定用户签发短期 JWT Access Token。"""

    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        "type": "access",
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> int:
    """解析访问令牌并返回用户主键。"""

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("type") != "access":
            raise AuthenticationError("无效的访问令牌")
        return int(payload["sub"])
    except (InvalidTokenError, KeyError, TypeError, ValueError) as exc:
        raise AuthenticationError("访问令牌无效或已过期") from exc
