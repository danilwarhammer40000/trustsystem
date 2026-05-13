from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
import random
import string

from services.user_service import get_all_users, delete_user, create_user, extend_user
from core.sync import full_sync
from services.vpn_card_builder import build_vpn_card

router = Router()

class AddUserStates(StatesGroup):
    waiting_tg_id = State()
    waiting_password = State()

class ExtendStates(StatesGroup):
    waiting_date = State()


# ====================== START ======================
@router.message(F.text == "/start")
async def start(msg: types.Message):
    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            ["📋 List users", "❌ Delete user"],
            ["🔄 Sync users", "📊 Stats"],
            ["➕ Add user"]
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

    await msg.answer(f"TG ID: <b>{tg_id}</b>\n\nВыберите пароль:", 
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


@router.callback_query(F.data.startswith("select:"))
async def user_selected(call: types.CallbackQuery):
    tg_id = call.data.split(":")[1]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Get Link", callback_data=f"link:{tg_id}")],
        [InlineKeyboardButton(text="➕ +3 дня", callback_data=f"extend:{tg_id}:3")],
        [InlineKeyboardButton(text="➕ +30 дней", callback_data=f"extend:{tg_id}:30")],
        [InlineKeyboardButton(text="♾️ Бесконечно", callback_data=f"extend:{tg_id}:9999")],
        [InlineKeyboardButton(text="📅 Ввести дату", callback_data=f"extend_date:{tg_id}")],
        [InlineKeyboardButton(text="❌ Удалить", callback_data=f"del:{tg_id}")]
    ])
    await call.message.answer(f"Выбран пользователь {tg_id}", reply_markup=kb)
    await call.answer()


# ====================== GET LINK ======================
@router.callback_query(F.data.startswith("link:"))
async def get_link(call: types.CallbackQuery):
    tg_id = call.data.split(":")[1]
    card = build_vpn_card(tg_id)
    await call.message.answer(card.get("text", "Ошибка"))
    await call.answer()


# ====================== EXTEND ======================
@router.callback_query(F.data.startswith("extend:"))
async def extend_handler(call: types.CallbackQuery):
    _, tg_id_str, days_str = call.data.split(":")
    tg_id = int(tg_id_str)
    days = int(days_str)

    try:
        if days == 9999:
            extend_user(tg_id, 9999)
            await call.message.answer(f"✅ Бессрочный доступ выдан")
        else:
            extend_user(tg_id, days)
            await call.message.answer(f"✅ Продлено на {days} дней")
        full_sync()
    except Exception as e:
        await call.message.answer(f"❌ Ошибка: {e}")
    await call.answer()


# ====================== MANUAL DATE EXTEND ======================
@router.callback_query(F.data.startswith("extend_date:"))
async def extend_date_start(call: types.CallbackQuery, state: FSMContext):
    tg_id = call.data.split(":")[1]
    await state.update_data(tg_id=tg_id)
    await call.message.answer("Введите дату окончания в формате ДД-ММ-ГГ (например: 31-12-26)")
    await call.answer()


# ====================== DELETE ======================
@router.callback_query(F.data.startswith("del:"))
async def delete_cb(call: types.CallbackQuery):
    tg_id = int(call.data.split(":")[1])
    if delete_user(tg_id):
        full_sync()
        await call.message.answer(f"✅ Удалён пользователь {tg_id}")
    else:
        await call.message.answer("Пользователь не найден")
    await call.answer()


# ====================== SYNC & STATS ======================
@router.message(F.text == "🔄 Sync users")
async def sync_users(msg: types.Message):
    full_sync()
    await msg.answer("✅ Синхронизация выполнена")


@router.message(F.text == "📊 Stats")
async def stats(msg: types.Message):
    users = get_all_users() or []
    active = sum(1 for u in users if u.get("status") == "active")
    await msg.answer(f"📊 Статистика:\nАктивных: {active}\nВсего: {len(users)}")