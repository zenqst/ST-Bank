from aiogram.fsm.state import StatesGroup, State

class Interaction(StatesGroup):
    amount = State()
    currency = State()
    type = State()
    msg_id = State()