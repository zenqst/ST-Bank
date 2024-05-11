from aiogram.fsm.state import StatesGroup, State


class Form(StatesGroup):
    name = State()
    age = State()
    sex = State()
    about = State()
    photo = State()

class Buy_ST(StatesGroup):
    pcs = State()

class Sell_ST(StatesGroup):
    pcs = State()

class Buy_V(StatesGroup):
    pcs = State()

class Sell_V(StatesGroup):
    pcs = State()

class Buy_Boxes(StatesGroup):
    pcs = State()