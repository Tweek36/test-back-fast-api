from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from api.models.env import env
from api.service.user import UserService
from dependencies.session import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from api.models.user import LoginUser, UserSecurity, UserSchema, RegisterUser

router = APIRouter(prefix="/user", tags=["Пользователи"])


@router.post("/register/")
async def register_user(
    data: RegisterUser,
    session: AsyncSession = Depends(get_async_session)
):
    if data.password != data.repeat_password:
        raise HTTPException(status_code=412, detail="Пароли не совпадают")
    hashed_data = UserService.create_salt_and_hashed_password(data.password)
    salt = hashed_data["salt"]
    hashed_password = hashed_data["hashed_password"]
    service = UserService(session)
    user_data = {**data.model_dump(exclude_unset=True)}
    del user_data["password"]
    del user_data["repeat_password"]
    user_data["access_lvl"] = 1
    user = await service.add(user_data)
    await session.commit()
    await session.refresh(user)
    await service.registrate(UserSecurity(user_id=user.id, 
                                          password=hashed_password,
                                          salt=salt
                                         ))
    await session.commit()
    await session.refresh(user)
    token = await service.login(user.id, data.password, salt=salt, hashed_password=hashed_password)
    response = JSONResponse({"id": user.id, "username": user.username})
    response.set_cookie("token", token, httponly=True, secure=True, max_age=env.exp_time_access, samesite="strict")
    return response

@router.post("/login/")
async def login_user(
    data: LoginUser,
    session: AsyncSession = Depends(get_async_session)
):
    service = UserService(session)
    try:
        user = await service.get(UserSchema.username==data.username)
        if not user:
            response = JSONResponse(status_code=404, content={"detail": "User does not exist!"})
            response.delete_cookie("token", httponly=True, secure=True, samesite="strict")
            return response
        token = await service.login(user.id, data.password)
    except HTTPException as e:
        response = JSONResponse(status_code=e.status_code, content={"detail": e.detail})
        response.delete_cookie("token", httponly=True, secure=True, samesite="strict")
        return response
    response = JSONResponse({"id": user.id, "username": user.username})
    response.set_cookie("token", token, httponly=True, secure=True, max_age=env.exp_time_access, samesite="strict")
    return response

@router.post("/logout/")
async def logout_user(
    session: AsyncSession = Depends(get_async_session),
    # token: JwtTokenData = Depends(get_token_data)
):
    response = HTMLResponse(status_code=200)
    response.delete_cookie("token", httponly=True, secure=True, samesite="strict")
    return response