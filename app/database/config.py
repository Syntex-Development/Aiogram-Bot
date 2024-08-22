from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import ClassVar

class Settings(BaseSettings):
    token: str = Field('7535191984:AAGil6PAyqKvf06gF7j3M5H8LekGRkOzRxE')
    database_url: str = Field('mysql+pymysql://root:1234@local/test_db')
    admin: int = Field(123)
    REFERRAL_REWARD: int = 2
    INITIAL_TASK_REWARD: int = 2
    REQUIRED_UC_FOR_WITHDRAWAL: int = 60

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(env_file='.env', extra='forbid')

settings = Settings()
