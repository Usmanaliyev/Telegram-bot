from aiogram import Bot, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import events
import keyboards as kb
import services
from callbacks import AdminCB
from filters import IsAdmin
from shop.models import OrderStatus
from states import AdminCancel

router = Router(name="admin")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


@router.message(Command("admin"), StateFilter(None))
@router.message(F.text == kb.BTN_ADMIN, StateFilter(None))
async def panel(message: Message):
    await message.answer("⚙️ <b>Admin panel</b>\n\nBo'limni tanlang:",
                         reply_markup=kb.admin_panel())


@router.callback_query(AdminCB.filter(F.action == "panel"))
async def panel_cb(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("⚙️ <b>Admin panel</b>\n\nBo'limni tanlang:",
                                 reply_markup=kb.admin_panel())
    await call.answer()


@router.callback_query(AdminCB.filter(F.action == "royxat"))
async def royxat(call: CallbackQuery, callback_data: AdminCB):
    holat = callback_data.value or None
    buyurtmalar = await services.buyurtmalar_royxati(holat)
    if not buyurtmalar:
        await call.message.edit_text("📭 Bu holatda buyurtma yo'q.",
                                     reply_markup=kb.admin_panel())
        return await call.answer()
    sarlavha = "🆕 <b>Yangi buyurtmalar</b>" if holat else "📦 <b>Barcha buyurtmalar</b>"
    await call.message.edit_text(f"{sarlavha} ({len(buyurtmalar)} ta)",
                                 reply_markup=kb.admin_royxat(buyurtmalar))
    await call.answer()


@router.callback_query(AdminCB.filter(F.action == "korish"))
async def korish(call: CallbackQuery, callback_data: AdminCB):
    b = await services.buyurtma_olish(callback_data.order_id)
    if not b:
        return await call.answer("Buyurtma topilmadi", show_alert=True)
    matn = events.buyurtma_matni(b, f"🧾 <b>Buyurtma #{b['id']}</b> — {b['holat_nomi']}")
    await call.message.edit_text(matn, reply_markup=kb.admin_buyurtma_tugmalari(b))
    await call.answer()


@router.callback_query(AdminCB.filter(F.action == "tasdiq"))
async def tasdiq(call: CallbackQuery, callback_data: AdminCB, user: dict, bot: Bot):
    b = await services.buyurtma_olish(callback_data.order_id)
    if not b or b["holat"] != OrderStatus.YANGI:
        return await call.answer("Bu buyurtma allaqachon ko'rib chiqilgan.", show_alert=True)

    b = await services.holat_ozgartirish(
        callback_data.order_id, OrderStatus.TASDIQLANDI,
        user["telegram_id"], "Admin tasdiqladi")

    matn = events.buyurtma_matni(b, f"🧾 <b>Buyurtma #{b['id']}</b> — {b['holat_nomi']}")
    await call.message.edit_text(matn, reply_markup=kb.admin_buyurtma_tugmalari(b))
    await call.answer(f"✅ #{b['id']} tasdiqlandi", show_alert=True)
    await events.on_tasdiqlandi(bot, b)


@router.callback_query(AdminCB.filter(F.action == "bekor"))
async def bekor_sorash(call: CallbackQuery, callback_data: AdminCB, state: FSMContext):
    b = await services.buyurtma_olish(callback_data.order_id)
    if not b or b["holat"] in (OrderStatus.BEKOR, OrderStatus.YAKUNLANDI):
        return await call.answer("Bu buyurtmani bekor qilib bo'lmaydi.", show_alert=True)
    await state.set_state(AdminCancel.sabab)
    await state.update_data(order_id=callback_data.order_id)
    await call.message.answer("✍️ Bekor qilish sababini yozing:")
    await call.answer()


@router.message(AdminCancel.sabab, F.text)
async def bekor_qilish(message: Message, state: FSMContext, user: dict, bot: Bot):
    data = await state.get_data()
    await state.clear()
    sabab = (message.text or "").strip()[:255]

    b = await services.holat_ozgartirish(
        data.get("order_id"), OrderStatus.BEKOR, user["telegram_id"], sabab)
    if not b:
        return await message.answer("⚠️ Buyurtma topilmadi.")

    await message.answer(f"❌ Buyurtma #{b['id']} bekor qilindi.")
    await events.on_bekor_qilindi(bot, b, sabab)


@router.callback_query(AdminCB.filter(F.action == "statistika"))
async def statistika(call: CallbackQuery):
    st = await services.admin_statistika()
    await call.message.edit_text(
        "📊 <b>Statistika</b>\n\n"
        f"🆕 Yangi: <b>{st['yangi']}</b>\n"
        f"📦 Jami buyurtmalar: <b>{st['jami']}</b>\n"
        f"👥 Mijozlar: <b>{st['mijozlar']}</b>\n"
        f"🛵 Kuryerlar: <b>{st['kuryerlar']}</b>",
        reply_markup=kb.admin_panel(),
    )
    await call.answer()