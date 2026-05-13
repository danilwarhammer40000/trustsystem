from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from services.user_service import get_all_users, delete_user, create_user
from core.sync import full_sync
from services.vpn_card_builder import build_vpn_card

router = Router()

# ====================== MAIN MENU ======================
@router.message(F.text == "/start")
async def start(msg: types.Message):
    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="📋 List users")],
            [types.KeyboardButton(text="❌ Delete user")],
            [types.KeyboardButton(text="🔄 Sync users")],
            [types.KeyboardButton(text="📊 Stats")],
            [types.KeyboardButton(text="➕ Add user")]
        ],
        resize_keyboard=True
    )
    await msg.answer("⚙️ Admin Panel", reply_markup=kb)


# ====================== LIST USERS ======================
@router.message(F.text == "📋 List users")
async def list_users(msg: types.Message):
    users = get_all_users() or []
    if not users:
        return await msg.answer("Нет пользователей")

    buttons = [
        [InlineKeyboardButton(
            text=f"{u.get('username')} | {u.get('status')}",
            callback_data=f"user:{u.get('telegram_id')}"
        )]
        for u in users if u.get('telegram_id')
    ]

    await msg.answer("📋 Пользователи:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@router.callback_query(F.data.startswith("user:"))
async def show_user_card(call: types.CallbackQuery):
    tg_id = int(call.data.split(":")[1])
    card = build_vpn_card(str(tg_id))
    await call.message.answer(card.get("text", "Данные пользователя"))
    await call.answer()


# ====================== DELETE ======================
@router.message(F.text == "❌ Delete user")
async def delete_menu(msg: types.Message):
    users = get_all_users() or []
    if not users:
        return await msg.answer("Нет пользователей")

    buttons = [
        [InlineKeyboardButton(
            text=u.get("username"),
            callback_data=f"del:{u.get('telegram_id')}"
        )]
        for u in users if u.get('telegram_id')
    ]

    await msg.answer("Выберите пользователя для удаления:", 
                     reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@router.callback_query(F.data.startswith("del:"))
async def delete_confirm(call: types.CallbackQuery):
    tg_id = int(call.data.split(":")[1])
    if delete_user(tg_id):
        await full_sync()  # синхронно
        await call.message.answer(f"✅ Пользователь user_{tg_id} удалён")
    else:
        await call.message.answer("Не удалось удалить")
    await call.answer()


# ====================== SYNC ======================
@router.message(F.text == "🔄 Sync users")
async def sync_cmd(msg: types.Message):
    await msg.answer("Запуск синхронизации...")
    try:
        full_sync()
        await msg.answer("✅ Синхронизация завершена успешно")
    except Exception as e:
        await msg.answer(f"❌ Ошибка синхронизации: {e}")


# ====================== STATS ======================
@router.message(F.text == "📊 Stats")
async def stats(msg: types.Message):
    users = get_all_users() or []
    active = sum(1 for u in users if u.get("status") == "active")
    await msg.answer(
        f"📊 Статистика:\n"
        f"Активных: {active}\n"
        f"Всего: {len(users)}"
    )


# ====================== ADD USER (простой) ======================
@router.message(F.text == "➕ Add user")
async def add_user(msg: types.Message):
    await msg.answer("Отправьте Telegram ID пользователя для добавления:")
    # Можно позже добавить FSM, пока просто создаём заглушку
    # create_user(tg_id) — можно доработать