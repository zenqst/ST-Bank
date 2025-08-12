import json
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from database.stats import StatsManager


class DummyDB:
    def __init__(self):
        self._data = {
            "stats": "{}",  # Инициализируем как пустую строку JSON
            "trades": "{}"
        }

    async def select_data(self, table: str, column: str, filters: dict):
        # Возвращаем данные как есть (строку JSON)
        return {column: self._data.get(column)}

    async def update_data(self, table: str, data: dict, filters: dict):
        self._data.update(data)


@pytest.mark.asyncio
async def test_buy_and_sell_flow():
    db = DummyDB()
    stats = StatsManager(user_id=1)
    stats.db = db  # Подменяем БД на тестовую
    await stats.load()
    # Покупка 10 монет по 100
    await stats.record_buy("ST", amount=10, price=100)
    assert stats.stats["current_portfolio"]["ST"]["amount"] == 10
    assert stats.stats["average_buy_price"]["ST"] == 100.0
    assert stats.stats["deal_count"]["buy"] == 1
    # Продажа 5 монет по 150
    await stats.record_sell("ST", amount=5, price=150)
    assert stats.stats["current_portfolio"]["ST"]["amount"] == 5
    assert stats.stats["average_sell_price"]["ST"] == 150.0
    # ROI = (прибыль/общие_инвестиции)*100 = (250/1000)*100 = 25%
    assert stats.stats["roi"]["ST"] == pytest.approx(25.0)
    await stats.save()
    # Вывод итогового JSON
    print("\n📊 Итоговая статистика (Buy/Sell):")
    print(json.dumps(stats.stats, indent=2, ensure_ascii=False))


@pytest.mark.asyncio
async def test_multiple_buys_same_coin():
    """Тест множественных покупок одной монеты"""
    db = DummyDB()
    stats = StatsManager(user_id=1)
    stats.db = db
    await stats.load()
    # Первая покупка: 5 монет по 100
    await stats.record_buy("V", amount=5, price=100)
    # Вторая покупка: 5 монет по 200
    await stats.record_buy("V", amount=5, price=200)
    # Проверка общего количества
    assert stats.stats["current_portfolio"]["V"]["amount"] == 10
    # Проверка средней цены покупки: ((5*100) + (5*200)) / 10 = 150
    assert stats.stats["average_buy_price"]["V"] == 150.0
    # Проверка счетчика сделок
    assert stats.stats["deal_count"]["buy"] == 2
    await stats.save()
    print("\n📊 Итоговая статистика (Multiple Buys):")
    print(json.dumps(stats.stats, indent=2, ensure_ascii=False))


@pytest.mark.asyncio
async def test_sell_exact_amount():
    """Тест продажи точно того количества, что есть"""
    db = DummyDB()
    stats = StatsManager(user_id=1)
    stats.db = db
    await stats.load()
    # Покупка 5 монет
    await stats.record_buy("ST", amount=5, price=100)
    # Продажа всех 5 монет
    await stats.record_sell("ST", amount=5, price=150)
    # Должно остаться 0 монет
    assert stats.stats["current_portfolio"]["ST"]["amount"] == 0
    # Счетчик продаж должен увеличиться
    assert stats.stats["deal_count"]["sell"] == 1
    # ROI должен быть 50%: profit = 5*(150-100) = 250, invested = 5*100 = 500, roi = 250/500*100 = 50%
    assert stats.stats["roi"]["ST"] == pytest.approx(50.0)
    await stats.save()
    print("\n📊 Итоговая статистика (Sell Exact Amount):")
    print(json.dumps(stats.stats, indent=2, ensure_ascii=False))


@pytest.mark.asyncio
async def test_multiple_coins():
    """Тест работы с несколькими разными монетами"""
    db = DummyDB()
    stats = StatsManager(user_id=1)
    stats.db = db
    await stats.load()
    # Работа с ST
    await stats.record_buy("ST", amount=2, price=50000)
    await stats.record_sell("ST", amount=1, price=55000)
    # Работа с V
    await stats.record_buy("V", amount=10, price=3000)
    await stats.record_sell("V", amount=5, price=3200)
    # Проверка ST
    assert stats.stats["current_portfolio"]["ST"]["amount"] == 1
    # ROI для ST: profit = 1*(55000-50000) = 5000, invested = 2*50000 = 100000, roi = 5000/100000*100 = 5%
    assert stats.stats["roi"]["ST"] == pytest.approx(5.0)
    # Проверка V
    assert stats.stats["current_portfolio"]["V"]["amount"] == 5
    # ROI для V: profit = 5*(3200-3000) = 1000, invested = 10*3000 = 30000, roi = 1000/30000*100 = 3.33%
    assert stats.stats["roi"]["V"] == pytest.approx(3.33, abs=0.01)
    # Проверка общих счетчиков
    assert stats.stats["deal_count"]["buy"] == 2
    assert stats.stats["deal_count"]["sell"] == 2
    await stats.save()
    print("\n📊 Итоговая статистика (Multiple Coins):")
    print(json.dumps(stats.stats, indent=2, ensure_ascii=False))


