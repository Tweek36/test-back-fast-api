from fastapi import APIRouter, Depends
# from api.service.token import JwtService
from dependencies.session import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(prefix="/search", tags=["Поиск"])

# @router.get("/")
# async def search(query: str, session: AsyncSession = Depends(get_async_session), service: JwtService = Depends()):
#     service = await JwtService()
#     return service._return()