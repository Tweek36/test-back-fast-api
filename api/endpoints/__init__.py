from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies.jwt_token import get_token_data
from dependencies.session import get_async_session
from api.service import BaseCRUDService
from api.models.exceptions import HTTPException404


# def add_crud(service: BaseCRUDService, router: APIRouter, exclude: set = None, include: set = None, dependencies: list[Depends] = []):

#     if exclude is None:
#         exclude = set()

#     if include is None:
#         include = set()
    
#     if "list" not in exclude and ("list" in include or len(include) == 0):
#         @router.get("/list/", response_model=service.Config.list_responce_model, dependencies=dependencies)
#         async def list(
#             session: AsyncSession = Depends(get_async_session)
#         ):
#             return await service(session).list()
    
#     if "paginated-list" not in exclude and ("paginated-list" in include or len(include) == 0):
#         @router.get("/paginated-list/", response_model=service.Config.paginated_list_responce_model, dependencies=dependencies)
#         async def get_paginated_list(
#             max_per_page: int,
#             page: int,
#             session: AsyncSession = Depends(get_async_session)
#         ):
#             cur_service = service(session)
#             data = await cur_service.paginated_list(max_per_page, page)
#             pages = await cur_service.get_pages(max_per_page)
#             return {"pages": pages, "data": data}
    
#     if "add" not in exclude and ("add" in include or len(include) == 0):
#         @router.post("/", response_model=service.Config.add_responce_model, dependencies=dependencies)
#         async def add(
#             model: service.Config.add_model, 
#             session: AsyncSession = Depends(get_async_session)
#         ):
#             value = await service(session).add(model)
#             return value

#     if "get" not in exclude and ("get" in include or len(include) == 0):
#         @router.get("/{id}/", response_model=service.Config.get_responce_model, dependencies=dependencies)
#         async def get(
#             id: int, 
#             session: AsyncSession = Depends(get_async_session)
#         ):
#             value = await service(session).get(service.Config.model.id == id)
#             if value is None:
#                 raise HTTPException404(f"{service.Config.model.__name__} with id={id} not found")
#             return value
    
#     if "patch" not in exclude and ("patch" in include or len(include) == 0):
#         @router.patch("/{id}/", response_model=service.Config.patch_responce_model, dependencies=dependencies)
#         async def patch(
#             id: int,
#             model: service.Config.patch_model, 
#             session: AsyncSession = Depends(get_async_session)
#         ):
#             value = await service(session).patch(model, service.Config.model.id == id)
#             return value
    
#     if "delete" not in exclude and ("delete" in include or len(include) == 0):
#         @router.delete("/{id}/", response_model=service.Config.delete_responce_model, dependencies=dependencies)
#         async def delete(
#             id: int,
#             session: AsyncSession = Depends(get_async_session)
#         ):
#             value = await service(session).delete(service.Config.model.id == id)
#             if value is None:
#                 raise HTTPException404(f"{service.Config.model.__name__} with id={id} not found")
#             return value
#         return router