@pytest.mark.asyncio
async def test_initial_state():
    """Тест начального состояния после загрузки"""
    db = DummyDB()
    stats = StatsManager(user_id=1)
    stats.db = db
    await stats.load()
    # Проверка начального состояния (пустые словари создаются при первой операции)
    # Но пока что stats пустой, так как не было операций
    assert isinstance(stats.stats, dict)
    await stats.save()
    print("\n📊 Итоговая статистика (Initial State):")
    print(json.dumps(stats.stats, indent=2, ensure_ascii=False))


@pytest.mark.asyncio
async def test_negative_roi():
    """Тест отрицательной рентабельности"""
    db = DummyDB()
    stats = StatsManager(user_id=1)
    stats.db = db
    await stats.load()
    # Покупка по высокой цене
    await stats.record_buy("ST", amount=1, price=1000)
    # Продажа по низкой цене
    await stats.record_sell("ST", amount=1, price=800)
    # ROI должен быть отрицательным: profit = 1*(800-1000) = -200, invested = 1000, roi = -200/1000*100 = -20%
    assert stats.stats["roi"]["ST"] == pytest.approx(-20.0)
    assert stats.stats["current_portfolio"]["ST"]["amount"] == 0
    await stats.save()
    print("\n📊 Итоговая статистика (Negative ROI):")
    print(json.dumps(stats.stats, indent=2, ensure_ascii=False))


@pytest.mark.asyncio
async def test_multi_day_trading():
    """Тест торговли в течение нескольких дней"""
    db = DummyDB()
    stats = StatsManager(user_id=1)
    stats.db = db
    await stats.load()
    # День 1: Покупка ST (2024-01-01)
    # Мокаем _get_today для этой операции
    with patch.object(stats, '_get_today', side_effect=lambda is_additional=False: "2024-01-01" if not is_additional else "2024-01-01T12:00:00"):
        await stats.record_buy("ST", amount=10, price=100)
    # День 2: Покупка V (2024-01-02)
    # Мокаем _get_today для этой операции
    with patch.object(stats, '_get_today', side_effect=lambda is_additional=False: "2024-01-02" if not is_additional else "2024-01-02T12:00:00"):
        await stats.record_buy("V", amount=5, price=200)
    # День 3: Продажа части ST (2024-01-03)
    # Мокаем _get_today для этой операции (включая внутренний вызов для profit_by_day)
    with patch.object(stats, '_get_today', side_effect=lambda is_additional=False: "2024-01-03" if not is_additional else "2024-01-03T12:00:00"):
        await stats.record_sell("ST", amount=5, price=150)
    # Проверки
    assert stats.stats["current_portfolio"]["ST"]["amount"] == 5
    assert stats.stats["current_portfolio"]["V"]["amount"] == 5
    assert stats.stats["deal_count"]["buy"] == 2
    assert stats.stats["deal_count"]["sell"] == 1
    # Проверка profit_by_day
    assert "2024-01-03" in stats.stats["profit_by_day"]
    assert "2024-01-01" not in stats.stats["profit_by_day"]
    assert "2024-01-02" not in stats.stats["profit_by_day"]
    # ROI для ST после продажи: profit = 5*(150-100) = 250, invested = 10*100 = 1000, roi = 250/1000*100 = 25%
    assert stats.stats["roi"]["ST"] == pytest.approx(25.0)
    await stats.save()
    print("\n📊 Итоговая статистика (Multi-Day Trading):")
    print(json.dumps(stats.stats, indent=2, ensure_ascii=False))


