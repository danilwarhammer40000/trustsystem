from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from services.user_service import create_user
from services.vpn_service import activate_access, get_vpn_link

router = Router()


# =========================
# FSM
# =========================

class ConnectState(StatesGroup):
    username = State()


# =========================
# START
# =========================

@router.message(Command("connect"))
async def connect_start(message: types.Message, state: FSMContext):
    await state.set_state(ConnectState.username)
    await message.answer("Введите username (3-20 символов, a-z, 0-9, _):")


# =========================
# PROCESS USERNAME
# =========================

@router.message(ConnectState.username)
async def process_username(message: types.Message, state: FSMContext):

    username = (message.text or "").strip()
    tg_id = message.from_user.id

    # защита от пустого ввода
    if not username:
        await message.answer("❌ Введите username")
        return

    try:
        # создаём пользователя
        create_user(
            username=username,
            tg_id=tg_id
        )

        # активируем trial
        activate_access(username, plan="trial")

        # получаем VPN
        vpn = get_vpn_link(username)

        if not vpn:
            await message.answer("❌ Ошибка получения VPN")
            await state.clear()
            return

        await message.answer(
            f"✅ Доступ выдан\n\n"
            f"👤 {vpn.get('username')}\n"
            f"🔑 {vpn.get('password')}\n"
            f"🌐 {vpn.get('link')}\n"
            f"⏳ {vpn.get('expires_at')}"
        )

        await state.clear()

    except ValueError as e:
        await message.answer(f"❌ {str(e)}")

    except Exception as e:
        # чтобы бот не "умирал молча"
        await message.answer("❌ Внутренняя ошибка")
        print("CONNECT ERROR:", e)
        await state.clear()
