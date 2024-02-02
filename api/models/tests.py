from pydantic import BaseModel


class CreateTests(BaseModel):
    user_id: int
    ended: bool = False
    prev_choice: int | None = None
    cur_choice: int | None = None
    round: int = 1
    items: list[int] = []
    next_items: list[int] = []

class CreateChoice(BaseModel):
    tests_id: int
    winner_id: int
    loser_id: int

class MakeChoice(BaseModel):
    winner_id: int
    loser_id: int
