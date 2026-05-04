from aiogram import Router, types
from aiogram.fsm.context import FSMContext

from bots.public.states.payment import PaymentState

router = Router()


@router.message(lambda m: m.text == "🚀 Подключить")
async def connect(message: types.Message, state: FSMContext):
    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🎁 3 дня")],
            [types.KeyboardButton(text="💳 30 дней")],
            [types.KeyboardButton(text="💳 60 дней")]
        ],
        resize_keyboard=True
    )

    await state.set_state(PaymentState.choosing_plan)
    await message.answer("Выберите тариф:", reply_markup=kb)


@router.message(PaymentState.choosing_plan)
async def choose_plan(message: types.Message, state: FSMContext):
    plans = {
        "🎁 3 дня": "3",
        "💳 30 дней": "30",
        "💳 60 дней": "60"
    }

    plan = plans.get(message.text)

    if not plan:
        return await message.answer("❌ Выберите тариф кнопкой")

    await state.update_data(plan=plan)

    await state.set_state(PaymentState.waiting_username)
    await message.answer("Введите username (например: david):")