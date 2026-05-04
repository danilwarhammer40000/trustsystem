from aiogram import Router, types, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from services.user_service import create_user, load_users
from services.vpn_service import activate_access, get_vpn_link

router = Router()


class ConnectState(StatesGroup):
    choosing_plan = State()
    username = State()


plan_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🆓 trial")],
        [KeyboardButton(text="💳 30 дней"), KeyboardButton(text="💳 60 дней")]
    ],
    resize_keyboard=True
)


@router.message(F.text == "🚀 Подключить")
async def connect_menu(message: types.Message, state: FSMContext):
    await state.set_state(ConnectState.choosing_plan)

    await message.answer(
        "Выберите тариф:",
        reply_markup=plan_kb
    )


@router.message(ConnectState.choosing_plan)
async def select_plan(message: types.Message, state: FSMContext):

    text = message.text

    mapping = {
        "🆓 trial": "trial",
        "💳 30 дней": "30",
        "💳 60 дней": "60"
    }

    plan = mapping.get(text)

    if not plan:
        await message.answer("❌ Выберите тариф кнопкой")
        return

    await state.update_data(plan=plan)

    # проверяем есть ли уже пользователь
    users = load_users()
    tg_id = message.from_user.id

    user = next((u for u in users if u.get("telegram_id") == tg_id), None)

    if user:
        # уже есть → сразу в оплату / продление
        await state.update_data(username=user["username"])

        if plan == "trial":
            await message.answer("❌ Триал уже использован")
            return

        await message.answer(f"💳 Продление {plan} дней\nНажмите /pay")
        return

    # новый пользователь
    await state.set_state(ConnectState.username)
    await message.answer("Введите username (3-20):")


@router.message(ConnectState.username)
async def process_username(message: types.Message, state: FSMContext):

    username = message.text.strip()
    tg_id = message.from_user.id

    data = await state.get_data()
    plan = data.get("plan")

    try:
        create_user(username=username, tg_id=tg_id)

        if plan == "trial":
            activate_access(username, "trial")

            vpn = get_vpn_link(username)

            await message.answer(
                f"✅ Доступ выдан\n\n"
                f"👤 {vpn['username']}\n"
                f"🔑 {vpn['password']}\n"
                f"🌐 {vpn['link']}\n"
                f"⏳ {vpn['expires_at']}"
            )

            await state.clear()
            return

        # платный → сохраняем
        await state.update_data(username=username)

        await message.answer(
            f"💳 Оплата {plan} дней\nНажмите /pay"
        )

    except ValueError as e:
        await message.answer(f"❌ {e}")

    except Exception as e:
        print(e)
        await message.answer("❌ Ошибка")