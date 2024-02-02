from fastapi import HTTPException

class MissingAuthHeaderError(HTTPException):
    def __init__(self, detail: str = "Нет токена!", status_code: int = 400):
        super().__init__(status_code=status_code, detail=detail)

class HTTPException404(HTTPException):
    def __init__(self, detail: str, status_code: int = 404):
        super().__init__(status_code=status_code, detail=detail)