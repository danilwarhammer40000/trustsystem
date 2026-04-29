from aiogram import Router, types, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from services.user_service import create_user
from services.vpn_service import activate_access, get_vpn_link

router = Router()


class ConnectState(StatesGroup):
    username = State()


@router.message(F.text == "/connect")
async def connect_start(message: types.Message, state: FSMContext):
    await state.set_state(ConnectState.username)
    await message.answer("Enter username:")


@router.message(ConnectState.username)
async def process_username(message: types.Message, state: FSMContext):

    username = message.text.strip()
    tg_id = message.from_user.id

    try:
        # создаём пользователя
        create_user(
            tg_id=tg_id,
            username=username
        )

        # активируем trial
        activate_access(username, plan="trial")

        # получаем VPN
        vpn = get_vpn_link(username)

        await message.answer(
            f"✅ Access activated\n\n"
            f"👤 {vpn['username']}\n"
            f"🔑 {vpn['password']}\n"
            f"🌐 {vpn['link']}\n"
            f"⏳ {vpn['expires_at']}"
        )

    except ValueError as e:
        await message.answer(f"❌ Error: {str(e)}")

    await state.clear()
