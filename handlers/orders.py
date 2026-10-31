from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery

import events
import services
from callbacks import OrderCB

router = Router(name="orders")


@router.callback_query(OrderCB.filter(F.action == "qabul"))
async def qabul_qildim(call: CallbackQuery, callback_data: OrderCB, user: dict, bot: Bot):
    b = await services.mijoz_qabul_qildi(callback_data.order_id, user["telegram_id"])
    if not b:
        return await call.answer("Bu buyurtmani hozir tasdiqlab bo'lmaydi.", show_alert=True)

    await call.message.edit_text(
        f"🎉 <b>Rahmat!</b>\n\nBuyurtma #{b['id']} yakunlandi.\n"
        f"Yana buyurtma berishni kutamiz! 🍽"
    )
    await call.answer("🎉 Rahmat!")
    await events.on_mijoz_qabul_qildi(bot, b)