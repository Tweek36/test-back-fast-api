from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from api.endpoints.user import router as user_router
from api.endpoints.search import router as search_router
from api.endpoints.youtube import router as youtube_router
from api.endpoints.test import router as test_router
from api.endpoints.tests import router as tests_router
from dependencies.logger import RequestLogger
from fastapi.middleware.cors import CORSMiddleware
from api.models.env import env


app = FastAPI()
request_logger = RequestLogger("request")

app.middleware("http")(request_logger)

app.mount("/image", StaticFiles(directory=env.images_folder), name="image")
origins = [
    "http://localhost:8000",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(user_router)
app.include_router(search_router)
app.include_router(youtube_router)
app.include_router(test_router)
app.include_router(tests_router)
