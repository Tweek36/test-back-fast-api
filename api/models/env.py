from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    secret_key: str
    algorithm: str = "HS256"
    exp_time_access: int = 3600
    exp_time_refresh: int = 2592000
    path_log_dir: str = "./logs"
    youtube_api_key: str
    images_folder: str = "./images"


env = Settings(
    _env_file=".env",
    _env_file_encoding="utf-8",
)
