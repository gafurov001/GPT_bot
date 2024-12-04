from aiogram.fsm.state import StatesGroup, State


class Form(StatesGroup):
    full_name = State()
    phone_number = State()
    user_id = State()
    text = State()
    image = State()