from api.service import BaseCRUDService
from schemas.schemas import Tests as TestsSchema
from schemas.schemas import Choice as ChoiceSchema
import random

class TestsService(BaseCRUDService[TestsSchema]):
    # schema = TestsSchema
    ...

class ChoiceService(BaseCRUDService[ChoiceSchema]):
    @staticmethod
    def get_pair(items: list):
        if len(items) == 0:
            return [], items
        if len(items) == 1:
            return [items.pop()], items        
        return [items.pop(random.randint(0, len(items) - 1)), items.pop(random.randint(0, len(items) - 1))], items
        