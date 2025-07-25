from typing import Literal, TypedDict


class Coin:
    max_growth: float = 0.0
    min_growth: float = 0.0
    max_fall: float = 0.0
    min_fall: float = 0.0
    min_price: float = 0.0


class RarityInfo(TypedDict):
    name: str
    display_name: str
    icon: str
    chance: int
    compensation: int
    order: int


class Item(TypedDict):
    id: int
    count: int


class ProfileData(TypedDict):
    id: int
    username: str
    rubles: float
    st: float
    v: float
    box: int
    items: Item
    casino_pts: int


TableProfile = list[tuple[str, int | float | str, str]]
CurrencyKey = Literal['rubles', 'st', 'v', 'box']