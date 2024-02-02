import re
from fastapi import APIRouter, Depends, HTTPException, Query
import httpx
from api.models.env import env
from api.models.jwt import JwtTokenData
from api.models.youtube import AddPlaylist
from api.service.test import TestService, TestItemService
from dependencies.jwt_token import get_token_data
from dependencies.session import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.schemas import Test as TestSchema
from schemas.schemas import TestItem as TestItemSchema
from sqlalchemy import insert
from psycopg2 import IntegrityError

router = APIRouter(prefix="/youtube", tags=["YouTube"])


def validate_youtube_video_id(id: str = Query(..., title="YouTube Video ID")):
    if not re.match(r"^[a-zA-Z0-9_-]{11}$", id):
        raise HTTPException(status_code=400, detail="Invalid YouTube Video ID format")
    return id



@router.get("/video-title/")
async def get_video_title(
    id: str = Depends(validate_youtube_video_id),
    token: JwtTokenData = Depends(get_token_data),
):
    youtube_api_url = f"https://www.googleapis.com/youtube/v3/videos?id={id}&part=snippet&key={env.youtube_api_key}"

    async with httpx.AsyncClient() as client:
        response = await client.get(youtube_api_url)

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code, detail="Failed to fetch video details"
        )
    response: dict = response.json()
    items = response.get("items")
    snippet: dict | None = items[0].get("snippet") if items else None
    video_title = snippet.get("title") if snippet else None

    return {"video_id": id, "video_title": video_title}


@router.post("/playlist-videos/")
async def add_playlis_videos(
    data: AddPlaylist,
    token: JwtTokenData = Depends(get_token_data),
    session: AsyncSession = Depends(get_async_session)
):
    service = TestService(session)
    if not await service.get(TestSchema.id == data.test_id, TestSchema.user_id == token.sub):
        raise HTTPException(status_code=404, detail="Тест не найден")
    playlist_api_url = f"https://www.googleapis.com/youtube/v3/playlistItems?playlistId={data.playlist_id}&part=contentDetails,snippet&key={env.youtube_api_key}&maxResults=50"  # Увеличьте maxResults по необходимости

    all_video_info = []

    async with httpx.AsyncClient() as client:
        while True:
            response = await client.get(playlist_api_url)
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code, detail="Failed to fetch playlist details"
                )

            response_data = response.json()
            items = response_data.get("items", [])

            video_info = [{"videoId": item["contentDetails"]["videoId"], "description": "", "test_id": data.test_id, "title": item["snippet"]["title"]} for item in items]
            all_video_info.extend(video_info)

            next_page_token = response_data.get("nextPageToken")
            if not next_page_token:
                break  # Выход из цикла, если больше страниц нет

            playlist_api_url = f"https://www.googleapis.com/youtube/v3/playlistItems?playlistId={data.playlist_id}&part=contentDetails,snippet&key={env.youtube_api_key}&maxResults=50&pageToken={next_page_token}"

    service = TestItemService(session)
    try:
        response = await service.add(all_video_info)
        response_data = [i.__dict__.copy() for i in response]
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail=f"This {TestItemSchema.__name__} already exists",
        )
    
    await session.commit()

    return response_data