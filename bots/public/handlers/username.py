from aiogram import Router, types, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

router = Router()


class UsernameState(StatesGroup):
    waiting = State()


@router.message(F.text == "/username")
async def ask_username(message: types.Message, state: FSMContext):
    await state.set_state(UsernameState.waiting)
    await message.answer("Send username:")


@router.message(UsernameState.waiting)
async def save_username(message: types.Message, state: FSMContext):

    await message.answer(f"Saved username: {message.text}")

    await state.clear()
