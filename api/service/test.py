from api.service import BaseCRUDService
from schemas.schemas import Test
from schemas.schemas import TestItem

class TestService(BaseCRUDService[Test]):
    schema = Test

class TestItemService(BaseCRUDService[TestItem]):
    schema = TestItem
