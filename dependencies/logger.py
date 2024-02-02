import logging
from logging.handlers import TimedRotatingFileHandler
import os
import traceback

from fastapi.concurrency import iterate_in_threadpool
from api.models.env import env
from dependencies.session import AsyncSessionLocal
from schemas.schemas import Log
from fastapi import Request
from fastapi import HTTPException
import asyncio
from http import HTTPStatus
from starlette.datastructures import UploadFile

class DBHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super().__init__(level)

    @staticmethod
    async def _save_to_db(record: logging.LogRecord):
        async with AsyncSessionLocal() as session:
            log = Log(
                message=record.message,
                level=record.levelname,
                status_code=record.status_code,
                url=record.url,
                method=record.method,
                params=record.params,
                name=record.name,
            )
            session.add(log)
            await session.commit()

    def emit(self, record):
        loop = asyncio.get_event_loop()
        loop.create_task(self._save_to_db(record))


class RequestLogger(logging.Logger):
    FORMATTER = logging.Formatter(
        "{asctime} [{levelname}] {name}: {url} [{method}] {status_code} {params}  - {message}",
        style="{",
    )

    def __init__(self, name, level=logging.NOTSET, logs_dir: str = env.path_log_dir):
        super().__init__(name, level)
        self.logs_dir = logs_dir
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)

        log_file = os.path.join(self.logs_dir, f"{self.name}.log")
        file_handler = TimedRotatingFileHandler(
            log_file,
            when="midnight",
            interval=1,
            backupCount=30,
            encoding="utf-8",
            utc=True,
        )

        def my_namer(default_name: str):
            base_filename, ext, date = default_name.split(".")
            return f"{base_filename}.{date}.{ext}"

        file_handler.namer = my_namer
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(self.FORMATTER)
        self.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(self.FORMATTER)
        self.addHandler(console_handler)

        db_handler = DBHandler()
        db_handler.setLevel(logging.DEBUG)
        db_handler.setFormatter(self.FORMATTER)
        self.addHandler(db_handler)

    async def __call__(self, request: Request, call_next):
        request_method = request.method
        request_url = request.url.path
        extra = {
            "method": request_method,
            "url": request_url,
            "status_code": 200,
            "params": {},
        }
        message = ""
        params = {}
        request_query_params = (
            request.query_params._dict if hasattr(request, "query_params") else {}
        )
        if request_query_params:
            params.update({"query_params": request_query_params})
        try:
            body = await request.json()
            params.update({"body": body})
        except Exception:
            pass

        try:
            response = await call_next(request)
        except HTTPException as e:
            response = e
            message = response.detail
        except Exception as e:
            message = traceback.format_exc()
            status_code = 500
            extra.update({"params": params, "status_code": status_code})
            self.critical(message, extra=extra)
            raise e
        
        form = {k:(str(v) if isinstance(v, UploadFile) else v) for k,v in (await request.form())._dict.items()}
        if form:
            params.update({"form": form})
            
        status_code = response.status_code
        params.update({"status_code": status_code})
        extra.update({"params": params})

        if 400 <= status_code < 500 and not message:
            response_body = [chunk async for chunk in response.body_iterator]
            response.body_iterator = iterate_in_threadpool(iter(response_body))
            message = response_body[0].decode("utf-8")

        if message:
            self.error(message, extra=extra)
            return response
        
        return response
