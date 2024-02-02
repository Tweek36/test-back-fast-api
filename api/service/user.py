from fastapi import HTTPException
from sqlalchemy import insert, select
from api.models.exceptions import HTTPException404
from schemas.schemas import User
from api.service import BaseCRUDService
from api.models.user import UserSecurity, UserSecuritySchema
from dependencies.jwt_token import create_jwt_token
import bcrypt


class UserService(BaseCRUDService[User]):
    schema = User
    async def registrate(self, model: UserSecurity):
        try:
            stmt = insert(UserSecuritySchema).returning(UserSecuritySchema).values(**model.model_dump(exclude_unset=True))
            response = await self.session.execute(stmt)
            response = response.scalars().first()
        except Exception as e:
            raise HTTPException(400, str(e))
        await self.session.commit()
    
    async def login(self, user_id: int, password: str, salt: str = None, hashed_password: str = None, access_lvl: int = 1):
        if salt is None or hashed_password is None:
            user_securityschema = await self.session.execute(select(UserSecuritySchema).where(UserSecuritySchema.user_id == user_id))
            user_securityschema = user_securityschema.scalars().first()
            if user_securityschema is None:
                raise HTTPException404("User does not exist!")
            salt = user_securityschema.salt
            hashed_password = user_securityschema.password
        verifed = UserService.verify_password(password, salt, hashed_password)
        if not verifed:
            raise HTTPException(401, "Не правильный логин или пароль!")
        token = create_jwt_token({"sub": str(user_id), "access_lvl": access_lvl})
        return token
    
    def create_salt_and_hashed_password(password: str) -> dict:
        # Генерация соли с использованием bcrypt.gensalt()
        salt = bcrypt.gensalt(rounds=12)

        # Хеширование пароля с использованием bcrypt.hashpw()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)

        return {"salt": salt.decode('utf-8'), "hashed_password": hashed_password.decode('utf-8')}

    def verify_password(password: str, salt: str, hashed_password: str) -> bool:
        # Верификация пароля с использованием bcrypt.checkpw()
        hashed_input_password = bcrypt.hashpw(password.encode('utf-8'), salt.encode('utf-8'))

        # Сравнение хешированного ввода пароля с хешированным паролем
        return hashed_input_password == hashed_password.encode('utf-8')
    
    def validate_password(self, password: str):
        # проверка длины, сложности и т.д.
        return True
    
class UserSecurityService(BaseCRUDService[UserSecuritySchema]):
    schema = UserSecuritySchema