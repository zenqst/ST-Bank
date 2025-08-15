from database.core import db
from database.stats import StatsManager
from database.utils import get_price
from states.enums import UserStatus
from states.types import ProfileData


async def check_casino_balance(user_id: int):
    data = await db.select_data("users", "casino_pts", {"id": user_id})
    return data


async def register(user_id: int, username: str) -> UserStatus:
    status = await check_profile(user_id)
    if status == UserStatus.NOT_FOUND:
        stats = StatsManager(user_id)
        price_st = await get_price("st")
        price_v = await get_price("v")
        await db.insert_data("users", {"id": user_id, "username": username})
        await stats.load()
        await stats.record_buy("st", 15, price_st["cost"])
        await stats.record_buy("v", 5, price_v["cost"])
        await stats.save()
        return UserStatus.SUCCESS
    return status


async def get_profile(user_id: int) -> ProfileData:
    data = await db.select_data("users", "*", {"id": user_id}, fetch_all=False)
    return data


async def check_profile(user_id: int) -> UserStatus:
    data = await db.select_data("users", "id", {"id": user_id})
    if data:
        return UserStatus.ALREADY_EXISTS
    elif not data:
        return UserStatus.NOT_FOUND
    else:
        return UserStatus.ERROR


async def toggle_notify(user_id: int) -> None:
    data = await db.select_data("users", "notify", {"id": user_id})
    if data.get("notify") is True:
        await db.update_data("users", {"notify": False}, {"id": user_id})
    else:
        await db.update_data("users", {"notify": True}, {"id": user_id})
