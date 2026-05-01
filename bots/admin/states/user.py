from aiogram.fsm.state import State, StatesGroup


class AddUser(StatesGroup):
    username = State()
    password = State()
    days = State()


class ExtendUser(StatesGroup):
    username = State()