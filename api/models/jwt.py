from pydantic import BaseModel


class JwtTokenData(BaseModel):
    exp: int
    iat: int
    sub: int
    access_lvl: int