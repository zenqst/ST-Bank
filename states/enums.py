from enum import Enum


class UserStatus(Enum):
    SUCCESS = "success"
    ALREADY_EXISTS = "already_exists"
    NOT_FOUND = "not_found"
    ERROR = "error"


class StatusMessages(Enum):
    TABLE_DENIED = "Access to the table is denied"
    REQUEST_ERROR = "Request error"
    REQUEST_WITHOUT = "Request w/o WHERE"


class CoinActions(Enum):
    BUY = 'buy'
    SELL = 'sell'
    OPEN = 'open'


class Currencies(Enum):
    ST = 'st'
    V = 'v'
    BOX = 'box'
    RUB = 'rub'


class Steps(Enum):
    PROFILE = 'profile'
    ACTIONS = 'actions'
    CURRENCIES = 'currencies'