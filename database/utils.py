from typing import Any

import prettytable as pt
from millify import millify

from database.core import db


async def diff_convert(diff: float) -> str:
    """
    Конвертирует число 50.3 в строку вида "+50.3%" или "-50.3%".
    """
    diff = round(diff, 2)
    return f"+{diff}%" if diff >= 0 else f"{diff}%"


async def get_price(name: str, is_round: bool = True) -> dict[str, Any]:
    """
    Возвращает стоимость и разницу в цене валюты name.
    """
    name = name.lower()
    data = await db.select_data("coins", ["cost", "diff", "trend_score"], {"name": name})
    cost = round(data["cost"], 2) if is_round else data["cost"]
    diff = await diff_convert(data["diff"])
    return {"name": name, "cost": cost, "diff": diff, "trend_score": data["trend_score"]}


async def format_number(num: float) -> str:
    """
    Преобразует числа типа 123456.78 -> 123.45K. Числа ниже 100К не сокращает.
    """
    treshold_to_shorten = 100_000
    if abs(num) < treshold_to_shorten:
        s = f"{num:.2f}".rstrip("0").rstrip(".")
        return s
    return millify(num, precision=2)


async def send_table(
    data: list[tuple[str, int | float | str, str]], total_sum: str
) -> pt.PrettyTable:
    """
    Создаёт таблицу профиля пользователя для отображения.
    """
    table = pt.PrettyTable(["Название", "Количество", "Стоимость"])
    table.align["Название"] = "l"
    table.align["Количество"] = "r"
    table.align["Стоимость"] = "r"

    for symbol, amount, cost in data:
        amount_str = await format_number(amount) if isinstance(amount, float) else amount
        table.add_row([symbol, f"{amount_str}", cost])

    table.add_row(["-" * 10, "-" * 10, "-" * 15])
    table.add_row(["TOTAL", "", f"~{total_sum} RUB"])
    return table
