from aiogram.fsm.state import State, StatesGroup


class Interaction(StatesGroup):
    amount = State()
    currency = State()
    type = State()
    msg_id = State()
    confirmation = State()


class BroadcastText(StatesGroup):
    sending_text = State()


class AdminPanelId(StatesGroup):
    user_id = State()
    coin = State()
    amount = State()
