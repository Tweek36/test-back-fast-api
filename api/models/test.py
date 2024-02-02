from pydantic import BaseModel
from dependencies.sqlalchemy_to_pydantic import sqlalchemy_to_pydantic
from schemas.schemas import Test as TestSchema
from schemas.schemas import TestItem as TestItemSchema


class Test(sqlalchemy_to_pydantic(TestSchema)):
    ...


class UpdateTest(
    sqlalchemy_to_pydantic(
        TestSchema, exclude={"id", "user_id"}, make_all_optional=True
    )
):
    ...


class TestItem(sqlalchemy_to_pydantic(TestItemSchema)):
    ...

class AddTestItem(BaseModel):
    title: str
    description: str = ''
    videoId: str

class PatchTestItem(BaseModel):
    title: str | None
    description: str | None
    videoId: str | None
