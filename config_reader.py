from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    bot_token: SecretStr
    db_password: SecretStr
    model_config: SettingsConfigDict = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

class Config():
    version = 'v0.5.5.2',
    admin_id = 980316238

class ST():
    max_growth = 0.3
    max_fall = 0.3
    min_price = 50

class V():
    max_growth = 0.45
    max_fall = 0.45
    min_price = 500


settings = Settings()
config = Config()
st = ST()
v = V()
