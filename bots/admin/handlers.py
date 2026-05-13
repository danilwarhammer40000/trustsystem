from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

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
        return await msg.answer("❌ Нужно отправить только цифры — Telegram ID.")

    tg_id = int(msg.text.strip())
    await state.update_data(tg_id=tg_id)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Автоматический пароль", callback_data="pass:auto")],
        [InlineKeyboardButton(text="✍️ Ввести пароль вручную", callback_data="pass:manual")]
    ])

    await msg.answer(f"Пользователь TG ID: <b>{tg_id}</b>\n\nВыберите способ создания пароля:", 
                     reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "pass:auto")
async def password_auto(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tg_id = data.get("tg_id")
    
    user = create_user(tg_id)
    user["password"] = "auto"
    user["username"] = f"user{tg_id}"   # без подчёркивания

    full_sync()
    await call.message.answer(f"✅ Пользователь создан!\n\n"
                              f"TG ID: {tg_id}\n"
                              f"Username: {user['username']}\n"
                              f"Пароль: auto")
    await state.clear()
    await call.answer()


@router.callback_query(F.data == "pass:manual")
async def password_manual(call: types.CallbackQuery):
    await call.message.answer("Введите желаемый пароль:")
    await call.answer()


@router.message(AddUserStates.waiting_password)
async def process_manual_password(msg: types.Message, state: FSMContext):
    password = msg.text.strip()
    if len(password) < 3:
        return await msg.answer("❌ Пароль слишком короткий (минимум 3 символа).")

    data = await state.get_data()
    tg_id = data.get("tg_id")

    user = create_user(tg_id)
    user["password"] = password
    user["username"] = f"user{tg_id}"

    full_sync()
    await msg.answer(f"✅ Пользователь создан!\n\n"
                     f"TG ID: {tg_id}\n"
                     f"Username: {user['username']}\n"
                     f"Пароль: <code>{password}</code>", parse_mode="HTML")
    await state.clear()


# ====================== LIST USERS ======================
@router.message(F.text == "📋 List users")
async def list_users(msg: types.Message):
    users = get_all_users() or []
    if not users:
        return await msg.answer("Нет пользователей")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{u.get('username')} | {u.get('status','—')}",
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
    await call.answer("✅ Отправлено")


# ====================== EXTEND ======================
@router.callback_query(F.data.startswith("extend:"))
async def extend_handler(call: types.CallbackQuery):
    _, tg_id_str, days_str = call.data.split(":")
    tg_id = int(tg_id_str)
    days = int(days_str)

    try:
        if days == 9999:
            user = extend_user(tg_id, 9999)
            await call.message.answer(f"✅ Бессрочный доступ выдан (TG: {tg_id})")
        else:
            user = extend_user(tg_id, days)
            await call.message.answer(f"✅ Продлено на {days} дней (TG: {tg_id})")
        full_sync()
    except Exception as e:
        await call.message.answer(f"❌ Ошибка: {e}")
    await call.answer()


# ====================== DELETE ======================
@router.callback_query(F.data.startswith("del:"))
async def delete_cb(call: types.CallbackQuery):
    tg_id = int(call.data.split(":")[1])
    if delete_user(tg_id):
        full_sync()
        await call.message.answer(f"✅ Удалён: user{tg_id}")
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