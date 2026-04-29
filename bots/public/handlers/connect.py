from aiogram import Router, types, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from services.user_service import create_user
from services.vpn_service import activate_access
from services.vpn_service import get_vpn_link

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

    # создаём пользователя через service
    user = create_user(
        tg_id=tg_id,
        username=username,
        password="auto"  # можно улучшить позже
    )

    # активируем trial access
    access = activate_access(username, plan="trial")

activate_access(username, plan="trial")

vpn = get_vpn_link(username)

await message.answer(
    f"✅ Access activated\n\n"
    f"👤 {vpn['username']}\n"
    f"🔑 {vpn['password']}\n"
    f"🌐 {vpn['link']}\n"
    f"⏳ {vpn['expires_at']}"
)

    await state.clear()
