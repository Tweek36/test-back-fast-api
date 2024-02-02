from pydantic import BaseModel
from dependencies.sqlalchemy_to_pydantic import sqlalchemy_to_pydantic
from schemas.schemas import User as UserSchema
from schemas.schemas import UserSecurity as UserSecuritySchema


class UserSecurity(sqlalchemy_to_pydantic(UserSecuritySchema)):
    ...

class User(sqlalchemy_to_pydantic(UserSchema)):
    ...

class LoginUser(BaseModel):
    username: str
    password: str

class RegisterUser(LoginUser):
    repeat_password: str
    email: str

class UserLoginResponse(BaseModel):
    username: str
    id: int