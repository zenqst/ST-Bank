from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class Settings(BaseSettings):
    bot_token: SecretStr
    db_name: SecretStr
    db_port: SecretStr
    db_user: SecretStr
    db_password: SecretStr
    db_host: SecretStr
    db_pool_min: SecretStr
    db_pool_max: SecretStr
    notify_chat_id: SecretStr

    model_config: SettingsConfigDict = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )
    
class Config():
    version = 'v0.9',
    admin_id = 980316238

class ST():
    max_growth: float = 0.3
    max_fall: float = 0.3
    min_price: float = 50.0

class V():
    max_growth: float = 0.45
    max_fall: float = 0.45
    min_price: float = 500.0

settings = Settings()
config = Config()
st = ST()
v = V()