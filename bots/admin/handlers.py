from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from services.user_service import get_all_users, delete_user
from core.sync import full_sync
from services.vpn_card_builder import build_vpn_card

router = Router()

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
    await msg.answer("📋 Пользователи:", reply_markup=kb)


@router.callback_query(F.data.startswith("user:"))
async def user_card(call: types.CallbackQuery):
    tg_id = call.data.split(":")[1]
    card = build_vpn_card(tg_id)
    await call.message.answer(card.get("text", "Ошибка"))
    await call.answer()


@router.message(F.text == "❌ Delete user")
async def delete_menu(msg: types.Message):
    users = get_all_users() or []
    if not users:
        return await msg.answer("Нет пользователей")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=u.get("username"), callback_data=f"del:{u.get('telegram_id')}")]
        for u in users if u.get('telegram_id')
    ])
    await msg.answer("Выберите для удаления:", reply_markup=kb)


@router.callback_query(F.data.startswith("del:"))
async def delete_cb(call: types.CallbackQuery):
    tg_id = int(call.data.split(":")[1])
    if delete_user(tg_id):
        full_sync()
        await call.message.answer(f"✅ Удалён: user_{tg_id}")
    else:
        await call.message.answer("Не найден")
    await call.answer()


@router.message(F.text == "🔄 Sync users")
async def sync_users(msg: types.Message):
    full_sync()
    await msg.answer("✅ Синхронизация выполнена")


@router.message(F.text == "📊 Stats")
async def stats(msg: types.Message):
    users = get_all_users() or []
    active = sum(1 for u in users if u.get("status") == "active")
    await msg.answer(f"📊 Статистика:\nАктивных: {active}\nВсего: {len(users)}")


@router.message(F.text == "➕ Add user")
async def add_user(msg: types.Message):
    await msg.answer("Отправьте Telegram ID пользователя:")