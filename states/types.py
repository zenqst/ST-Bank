from typing import TypedDict


class Coin:
    max_growth: float = 0.0
    min_growth: float = 0.0
    max_fall: float = 0.0
    min_fall: float = 0.0
    min_price: float = 0.0


class RarityInfo(TypedDict):
    name: str
    icon: str
    chance: int
    compensation: int
    order: int