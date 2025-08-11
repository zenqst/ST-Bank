import datetime
from json import dumps, loads

from database.core import db


async def format_currency(val: float) -> str:
    return f"{val:,.2f}".replace(",", " ")


from aiogram.types import CallbackQuery

from keyboards.inline import items_buttons


class StatsManager:
    """
    Класс для работы со статистикой.
    При инициализации использовать stats.load()
    После всех операций использовать stats.save()
    """
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.db = db
        self.stats = {}
        self.trades = {}

    def __getitem__(self, key):
        return self.stats[key]

    def __setitem__(self, key, value):
        self.stats[key] = value

    async def load(self):
        """Загружает статистику из БД"""
        row = await self.db.select_data("users", "stats", {"id": self.user_id})
        self.stats = loads(row["stats"] or "{}")

        row = await self.db.select_data("users", "trades", {"id": self.user_id})
        self.trades = loads(row['trades'] or "{}")

    @staticmethod
    def _get_today(*, is_additional: bool = False) -> str:
        now = datetime.datetime.now()
        if is_additional:
            return now.isoformat(timespec='seconds')
        else:
            return now.date().isoformat()

    def _init_currency_fields(self, currency: str):
        keys = ["invested", "sold", "average_buy_price", "average_sell_price", "roi", "profit"]
        for key in keys:
            if key not in self.stats:
                self.stats[key] = {}
            if currency not in self.stats[key]:
                self.stats[key][currency] = 0

        if "profit" not in self.stats:
            self.stats["profit"] = {}
        if "total" not in self.stats["profit"]:
            self.stats["profit"]["total"] = 0
        if "current_portfolio" not in self.stats:
            self.stats["current_portfolio"] = {}
        if currency not in self.stats["current_portfolio"]:
            self.stats["current_portfolio"][currency] = {"amount": 0, "avg_price": 0}
        
        if "sell_history" not in self.stats:
            self.stats["sell_history"] = {}
        if currency not in self.stats["sell_history"]:
            self.stats["sell_history"][currency] = {"total_amount": 0, "total_value": 0}

    def _init_counters(self):
        self.stats.setdefault("deal_count", {"total": 0, "buy": 0, "sell": 0})
        self.stats.setdefault("spam_attempts", 0)
        self.stats.setdefault("profit_by_day", {})

    async def update_favorite_currency(self):
        totals = {}
        for key in ["invested", "sold"]:
            for curr, val in self.stats.get(key, {}).items():
                totals[curr] = totals.get(curr, 0) + val
        if not totals:
            self.stats["favorite_currency"] = None
        else:
            self.stats["favorite_currency"] = max(totals, key=totals.get)

    async def record_buy(self, currency: str, amount: float, price: float):
        if amount <= 0 or price <= 0:
            raise ValueError("Количество и цена должны быть положительными числами")
        
        self._init_counters()
        self._init_currency_fields(currency)

        self.stats["invested"][currency] = self.stats["invested"].get(currency, 0) + amount * price
        self.stats["deal_count"]["total"] += 1
        self.stats["deal_count"]["buy"] += 1

        current = self.stats["current_portfolio"].get(currency, {"amount": 0, "avg_price": 0})
        total_amount = current["amount"] + amount
        total_value = current["amount"] * current["avg_price"] + amount * price
        avg_price = total_value / total_amount if total_amount > 0 else 0

        self.stats["current_portfolio"][currency] = {
            "amount": round(total_amount, 4),
            "avg_price": round(avg_price, 2)
        }

        self.stats["average_buy_price"][currency] = round(avg_price, 2)

        new_trade = {"amount": amount, "price": price}

        if currency not in self.trades:
            self.trades[currency] = []

        self.trades[currency].append(new_trade)

        await self.update_favorite_currency()
        self.stats["last_active"] = self._get_today(is_additional=True)
    
    async def record_lots(self, remaining: float, currency: str, price: float):
        self._init_counters()
        self._init_currency_fields(currency)

        lots = self.trades[currency].copy()
        new_lots = []
        profit = 0.0
        invested_in_sold = 0.0

        for lot in lots:
            if remaining <= 0:
                new_lots.append(lot)
                continue
                
            lot_amount = lot["amount"]
            lot_price = lot["price"]
            
            if lot_amount <= remaining:
                profit += lot_amount * (price - lot_price)
                invested_in_sold += lot_amount * lot_price
                remaining -= lot_amount
            else:
                profit += remaining * (price - lot_price)
                invested_in_sold += remaining * lot_price
                updated_lot = lot.copy()
                updated_lot["amount"] = lot_amount - remaining
                new_lots.append(updated_lot)
                remaining = 0

        if remaining > 0:
            raise ValueError("Недостаточно валюты для продажи")

        return profit, invested_in_sold, new_lots

    async def record_sell(self, currency: str, amount: float, price: float):
        if amount <= 0 or price <= 0:
            raise ValueError("Количество и цена должны быть положительными числами")
        
        self._init_counters()
        self._init_currency_fields(currency)

        self.stats["sold"][currency] = self.stats["sold"].get(currency, 0) + amount * price
        self.stats["deal_count"]["total"] += 1
        self.stats["deal_count"]["sell"] += 1

        if currency not in self.trades:
            raise ValueError(f"Нет такой валюты в портфеле ({currency})")

        profit, invested_in_sold, new_lots = await self.record_lots(amount, currency, price)

        self.trades[currency] = new_lots

        current = self.stats["current_portfolio"].get(currency, {"amount": 0, "avg_price": 0})
        total_amount = current["amount"] - amount
        avg_price = current["avg_price"] if total_amount > 0 else 0

        self.stats["current_portfolio"][currency] = {
            "amount": round(total_amount, 4),
            "avg_price": round(avg_price, 2)
        }

        sell_history = self.stats["sell_history"][currency]
        old_total_amount = sell_history["total_amount"]
        old_total_value = sell_history["total_value"]
        
        new_total_amount = old_total_amount + amount
        new_total_value = old_total_value + (amount * price)
        
        self.stats["sell_history"][currency] = {
            "total_amount": new_total_amount,
            "total_value": new_total_value
        }
        
        self.stats["average_sell_price"][currency] = round(
            new_total_value / new_total_amount if new_total_amount > 0 else 0, 2
        )

        self.stats["profit"][currency] += profit
        self.stats["profit"]["total"] += profit

        today = self._get_today(is_additional=False)
        self.stats["profit_by_day"].setdefault(today, 0)
        self.stats["profit_by_day"][today] += profit

        total_invested = self.stats["invested"].get(currency, 0)
        total_profit = self.stats["profit"].get(currency, 0)
        roi = (total_profit / total_invested) * 100 if total_invested > 0 else 0
        self.stats["roi"][currency] = round(roi, 2)

        current_best = self.stats.get("best_deal", None)
        deal_roi = (profit / invested_in_sold) * 100 if invested_in_sold > 0 else 0
        deal_info = {
            "currency": currency,
            "amount": amount,
            "price": price,
            "profit": profit,
            "roi": round(deal_roi, 2),
            "date": self._get_today(is_additional=False)
        }
        
        if (current_best is None) or (profit > current_best.get("profit", 0)):
            self.stats["best_deal"] = deal_info

        await self.update_favorite_currency()
        self.stats["last_active"] = self._get_today(is_additional=True)

        return profit

    async def add_spam_attempt(self):
        self._init_counters()
        self.stats["spam_attempts"] += 1

    async def save(self):
        await self.db.update_data("users", {"stats": dumps(self.stats), "trades": dumps(self.trades)}, {"id": self.user_id})

    async def show_stats(self, username: str, user_id: int, call: CallbackQuery) -> None:
        stats = StatsManager(user_id)
        await stats.load()

        deal_count = stats.stats.get('deal_count', {})
        invested = stats.stats.get('invested', {})
        sold = stats.stats.get('sold', {})
        profit = stats.stats.get('profit', {})
        roi = stats.stats.get('roi', {})
        best_deal = stats.stats.get('best_deal', {})

        text = (
            f"📊\u003cb\u003eСтатистика пользователя @{username}\u003c/b\u003e (\u003ci\u003e{user_id}\u003c/i\u003e)\n\n"
            "🏛 \u003cu\u003eОперации:\u003c/u\u003e\n"
            f"• Покупка: {deal_count.get('buy', 0)}\n"
            f"• Продажа: {deal_count.get('sell', 0)}\n"
            f"• Общее: {deal_count.get('total', 0)}\n\n"
            "💸 \u003cu\u003eИнвестировано:\u003c/u\u003e\n"
            f"• ST: {await format_currency(invested.get('st', 0))} RUB\n"
            f"• V: {await format_currency(invested.get('v', 0))} RUB\n\n"
            "💰 \u003cu\u003eПродано:\u003c/u\u003e\n"
            f"• ST: {await format_currency(sold.get('st', 0))} RUB\n"
            f"• V: {await format_currency(sold.get('v', 0))} RUB\n\n"
            "📈 \u003cu\u003eПрибыль:\u003c/u\u003e\n"
            f"• ST: {await format_currency(profit.get('st', 0))} RUB\n"
            f"• V: {await format_currency(profit.get('v', 0))} RUB\n\n"
            "📊 \u003cu\u003eROI*:\u003c/u\u003e\n"
            f"• ST: {roi.get('st', 0)}%\n"
            f"• V: {roi.get('v', 0)}%\n\n"
        )

        if stats.stats.get('favorite_currency'):
            text += f"⭐️ \u003cu\u003eЛюбимая валюта:\u003c/u\u003e {stats.stats.get('favorite_currency', '').upper()}\n"
        if best_deal:
            text += f"🏆 \u003cu\u003eЛучшая сделка:\u003c/u\u003e {best_deal.get('currency', '').upper()} \u003ci\u003e({best_deal.get('roi', 0)}% ROI*)\u003c/i\u003e\n"

        text += (
            f"😡 \u003cu\u003eПопытки спама:\u003c/u\u003e {stats.stats.get('spam_attempts', 0)}\n\n"
            "\u003ci\u003e*ROI (Return on Investment) — доходность инвестиций в процентах\u003c/i\u003e"
        )

        await call.message.edit_text(text, reply_markup=items_buttons)