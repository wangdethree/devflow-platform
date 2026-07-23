"""密码哈希与 JWT Access/Refresh Token 工具。"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from uuid import uuid4

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


@dataclass(frozen=True)
class TokenClaims:
    """经过签名与类型校验的令牌身份信息。"""

    user_id: int
    session_id: str
    token_id: str | None = None


def create_access_token(user_id: int, session_id: str) -> str:
    """为指定用户签发短期 JWT Access Token。"""

    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        "type": "access",
        "sid": session_id,
        "jti": str(uuid4()),
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(user_id: int, session_id: str) -> str:
    """签发可轮换的长期 Refresh Token。"""

    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "sid": session_id,
        "jti": str(uuid4()),
        "iat": now,
        "exp": now + timedelta(days=settings.refresh_token_expire_days),
        "type": "refresh",
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def _decode_token(token: str, expected_type: str) -> TokenClaims:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("type") != expected_type:
            raise AuthenticationError("令牌类型无效")
        token_id = payload.get("jti")
        if expected_type == "refresh" and not token_id:
            raise AuthenticationError("Refresh Token 缺少唯一标识")
        return TokenClaims(
            user_id=int(payload["sub"]),
            session_id=str(payload["sid"]),
            token_id=str(token_id) if token_id else None,
        )
    except (InvalidTokenError, KeyError, TypeError, ValueError) as exc:
        raise AuthenticationError("令牌无效或已过期") from exc


def decode_access_token(token: str) -> TokenClaims:
    """解析 Access Token。"""

    return _decode_token(token, "access")


def decode_refresh_token(token: str) -> TokenClaims:
    """解析 Refresh Token。"""

    return _decode_token(token, "refresh")


def hash_token(token: str) -> str:
    """仅持久化令牌摘要，避免数据库泄露时暴露原始 Refresh Token。"""

    return sha256(token.encode("utf-8")).hexdigest()
