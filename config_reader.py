from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    bot_token: SecretStr
    db_name: SecretStr
    db_port: SecretStr
    db_user: SecretStr
    db_password: SecretStr
    db_host: SecretStr


    model_config: SettingsConfigDict = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

class Config():
    version = 'v0.8',
    admin_id = 980316238

class ST():
    max_growth = 0.3
    max_fall = 0.3
    min_price = 50

class V():
    max_growth = 0.45
    max_fall = 0.45
    min_price = 500
    in_irl_rub = 100


settings = Settings()
config = Config()
st = ST()
v = V()