@pytest.mark.asyncio
async def test_weekly_summary():
    """Тест еженедельной сводки"""
    db = DummyDB()
    stats = StatsManager(user_id=1)
    stats.db = db
    await stats.load()
    # Эмуляция торговли в течение недели
    base_date = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    # Понедельник: покупка
    with patch('database.stats.datetime') as mock_date:
        mock_date.datetime.now.return_value = base_date
        mock_date.timezone.utc = UTC
        await stats.record_buy("ST", amount=10, price=100)  # Инвестиция 1000
    # Вторник: покупка
    with patch('database.stats.datetime') as mock_date:
        mock_date.datetime.now.return_value = base_date + timedelta(days=1)
        mock_date.timezone.utc = UTC
        await stats.record_buy("V", amount=5, price=200)   # Инвестиция 1000
    # Среда: продажа с прибылью
    with patch('database.stats.datetime') as mock_date:
        mock_date.datetime.now.return_value = base_date + timedelta(days=2)
        mock_date.timezone.utc = UTC
        await stats.record_sell("ST", amount=5, price=150)  # Прибыль 250
    # Четверг: продажа с убытком
    with patch('database.stats.datetime') as mock_date:
        mock_date.datetime.now.return_value = base_date + timedelta(days=3)
        mock_date.timezone.utc = UTC
        await stats.record_sell("V", amount=2, price=150)  # Убыток -100
    # Пятница: еще покупка
    with patch('database.stats.datetime') as mock_date:
        mock_date.datetime.now.return_value = base_date + timedelta(days=4)
        mock_date.timezone.utc = UTC
        await stats.record_buy("ST", amount=5, price=120)  # Инвестиция 600
    # Проверки
    assert stats.stats["current_portfolio"]["ST"]["amount"] == 10
    assert stats.stats["current_portfolio"]["V"]["amount"] == 3
    assert stats.stats["deal_count"]["total"] == 5
    assert stats.stats["deal_count"]["buy"] == 3
    assert stats.stats["deal_count"]["sell"] == 2
    assert stats.stats["profit"]["total"] == 150  # 250 - 100
    # Проверка прибыли по дням
    assert stats.stats["profit_by_day"]["2024-01-03"] == 250  # Среда
    assert stats.stats["profit_by_day"]["2024-01-04"] == -100  # Четверг
    await stats.save()
    print("\n📊 Итоговая статистика (Weekly Summary):")
    print(json.dumps(stats.stats, indent=2, ensure_ascii=False))


@pytest.mark.asyncio
async def test_monthly_performance():
    """Тест месячной производительности"""
    db = DummyDB()
    stats = StatsManager(user_id=1)
    stats.db = db
    await stats.load()
    # Эмуляция торговли в течение месяца
    start_date = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    # Разные дни месяца
    activities = [
        (0, "buy", "ST", 5, 100),    # 1 января
        (5, "buy", "V", 10, 50),     # 6 января
        (10, "sell", "ST", 3, 120),  # 11 января (прибыль)
        (15, "buy", "ST", 2, 90),    # 16 января
        (20, "sell", "V", 5, 40),    # 21 января (убыток)
        (25, "sell", "ST", 4, 110),  # 26 января (прибыль)
    ]
    for day_offset, action, currency, amount, price in activities:
        with patch('database.stats.datetime') as mock_date:
            mock_date.datetime.now.return_value = start_date + timedelta(days=day_offset)
            mock_date.timezone.utc = UTC
            if action == "buy":
                await stats.record_buy(currency, amount, price)
            elif action == "sell":
                await stats.record_sell(currency, amount, price)
    # Проверки
    assert stats.stats["deal_count"]["total"] == 6
    assert stats.stats["deal_count"]["buy"] == 3
    assert stats.stats["deal_count"]["sell"] == 3
    # Проверка финального портфеля
    assert stats.stats["current_portfolio"]["ST"]["amount"] == 0  # Все продано
    assert stats.stats["current_portfolio"]["V"]["amount"] == 5   # Осталось 5
    await stats.save()
    print("\n📊 Итоговая статистика (Monthly Performance):")
    print(json.dumps(stats.stats, indent=2, ensure_ascii=False))


@pytest.mark.asyncio
async def test_spam_attempt():
    """Тест добавления попыток спама"""
    db = DummyDB()
    stats = StatsManager(user_id=1)
    stats.db = db
    await stats.load()
    await stats.add_spam_attempt()
    # Проверки
    assert stats.stats["spam_attempts"] == 1
    await stats.save()
    print("\n📊 Итоговая статистика (Spam Attempt):")
    print(json.dumps(stats.stats, indent=2, ensure_ascii=False))


