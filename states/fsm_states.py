from aiogram.fsm.state import State, StatesGroup


class Interaction(StatesGroup):
    amount = State()
    currency = State()
    type = State()
    msg_id = State()


class BroadcastText(StatesGroup):
    sending_text = State()