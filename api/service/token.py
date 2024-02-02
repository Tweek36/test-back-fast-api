from sqlalchemy import select
from api.service import BaseService
from dependencies.jwt_token import create_jwt_token
from schemas.schemas import User

# class JwtService(NewBaseService):
#     async def _return(self):
#         return self.session.execute(select(User))