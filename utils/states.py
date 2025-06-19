from aiogram.fsm.state import StatesGroup, State

class Interaction(StatesGroup):
    amount = State()
    currency = State()
    type = State()

class Sending_Text(StatesGroup):
    text = State()