@pytest.mark.asyncio
async def test_best_deal_by_roi():
    db = DummyDB()
    stats = StatsManager(user_id=1)
    stats.db = db
    await stats.load()
    # Покупка 10 ST по 100
    await stats.record_buy("ST", amount=10, price=100)
    # Продажа 5 ST по 150 → ROI = (150 - 100) / 100 = 50%
    profit1 = await stats.record_sell("ST", amount=5, price=150)
    best = stats.stats.get("best_deal")
    assert best["currency"] == "ST"
    assert best["amount"] == 5
    assert best["price"] == 150
    assert best["roi"] == pytest.approx(50.0)
    assert best["profit"] == profit1
    # Покупка 4 V по 100
    await stats.record_buy("V", amount=4, price=100)
    # Продажа 4 V по 180 → ROI = 80%
    profit2 = await stats.record_sell("V", amount=4, price=180)
    best = stats.stats.get("best_deal")
    assert best["currency"] == "V"
    assert best["amount"] == 4
    assert best["price"] == 180
    assert best["roi"] == pytest.approx(80.0)
    assert best["profit"] == profit2
    # Покупка 2 USD по 200
    await stats.record_buy("USD", amount=2, price=200)
    # Продажа 2 USD по 250 → ROI = 25% (меньше текущего)
    await stats.record_sell("USD", amount=2, price=250)
    # best_deal не должен измениться
    best = stats.stats.get("best_deal")
    assert best["currency"] == "V"
    assert best["roi"] == pytest.approx(80.0)
    await stats.save()
    print("\n📊 Итоговая статистика (Best Deal):")
    print(json.dumps(stats.stats, indent=2, ensure_ascii=False))


@pytest.mark.asyncio
async def test_sell_more_than_have_raises():
    db = DummyDB()
    stats = StatsManager(user_id=1)
    stats.db = db
    await stats.load()

    await stats.record_buy("ST", amount=2, price=100)
    with pytest.raises(ValueError, match="Недостаточно валюты для продажи"):
        await stats.record_sell("ST", amount=5, price=200)


@pytest.mark.asyncio
async def test_sell_nonexistent_currency_raises():
    db = DummyDB()
    stats = StatsManager(user_id=1)
    stats.db = db
    await stats.load()

    with pytest.raises(ValueError, match="Нет такой валюты в портфеле"):
        await stats.record_sell("V", amount=1, price=1000)


@pytest.mark.asyncio
async def test_favorite_currency_updates_correctly():
    db = DummyDB()
    stats = StatsManager(user_id=1)
    stats.db = db
    await stats.load()

    await stats.record_buy("ST", amount=1, price=50000)  # invested = 50k
    await stats.record_buy("V", amount=10, price=2000)   # invested = 20k
    assert stats.stats["favorite_currency"] == "ST"

    await stats.record_buy("V", amount=20, price=2000)   # V invested = 60k
    assert stats.stats["favorite_currency"] == "V"


@pytest.mark.asyncio
async def test_sell_fifo_lots():
    db = DummyDB()
    stats = StatsManager(user_id=1)
    stats.db = db
    await stats.load()

    await stats.record_buy("ST", amount=2, price=100)  # Лот 1
    await stats.record_buy("ST", amount=3, price=200)  # Лот 2
    await stats.record_buy("ST", amount=5, price=300)  # Лот 3

    profit = await stats.record_sell("ST", amount=6, price=400)
    assert profit == pytest.approx(1300)
    assert stats.stats["current_portfolio"]["ST"]["amount"] == 4
    assert stats.trades["ST"][0]["price"] == 300


@pytest.mark.asyncio
async def test_avg_price_and_roi_precision():
    db = DummyDB()
    stats = StatsManager(user_id=1)
    stats.db = db
    await stats.load()

    await stats.record_buy("V", amount=1.3333, price=123.4567)
    assert stats.stats["current_portfolio"]["V"]["amount"] == pytest.approx(1.3333, abs=1e-4)
    assert stats.stats["current_portfolio"]["V"]["avg_price"] == round(123.4567, 2)

    await stats.record_sell("V", amount=1.3333, price=150.9876)
    roi = stats.stats["roi"]["V"]
    assert isinstance(roi, float)
    expected_roi = ((150.9876 - 123.4567) / 123.4567 * 100)
    assert abs(roi - expected_roi) < 0.05


@pytest.mark.asyncio
async def test_last_active_changes_each_time():
    db = DummyDB()
    stats = StatsManager(user_id=1)
    stats.db = db
    await stats.load()

    with patch.object(stats, "_get_today", side_effect=["2025-01-01T10:00:00", "2025-01-02T11:00:00"]):
        await stats.record_buy("ST", amount=1, price=50000)
        first_time = stats.stats["last_active"]
        await stats.record_buy("V", amount=1, price=51000)
        second_time = stats.stats["last_active"]

    assert first_time != second_time
    assert first_time == "2025-01-01T10:00:00"
    assert second_time == "2025-01-02T11:00:00"
    await stats.save()