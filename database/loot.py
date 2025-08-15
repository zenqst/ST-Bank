import random as rn
from json import JSONDecodeError, dumps, loads
from typing import Any

from aiogram.types import CallbackQuery, Message

from config_reader import config
from database.core import db
from database.currencies import create_action_msg
from database.user import get_profile
from keyboards.builders import create_box_button
from keyboards.inline import items_buttons
from states.enums import Currencies
from states.types import CurrencyInfo


async def find_loot_item(user_loot: list[dict[str, Any]], item_id: int) -> dict[str, Any] | None:
    for item in user_loot:
        if item.get("id") == item_id:
            return item
    return None


async def update_box_data(
    user_loot: list[dict[str, Any]], ruble_balance: float, boxes_left: float, user_id: int
) -> None:
    await db.update_data(
        "users",
        {"items": dumps(user_loot), "rubles": ruble_balance, "box": boxes_left},
        {"id": user_id},
    )


async def create_result_message(
    obtained_items: list[tuple[str, str]],
    amount: int,
    ruble_balance: dict[str, int | float],
    boxes_balance: dict[str, int],
) -> str:
    obtained_items.sort(key=lambda x: config.rarities[x[0]]["order"])
    items_text = "\n".join(item[1] for item in obtained_items) or "— ничего не выпало —"
    comp_text = (
        f"[+{ruble_balance['compensation']} RUB]" if ruble_balance["compensation"] > 0 else ""
    )
    boxes_compensation = boxes_balance["balance"] - boxes_balance["left"]
    result_message = (
        "<b>🎉 Поздравляем!</b>\n\n"
        f"<i>После открытия {amount} BOX, вы получили:</i>\n"
        f"{items_text}\n\n"
        "<i>После открытия изменился ваш баланс:</i>\n"
        f"<b>Баланс RUB:</b> {round(ruble_balance['balance'], 2)} <i>{comp_text}</i>\n"
        f"<b>Баланс BOX:</b> {boxes_balance['left']} <i>[-{boxes_compensation} BOX]</i>\n"
    )
    return result_message


async def get_available_items_by_rarity(all_items: list[dict], rarity_name: str) -> list[dict]:
    return [item for item in all_items if str(item["rarity"]) == rarity_name]


async def handle_loot_item(
    user_loot: list[dict], item_id: int, rarity_conf: dict, ruble_balance: dict[str, int | float]
) -> str:
    compensation_text = ""
    loot_item = await find_loot_item(user_loot, item_id)
    if loot_item:
        loot_item["count"] += 1
        compensation = rarity_conf["compensation"]
        ruble_balance["compensation"] += compensation
        ruble_balance["balance"] += compensation
        compensation_text = f"[+{compensation} RUB]"
    else:
        user_loot.append({"id": item_id, "count": 1})
    return compensation_text


async def process_box_rewards(
    amount: int,
    boxes_balance: dict[str, int],
    ruble_balance: dict[str, int | float],
    user_loot: list[dict[str, Any]],
    is_free: bool,
) -> list[tuple[str, str]]:
    obtained_items = []
    all_items = await db.select_data("items", ["id", "name", "rarity"], fetch_all=True)
    rarities = list(config.rarities.keys())
    weights = [config.rarities[r]["chance"] for r in rarities]
    lucky_chance = 0.1
    for _ in range(amount):
        if boxes_balance["balance"] <= 0 and not is_free:
            break
        selected_rarity = rn.choices(rarities, weights=weights, k=1)[0]
        rarity_conf = config.rarities[selected_rarity]
        rarity_name = rarity_conf["name"]
        available_items = await get_available_items_by_rarity(all_items, rarity_name)
        if not available_items:
            continue
        selected_item = rn.choice(available_items)
        item_id = selected_item["id"]
        item_name = selected_item["name"]
        compensation_text = await handle_loot_item(user_loot, item_id, rarity_conf, ruble_balance)
        obtained_items.append((
            selected_rarity,
            f"{rarity_conf['icon']} <b>{item_name}</b> <i>{compensation_text}</i>",
        ))
        if rn.random() > lucky_chance and not is_free:
            boxes_balance["left"] -= 1
    return obtained_items


