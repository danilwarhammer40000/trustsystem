from aiogram.fsm.state import State, StatesGroup


class AddUser(StatesGroup):
    username = State()
    password = State()


class ManualDate(StatesGroup):
    date = State()