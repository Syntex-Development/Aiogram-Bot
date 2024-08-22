from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import ClassVar

class Settings(BaseSettings):
    token: str = Field(..., env='TOKEN')
    database_url: str = Field(..., env='DATABASE_URL')
    admin: int = Field(..., env='ADMIN')
    REFERRAL_REWARD: int = 2
    INITIAL_TASK_REWARD: int = 2
    REQUIRED_UC_FOR_WITHDRAWAL: int = 60

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(env_file='.env', extra='forbid')

settings = Settings()
