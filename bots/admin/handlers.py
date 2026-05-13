from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from services.user_service import get_all_users, delete_user, create_user
from core.sync import full_sync
from services.vpn_card_builder import build_vpn_card

router = Router()

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
async def add_user_start(msg: types.Message):
    await msg.answer("Отправьте Telegram ID пользователя:")


# Обработка Telegram ID (только цифры)
@router.message(lambda message: message.text and message.text.strip().isdigit())
async def add_user_by_id(msg: types.Message):
    try:
        tg_id = int(msg.text.strip())
        user = create_user(tg_id)
        full_sync()
        await msg.answer(
            f"✅ Пользователь успешно создан!\n\n"
            f"ID: {tg_id}\n"
            f"Username: {user.get('username')}\n"
            f"Статус: {user.get('status')}"
        )
    except Exception as e:
        await msg.answer(f"❌ Ошибка при создании пользователя: {e}")


# ====================== LIST USERS ======================
@router.message(F.text == "📋 List users")
async def list_users(msg: types.Message):
    users = get_all_users() or []
    if not users:
        return await msg.answer("Нет пользователей")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{u.get('username')} | {u.get('status','—')}",
            callback_data=f"user:{u.get('telegram_id')}"
        )]
        for u in users if u.get('telegram_id')
    ])
    await msg.answer(f"📋 Пользователи: {len(users)} шт.", reply_markup=kb)


@router.callback_query(F.data.startswith("user:"))
async def user_card(call: types.CallbackQuery):
    tg_id = call.data.split(":")[1]
    card = build_vpn_card(tg_id)
    await call.message.answer(card.get("text", "Ошибка загрузки данных"))
    await call.answer()


# ====================== DELETE ======================
@router.message(F.text == "❌ Delete user")
async def delete_menu(msg: types.Message):
    users = get_all_users() or []
    if not users:
        return await msg.answer("Нет пользователей")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=u.get("username"),
            callback_data=f"del:{u.get('telegram_id')}"
        )]
        for u in users if u.get('telegram_id')
    ])
    await msg.answer("Выберите пользователя для удаления:", reply_markup=kb)


@router.callback_query(F.data.startswith("del:"))
async def delete_cb(call: types.CallbackQuery):
    try:
        tg_id = int(call.data.split(":")[1])
        if delete_user(tg_id):
            full_sync()
            await call.message.answer(f"✅ Удалён: user_{tg_id}")
        else:
            await call.message.answer("Пользователь не найден")
        await call.answer()
    except Exception as e:
        await call.answer("Ошибка", show_alert=True)


# ====================== SYNC ======================
@router.message(F.text == "🔄 Sync users")
async def sync_users(msg: types.Message):
    try:
        full_sync()
        await msg.answer("✅ Синхронизация выполнена")
    except Exception as e:
        await msg.answer(f"❌ Ошибка синхронизации: {e}")


# ====================== STATS ======================
@router.message(F.text == "📊 Stats")
async def stats(msg: types.Message):
    users = get_all_users() or []
    active = sum(1 for u in users if u.get("status") == "active")
    await msg.answer(f"📊 Статистика:\nАктивных: {active}\nВсего: {len(users)}")