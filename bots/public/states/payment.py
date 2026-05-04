from aiogram.fsm.state import StatesGroup, State


class PaymentState(StatesGroup):
    choosing_plan = State()
    waiting_username = State()
    ready_to_pay = State()