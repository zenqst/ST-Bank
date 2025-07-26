import datetime
from json import dumps, loads


class StatsManager:
    def __init__(self, user_id: int, db):
        self.user_id = user_id
        self.db = db
        self.stats = {}
        self.trades = {}

    async def load(self):
        """Загружает статистику из БД"""
        row = await self.db.select_data("users", "stats", {"id": self.user_id})
        self.stats = loads(row["stats"] or "{}")

        row = await self.db.select_data("users", "trades", {"id": self.user_id})
        self.trades = loads(row['trades'] or "{}")

    @staticmethod
    def _get_today(is_additional: bool = False) -> str:
        now = datetime.datetime.now(tz=datetime.UTC)
        if is_additional:
            return now.isoformat(timespec='seconds').split('+')[0]
        else:
            return now.date().isoformat()

    def _init_currency_fields(self, currency: str):
        for key in ["invested", "sold", "average_buy_price", "average_sell_price", "roi"]:
            self.stats.setdefault(key, {})
            self.stats[key].setdefault(currency, 0)
        self.stats.setdefault("current_portfolio", {})
        self.stats["current_portfolio"].setdefault(currency, {"amount": 0, "avg_price": 0})

    def _init_counters(self):
        self.stats.setdefault("deal_count", {"total": 0, "buy": 0, "sell": 0})
        self.stats.setdefault("profit_total", 0)
        self.stats.setdefault("spam_attempts", 0)
        self.stats.setdefault("profit_by_day", {})
        self.stats.setdefault("favorite_currency", None)

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
        self._init_counters()
        self._init_currency_fields(currency)

        self.stats["invested"][currency] = self.stats["invested"].get(currency, 0) + amount * price
        self.stats["deal_count"]["total"] += 1
        self.stats["deal_count"]["buy"] += 1

        current = self.stats["current_portfolio"].get(currency, {"amount": 0, "avg_price": 0})
        total_amount = current["amount"] + amount
        total_value = current["amount"] * current["avg_price"] + amount * price
        avg_price = total_value / total_amount if total_amount != 0 else price

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
    
    async def record_sell(self, currency: str, amount: float, price: float):
        self._init_counters()
        self._init_currency_fields(currency)

        self.stats["sold"][currency] = self.stats["sold"].get(currency, 0) + amount * price
        self.stats["deal_count"]["total"] += 1
        self.stats["deal_count"]["sell"] += 1

        if currency not in self.trades:
            raise ValueError("Нет такой валюты в портфеле")

        lots = self.trades[currency]
        profit = 0.0
        invested_in_sold = 0.0
        new_lots = []
        remaining = amount

        for lot in lots:
            lot_amount = lot["amount"]
            lot_price = lot["price"]
            if lot_amount <= remaining:
                profit += lot_amount * (price - lot_price)
                invested_in_sold += lot_amount * lot_price
                remaining -= lot_amount
            else:
                profit += remaining * (price - lot_price)
                invested_in_sold += remaining * lot_price
                lot["amount"] -= remaining
                new_lots.append(lot)
                remaining = 0
                break

        if remaining > 0:
            raise ValueError("Недостаточно валюты для продажи")

        self.trades[currency] = new_lots

        # Обновляем текущий портфель
        current = self.stats["current_portfolio"].get(currency, {"amount": 0, "avg_price": 0})
        total_amount = current["amount"] - amount
        avg_price = current["avg_price"] if total_amount > 0 else 0

        self.stats["current_portfolio"][currency] = {
            "amount": round(total_amount, 4),
            "avg_price": round(avg_price, 2)
        }

        self.stats["average_sell_price"][currency] = round(price, 2)

        self.stats["profit_total"] += profit

        today = self._get_today(is_additional=False)
        self.stats["profit_by_day"].setdefault(today, 0)
        self.stats["profit_by_day"][today] += profit

        roi = (profit / invested_in_sold) * 100 if invested_in_sold != 0 else 0
        self.stats["roi"][currency] = round(roi, 2)

        await self.update_favorite_currency()
        self.stats["last_active"] = self._get_today(is_additional=True)

    async def add_spam_attempt(self):
        self._init_counters()
        self.stats["spam_attempts"] += 1

    async def save(self):
        await self.db.update_data("users", {"stats": dumps(self.stats), "trades": dumps(self.trades)}, {"id": self.user_id})