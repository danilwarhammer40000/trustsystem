from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import random
import string

from services.user_service import get_all_users, delete_user, create_user, extend_user
from core.sync import full_sync
from services.vpn_card_builder import build_vpn_card

router = Router()

class AddUserStates(StatesGroup):
    waiting_tg_id = State()
    waiting_password = State()


# ====================== START ======================
@router.message(F.text == "/start")
async def start(msg: types.Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 List users"), KeyboardButton(text="❌ Delete user")],
            [KeyboardButton(text="🔄 Sync users"), KeyboardButton(text="📊 Stats")],
            [KeyboardButton(text="➕ Add user")]
        ],
        resize_keyboard=True
    )
    await msg.answer("⚙️ **Admin Panel TrustTunnel**", reply_markup=kb)


# ====================== ADD USER ======================
@router.message(F.text == "➕ Add user")
async def add_user_start(msg: types.Message, state: FSMContext):
    await msg.answer("Отправьте Telegram ID пользователя:")
    await state.set_state(AddUserStates.waiting_tg_id)


@router.message(AddUserStates.waiting_tg_id)
async def process_tg_id(msg: types.Message, state: FSMContext):
    if not msg.text.strip().isdigit():
        return await msg.answer("❌ Нужно отправить только цифры (Telegram ID).")

    tg_id = int(msg.text.strip())
    await state.update_data(tg_id=tg_id)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Авто пароль", callback_data="pass:auto")],
        [InlineKeyboardButton(text="✍️ Ввести пароль вручную", callback_data="pass:manual")]
    ])

    await msg.answer(f"TG ID: <b>{tg_id}</b>\n\nВыберите способ создания пароля:", 
                     reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "pass:auto")
async def password_auto(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tg_id = data.get("tg_id")

    # Генерация случайного пароля
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))

    user = create_user(tg_id)
    user["password"] = password
    user["username"] = f"user{tg_id}"

    full_sync()
    await call.message.answer(f"✅ Пользователь создан!\n\n"
                              f"TG: {tg_id}\n"
                              f"Username: {user['username']}\n"
                              f"Пароль: <code>{password}</code>", parse_mode="HTML")
    await state.clear()
    await call.answer()


@router.callback_query(F.data == "pass:manual")
async def password_manual_start(call: types.CallbackQuery):
    await call.message.answer("Введите пароль для пользователя:")
    await call.answer()


@router.message(AddUserStates.waiting_password)
async def process_manual_password(msg: types.Message, state: FSMContext):
    password = msg.text.strip()
    if len(password) < 4:
        return await msg.answer("❌ Пароль слишком короткий (минимум 4 символа).")

    data = await state.get_data()
    tg_id = data.get("tg_id")

    user = create_user(tg_id)
    user["password"] = password
    user["username"] = f"user{tg_id}"

    full_sync()
    await msg.answer(f"✅ Пользователь создан!\n\n"
                     f"TG: {tg_id}\n"
                     f"Username: {user['username']}\n"
                     f"Пароль: <code>{password}</code>", parse_mode="HTML")
    await state.clear()


# ====================== LIST USERS ======================
def format_date(dt_str):
    if not dt_str:
        return "∞"
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%d-%m-%y")
    except:
        return dt_str


@router.message(F.text == "📋 List users")
async def list_users(msg: types.Message):
    users = get_all_users() or []
    if not users:
        return await msg.answer("Нет пользователей")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{u.get('username')} | {u.get('status','—')} | {format_date(u.get('expires_at'))}",
            callback_data=f"select:{u.get('telegram_id')}"
        )]
        for u in users if u.get('telegram_id')
    ])
    await msg.answer(f"📋 Пользователи ({len(users)}):", reply_markup=kb)


# (Остальные обработчики — select, link, extend, delete — можно добавить позже, если нужно)

@router.message(F.text == "🔄 Sync users")
async def sync_users(msg: types.Message):
    full_sync()
    await msg.answer("✅ Синхронизация выполнена")


@router.message(F.text == "📊 Stats")
async def stats(msg: types.Message):
    users = get_all_users() or []
    active = sum(1 for u in users if u.get("status") == "active")
    await msg.answer(f"📊 Статистика:\nАктивных: {active}\nВсего: {len(users)}")