async def open_box(
    user_id: int, call: CallbackQuery, *, amount: int = 1, is_free: bool = False
) -> None:
    if call.message is None:
        return
    profile = await get_profile(user_id)
    if not is_free and profile["box"] < amount:
        currency_info: CurrencyInfo = {
            "balance": profile["box"],
            "cost": None,
            "amount": amount,
        }
        text = await create_action_msg(
            Currencies.BOX,
            balance=None,
            currency_info=currency_info,
            action_word=None,
            profit=None,
        )
        await call.message.answer(text)
        return
    user_data = await db.select_data("users", "items", {"id": user_id})
    user_loot = loads(user_data["items"]) if user_data and user_data["items"] else []
    boxes_balance: dict[str, int] = {"balance": profile["box"], "left": profile["box"]}
    ruble_balance: dict[str, int | float] = {"balance": profile["rubles"], "compensation": 0}
    obtained_items = await process_box_rewards(
        amount, boxes_balance, ruble_balance, user_loot, is_free
    )
    await update_box_data(user_loot, ruble_balance["balance"], boxes_balance["left"], user_id)
    result_message = await create_result_message(
        obtained_items, amount, ruble_balance, boxes_balance
    )
    inline_kb = await create_box_button(amount=amount, box_balance=boxes_balance["left"])
    await call.message.answer(result_message, reply_markup=inline_kb)


def _generate_user_items_text(available_items: list[dict], user_items_dict: dict[int, int]) -> str:
    lines = []
    for item in available_items:
        count = user_items_dict.get(item["id"], 0)
        if count > 0:
            lines.append(f"{item['name']} <i>[{count} шт.]</i>")
    return "\n".join(lines)


async def build_rarity_section(
    rarity_key: str, info: dict, all_items: list[dict], user_items_dict: dict[int, int]
) -> str:
    name = info["display_name"]
    icon = info["icon"]
    chance = info["chance"]
    section_text = f"<b>{icon} {name} ({chance}%):</b> — "
    available_items = [item for item in all_items if item["rarity"] == rarity_key]
    item_count = len(available_items)
    if not user_items_dict:
        return section_text + f"0 из {item_count}\n<i>Не открыто ни одного предмета редкости</i>"
    count_with_user = sum(1 for item in available_items if user_items_dict.get(item["id"], 0) > 0)
    if count_with_user == 0:
        section_text += f"0 из {item_count}\n<i>Не открыто ни одного предмета редкости</i>"
    else:
        section_text += f"<b>{count_with_user}</b> из {item_count}\n"
        section_text += _generate_user_items_text(available_items, user_items_dict)
    section_text += "\n\n"
    return section_text


async def show_items(user_id: int, call: CallbackQuery):
    all_items = await db.select_data("items", ["id", "name", "rarity"], fetch_all=True)
    res = await db.select_data("users", ["items"], {"id": user_id})
    raw_items = res["items"] if res and res["items"] else None
    user_loot = []
    if raw_items:
        try:
            temp = loads(raw_items)
            user_loot = loads(temp) if isinstance(temp, str) else temp
        except JSONDecodeError:
            user_loot = []
    user_items_dict: dict[int, int] = {}
    for user_item in user_loot:
        if not isinstance(user_item, dict):
            continue
        user_items_dict[user_item["id"]] = user_items_dict.get(user_item["id"], 0) + user_item.get(
            "count", 0
        )
    text = ""
    for rarity_key, info in sorted(config.rarities.items(), key=lambda x: x[1]["order"]):
        section = await build_rarity_section(rarity_key, info, all_items, user_items_dict)
        text += section
    if isinstance(call.message, Message):
        return await call.message.edit_text(text, reply_markup=items_buttons)
