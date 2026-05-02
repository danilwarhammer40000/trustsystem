from aiogram import Router, types, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from services.user_service import create_user
from services.vpn_service import activate_access, get_vpn_link

router = Router()


# =========================
# FSM
# =========================

class ConnectState(StatesGroup):
    choosing_plan = State()
    username = State()


# =========================
# OPEN MENU
# =========================

@router.message(F.text == "🚀 Подключить")
async def connect_menu(message: types.Message, state: FSMContext):
    await state.set_state(ConnectState.choosing_plan)

    await message.answer(
        "Выберите тариф:\n\n"
        "🆓 trial — 3 дня\n"
        "💳 30 — 30 дней\n"
        "💳 60 — 60 дней\n\n"
        "Отправьте: trial / 30 / 60"
    )


# =========================
# SELECT PLAN
# =========================

@router.message(ConnectState.choosing_plan)
async def select_plan(message: types.Message, state: FSMContext):

    plan = (message.text or "").strip()

    if plan not in ["trial", "30", "60"]:
        await message.answer("❌ Неверный тариф")
        return

    await state.update_data(plan=plan)
    await state.set_state(ConnectState.username)

    await message.answer("Введите username (3-20 символов):")


# =========================
# USERNAME
# =========================

@router.message(ConnectState.username)
async def process_username(message: types.Message, state: FSMContext):

    username = (message.text or "").strip()
    tg_id = message.from_user.id

    data = await state.get_data()
    plan = data.get("plan")

    try:
        # создаём пользователя
        create_user(username=username, tg_id=tg_id)

        # TRIAL — сразу активируем
        if plan == "trial":
            activate_access(username, plan="trial")

            vpn = get_vpn_link(username)

            await message.answer(
                f"✅ Доступ выдан\n\n"
                f"👤 {vpn['username']}\n"
                f"🔑 {vpn['password']}\n"
                f"🌐 {vpn['link']}\n"
                f"⏳ {vpn['expires_at']}"
            )

        else:
            # платный тариф → в оплату
            await state.update_data(username=username)

            await message.answer(
                f"💳 Оплата тарифа {plan} дней\n"
                f"Отправьте /pay для оплаты"
            )

    except ValueError as e:
        await message.answer(f"❌ {str(e)}")

    except Exception as e:
        await message.answer("❌ Ошибка")
        print("CONNECT ERROR:", e)

    finally:
        await state.clear()