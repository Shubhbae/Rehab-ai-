from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
	app_name: str = Field(default="Rehab LSTM Backend")
	secret_key: str = Field(default="CHANGE_ME_SUPER_SECRET")
	algorithm: str = Field(default="HS256")
	access_token_expire_minutes: int = Field(default=60 * 24)
	database_url: str = Field(default="sqlite:///./rehab.db")
	media_dir: str = Field(default="media")
	models_dir: str = Field(default="app/models")
	movenet_model_handle: str = Field(
		default="https://tfhub.dev/google/movenet/singlepose/thunder/4"
	)
	lstm_model_path: str = Field(default="app/models/lstm_model.h5")

	class Config:
		env_file = ".env"
		populate_by_name = True


settings = Settings()

