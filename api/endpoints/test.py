from datetime import datetime
import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from psycopg2 import IntegrityError
from sqlalchemy import insert, update, delete
from api.models.jwt import JwtTokenData
from dependencies.jwt_token import get_token_data
from api.service.test import TestService, TestItemService
from dependencies.session import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.schemas import Test as TestSchema
from schemas.schemas import TestItem as TestItemSchema
from api.models.test import AddTestItem, PatchTestItem, UpdateTest
from api.models.env import env
from pathlib import Path


router = APIRouter(prefix="/test", tags=["Тест"])


@router.get("/paginated-list/")
async def get_paginated_list(
    max_per_page: int, page: int, session: AsyncSession = Depends(get_async_session)
):
    cur_service = TestService(session)
    data = await cur_service.paginated_list(
        max_per_page, page, TestSchema.published == True
    )
    pages = await cur_service.get_pages(max_per_page)
    return {"pages": pages, "data": data}


@router.get("/list/")
async def get_test_list(
    token: JwtTokenData = Depends(get_token_data),
    session: AsyncSession = Depends(get_async_session),
):
    service = TestService(session)
    return await service.list(TestSchema.user_id == token.sub)


@router.post("/")
async def add_test(
    image: UploadFile | None = File(default=None),
    title: str = Form(),
    description: str = Form(default=""),
    category: str = Form(),
    published: str = Form(),
    token: JwtTokenData = Depends(get_token_data),
    session: AsyncSession = Depends(get_async_session),
):
    if image:
        filename = f"{token.sub}_{datetime.now().timestamp()}_{image.filename}"
        file_path = os.path.join(Path(env.images_folder), filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
    service = TestService(session)
    published = (
        True
        if published.lower() == "true"
        else False
        if published.lower() == "false"
        else None
    )
    res = await service.add(
        {
            "user_id": token.sub,
            "title": title,
            "description": description,
            "category": category,
            "image": filename if image else "default.png",
            "published": published,
        }
    )
    await session.commit()
    await session.refresh(res)
    return res


@router.patch("/{test_id}/")
async def update_test(
    test_id: int,
    image: UploadFile | None = File(default=None),
    title: str | None = Form(default=None),
    description: str | None = Form(default=None),
    category: str | None = Form(default=None),
    published: str | None = Form(default=None),
    token: JwtTokenData = Depends(get_token_data),
    session: AsyncSession = Depends(get_async_session),
):
    service = TestService(session)
    published = (
        True
        if published and published.lower() == "true"
        else False
        if published and published.lower() == "false"
        else None
    )
    data = {
        "image": image.filename if image else None,
        "title": title,
        "description": description,
        "category": category,
        "published": published,
    }
    res = await service.patch(
        UpdateTest(**data).model_dump(exclude_none=True, exclude_unset=True), TestSchema.id == test_id, TestSchema.user_id == token.sub
    )
    await session.commit()
    await session.refresh(res)
    return res


@router.get("/{test_id}/items/")
async def get_test_items(
    test_id: int,
    token: JwtTokenData = Depends(get_token_data),
    session: AsyncSession = Depends(get_async_session),
):
    service = TestService(session)
    if not await service.get(TestSchema.id == test_id, TestSchema.user_id == token.sub):
        raise HTTPException(status_code=404, detail="Тест не найден")
    service = TestItemService(session)
    return await service.list(TestItemSchema.test_id == test_id)


@router.post("/{test_id}/items/")
async def add_test_items(
    test_id: int,
    data: dict[int, AddTestItem],
    token: JwtTokenData = Depends(get_token_data),
    session: AsyncSession = Depends(get_async_session),
):
    service = TestService(session)
    if not await service.get(TestSchema.id == test_id, TestSchema.user_id == token.sub):
        raise HTTPException(status_code=404, detail="Тест не найден")
    service = TestItemService(session)
    try:
        stmt = insert(TestItemSchema).values(
            [
                {
                    "test_id": test_id,
                    **v.model_dump(exclude_unset=True, exclude_none=True),
                }
                for k, v in data.items()
            ]
        )
        response = await session.execute(stmt)
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail=f"This {TestItemSchema.__name__} already exists",
        )
    await session.commit()
    return True


@router.patch("/{test_id}/items/")
async def patch_test_items(
    test_id: int,
    data: dict[int, PatchTestItem],
    token: JwtTokenData = Depends(get_token_data),
    session: AsyncSession = Depends(get_async_session),
):
    service = TestService(session)
    if not await service.get(TestSchema.id == test_id, TestSchema.user_id == token.sub):
        raise HTTPException(status_code=404, detail="Тест не найден")
    service = TestItemService(session)
    try:
        for k, v in data.items():
            stmt = (
                update(TestItemSchema)
                .where(TestItemSchema.id == k, TestItemSchema.test_id == test_id)
                .values({**v.model_dump(exclude_unset=True, exclude_none=True)})
            )
            await session.execute(stmt)
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail=f"This {TestItemSchema.__name__} already exists",
        )
    await session.commit()
    return True


@router.delete("/{test_id}/items/")
async def delete_test_items(
    test_id: int,
    data: list[int],
    token: JwtTokenData = Depends(get_token_data),
    session: AsyncSession = Depends(get_async_session),
):
    service = TestService(session)
    if not await service.get(TestSchema.id == test_id, TestSchema.user_id == token.sub):
        raise HTTPException(status_code=404, detail="Тест не найден")
    service = TestItemService(session)
    try:
        for i in data:
            stmt = delete(TestItemSchema).where(
                TestItemSchema.id == i, TestItemSchema.test_id == test_id
            )
            await session.execute(stmt)
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail=f"This {TestItemSchema.__name__} already exists",
        )
    await session.commit()
    return True


@router.get("/{test_id}/")
async def get_test(
    test_id: int,
    token: JwtTokenData = Depends(get_token_data),
    session: AsyncSession = Depends(get_async_session),
):
    service = TestService(session)
    return await service.get(
        service.schema.id == test_id, service.schema.user_id == token.sub
    )
