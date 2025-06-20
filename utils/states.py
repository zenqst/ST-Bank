from aiogram.fsm.state import StatesGroup, State

class Interaction(StatesGroup):
    amount = State()
    currency = State()
    type = State()

class Donate(StatesGroup):
    amount = State()

class Sending_Text(StatesGroup):
    text = State()