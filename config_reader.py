from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from states.types import Coin, RarityInfo


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
    github_token: SecretStr
    github_repo: SecretStr
    github_ref: SecretStr

    model_config: SettingsConfigDict = SettingsConfigDict(  # type: ignore[misc]
        env_file=".env",
        env_file_encoding="utf-8"
    )
    

class Config:
    admin_ids = [980316238]
    rarities: dict[str, RarityInfo] = {
        "legendary": {'name': 'legendary', 'display_name': 'Легендарная', 'icon': '🟡', 'chance': 1, 'compensation': 1100, 'order': 0},
        "mythic": {'name': 'mythic', 'display_name': 'Мифическая', 'icon': '🔴', 'chance': 3, 'compensation': 700, 'order': 1},
        "epic": {'name': 'epic', 'display_name': 'Эпическая', 'icon': '🟣', 'chance': 9, 'compensation': 500, 'order': 2},
        "exotic": {'name': 'exotic', 'display_name': 'Экзотическая', 'icon': '🟢', 'chance': 18, 'compensation': 300, 'order': 3},
        "common": {'name': 'common', 'display_name': 'Обычная', 'icon': '⚪️', 'chance': 69, 'compensation': 200, 'order': 4},
    }


class ST(Coin):
    max_growth: float = 0.25
    min_growth: float = 0.1
    max_fall: float = 0.3
    min_fall: float = 0.08
    min_price: float = 50.0


class V(Coin):
    max_growth: float = 0.40
    min_growth: float = 0.15
    max_fall: float = 0.45
    min_fall: float = 0.05
    min_price: float = 500.0


settings = Settings()  # type: ignore[call-arg]
config = Config()
st = ST()
v = V()