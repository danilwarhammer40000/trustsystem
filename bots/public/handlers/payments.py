from aiogram import Router, types

from services.payment_service import create_payment
from services.public_user_service import get_or_create

router = Router()

@router.message(lambda m: m.text in ["💳 30 дней", "💳 60 дней"])
async def buy(message: types.Message):

tg_id = message.from_user.id  

plan = "30" if "30" in message.text else "60"  

# создаём пользователя автоматически  
user = get_or_create(tg_id)  

payment = create_payment(plan, tg_id)  

await message.answer(  
    f"Оплата {payment['amount']} RUB\n\n{payment['url']}\n\n"  
    f"После оплаты доступ выдаётся автоматически"  
)
