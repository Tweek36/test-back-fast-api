from fastapi.security import APIKeyCookie
from fastapi import Depends
from jwt import decode, encode
from api.models.env import env
from api.models.exceptions import MissingAuthHeaderError
from api.models.jwt import JwtTokenData
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies.session import get_async_session


cookie_scheme = APIKeyCookie(name="token")


async def get_token_data(authorization: str = Depends(cookie_scheme)):
    # Проверка наличия заголовка Authorization
    if not authorization:
        raise MissingAuthHeaderError

    # Декодирование токена
    payload = decode(
        authorization, env.secret_key, env.algorithm
    )
    payload["sub"] = int(payload["sub"])

    return JwtTokenData(**payload)


def create_jwt_token(data: dict, exp: int = env.exp_time_access) -> str:
    to_encode = data.copy()
    expiration_datetime = datetime.utcnow() + timedelta(minutes=exp)
    to_encode.update({"exp": expiration_datetime, "iat": datetime.utcnow()})
    encoded_jwt = encode(to_encode, env.secret_key, algorithm=env.algorithm)
    return encoded_jwt
