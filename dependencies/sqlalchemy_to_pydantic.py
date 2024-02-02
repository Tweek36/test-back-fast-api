from schemas import Base
from pydantic import BaseModel, create_model
from typing import Optional



def sqlalchemy_to_pydantic(model: Base, name: str = "BaseModel", exclude: set = set(), make_all_optional: bool = False):

    fields = {}

    for column in model.__table__.columns:
        field_name = column.name
        if field_name in exclude:
            continue
        field_type = column.type.python_type
        nullable = True if make_all_optional else column.nullable

        if nullable:
            field_type = Optional[field_type]

        fields[field_name] = (field_type, None if nullable else ...)

    pydantic_model = create_model(name, **fields, __config__={"from_attributes": True})
    return pydantic_model