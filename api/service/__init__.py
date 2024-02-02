from math import ceil
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, insert, update, delete
from schemas import Base
from sqlalchemy.sql._typing import _ColumnExpressionArgument
from sqlalchemy.exc import IntegrityError
from typing import List, Type, Generic, TypeVar, Sequence, Union, overload


T = TypeVar("T", bound=Base)

class BaseService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

class BaseCRUDService(BaseService, Generic[T]):
    schema: Type[T]

    def __init_subclass__(cls) -> None:
        cls.schema = cls.__orig_bases__[0].__args__[0]
        if cls.schema is None:
            raise ValueError("Добавьте схему!")
        if not issubclass(cls.schema, Base):
            raise ValueError("Схема должна быть подклассом Base!")
        
        return super().__init_subclass__()

    async def get(self, *args: _ColumnExpressionArgument[bool]):
        stmt = select(self.schema).where(*args)
        response = await self.session.execute(stmt)
        response = response.scalars().first()
        return response
    
    @overload
    async def add(self, values: dict) -> T: ...

    @overload
    async def add(self, values: List[dict]) -> Sequence[T]: ...

    @overload
    async def add(self, values: Union[dict, List[dict]]) -> Union[T, Sequence[T]]: ...

    async def add(self, values: Union[dict, List[dict]]) -> Union[T, Sequence[T]]:
        try:
            stmt = (
                insert(self.schema).returning(self.schema).values(values)
            )
            response = await self.session.execute(stmt)
            if isinstance(values, list):
                response = response.scalars().all()
            else:
                response = response.scalars().first()
        except IntegrityError as e:
            print(e)
            raise HTTPException(
                status_code=409,
                detail=f"This {self.schema.__name__} already exists",
            )
        return response

    async def patch(self, values: dict, *args: _ColumnExpressionArgument[bool]):
        stmt = (
            update(self.schema)
            .returning(self.schema)
            .where(*args)
            .values(values)
        )
        response = await self.session.execute(stmt)
        response = response.scalars().first()
        return response

    async def delete(self, *args: _ColumnExpressionArgument[bool]):
        stmt = delete(self.schema).returning(self.schema).where(*args)
        response = await self.session.execute(stmt)
        response = response.scalars().first()
        return response

    async def list(self, *args: _ColumnExpressionArgument[bool]):
        stmt = select(self.schema).where(*args)
        response = await self.session.execute(stmt)
        response = response.scalars().all()
        return response

    async def paginated_list(
        self, max_per_page: int, page: int, *args: _ColumnExpressionArgument[bool]
    ):
        stmt = select(self.schema).where(*args)
        offset = (page - 1) * max_per_page
        stmt = stmt.limit(max_per_page).offset(offset)
        response = await self.session.execute(stmt)
        response = response.scalars().all()
        return response

    async def get_pages(
        self, max_per_page: int, *args: _ColumnExpressionArgument[bool]
    ):
        stmt = (
            select(func.count().label("total_count"))
            .select_from(self.schema)
            .where(*args)
        )
        total_count = await self.session.execute(stmt)
        total_count = total_count.scalar()
        if total_count is None:
            return 1
        page_count = ceil(total_count / max_per_page)
        return page_count
