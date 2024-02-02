from pydantic import BaseModel, validator
import re


class AddPlaylist(BaseModel):
    test_id: int
    playlist_id: str

    @validator("playlist_id")
    def validate_my_field(cls, value):
        if not re.match(r"^[a-zA-Z0-9_-]{34}$", value):
            raise ValueError("Значение не может быть отрицательным")
        return value