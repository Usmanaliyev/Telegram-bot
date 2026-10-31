from aiogram import Bot, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.types import CallbackQuery, KeyboardButton, Message, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

import events
import keyboards as kb
import services
from callbacks import CourierCB
from filters import IsCourier

router = Router(name="courier")
router.message.filter(IsCourier())
router.callback_query.filter(IsCourier())

BTN_SMENA_ON = "🟢 Smenani boshlash"
BTN_SMENA_OFF = "🔴 Smenani tugatish"
BTN_BOSH = "📋 Bo'sh buyurtmalar"
BTN_MENING = "🛵 Mening buyurtmalarim"
BTN_STAT = "📊 Statistikam"
BTN_ORQAGA = "🔙 Asosiy menyu"


def kuryer_menyu(smenada: bool) -> ReplyKeyboardMarkup:
    k = ReplyKeyboardBuilder()
    k.row(KeyboardButton(text=BTN_BOSH), KeyboardButton(text=BTN_MENING))
    k.row(KeyboardButton(text=BTN_SMENA_OFF if smenada else BTN_SMENA_ON))
    k.row(KeyboardButton(text=BTN_STAT), KeyboardButton(text=BTN_ORQAGA))
    return k.as_markup(resize_keyboard=True)


@router.message(Command("kuryer"), StateFilter(None))
@router.message(F.text == kb.BTN_KURYER, StateFilter(None))
async def panel(message: Message, user: dict):
    await message.answer(
        f"🛵 <b>Kuryer paneli</b>\n\nSmena: <b>{'🟢 ochiq' if user['smenada'] else '🔴 yopiq'}</b>",
        reply_markup=kuryer_menyu(user["smenada"]),
    )


@router.message(F.text.in_({BTN_SMENA_ON, BTN_SMENA_OFF}), StateFilter(None))
async def smena(message: Message, user: dict):
    smenada = await services.smena_almashtirish(user["telegram_id"])
    await message.answer(
        "🟢 Smena boshlandi. Yangi buyurtmalar sizga yuboriladi."
        if smenada else "🔴 Smena tugadi.",
        reply_markup=kuryer_menyu(smenada),
    )


@router.message(F.text == BTN_BOSH, StateFilter(None))
async def bosh_buyurtmalar(message: Message):
    royxat = await services.bosh_buyurtmalar()
    if not royxat:
        return await message.answer("📭 Hozircha bo'sh buyurtma yo'q.")
    await message.answer(f"📋 <b>Bo'sh buyurtmalar</b> ({len(royxat)} ta)",
                         reply_markup=kb.kuryer_royxat(royxat))


@router.callback_query(CourierCB.filter(F.action == "bosh"))
async def bosh_cb(call: CallbackQuery):
    royxat = await services.bosh_buyurtmalar()
    if not royxat:
        await call.message.edit_text("📭 Hozircha bo'sh buyurtma yo'q.")
    else:
        await call.message.edit_text(f"📋 <b>Bo'sh buyurtmalar</b> ({len(royxat)} ta)",
                                     reply_markup=kb.kuryer_royxat(royxat))
    await call.answer()


@router.message(F.text == BTN_MENING, StateFilter(None))
async def mening(message: Message, user: dict):
    royxat = await services.kuryer_buyurtmalari(user["telegram_id"])
    if not royxat:
        return await message.answer("📭 Sizda faol buyurtma yo'q.")
    for b in royxat:
        matn = events.buyurtma_matni(b, f"🧾 <b>Buyurtma #{b['id']}</b> — {b['holat_nomi']}")
        await message.answer(matn, reply_markup=kb.kuryer_buyurtma_tugmalari(b))


@router.message(F.text == BTN_STAT, StateFilter(None))
async def statistika(message: Message, user: dict):
    st = await services.kuryer_statistikasi(user["telegram_id"])
    await message.answer(
        "📊 <b>Kuryer statistikasi</b>\n\n"
        f"🎉 Yakunlangan: <b>{st['yakunlangan']}</b>\n"
        f"🛵 Faol: <b>{st['faol']}</b>\n"
        f"📦 Jami: <b>{st['jami']}</b>"
    )


@router.callback_query(CourierCB.filter(F.action == "korish"))
async def korish(call: CallbackQuery, callback_data: CourierCB):
    b = await services.buyurtma_olish(callback_data.order_id)
    if not b:
        return await call.answer("Buyurtma topilmadi", show_alert=True)
    matn = events.buyurtma_matni(b, f"🧾 <b>Buyurtma #{b['id']}</b> — {b['holat_nomi']}")
    await call.message.edit_text(matn, reply_markup=kb.kuryer_buyurtma_tugmalari(b))
    await call.answer()


@router.callback_query(CourierCB.filter(F.action == "olaman"))
async def olaman(call: CallbackQuery, callback_data: CourierCB, user: dict, bot: Bot):
    b, natija = await services.kuryer_olish(callback_data.order_id, user["telegram_id"])

    if natija == "band":
        await call.answer(f"⚠️ Buyurtma #{callback_data.order_id} allaqachon band.",
                          show_alert=True)
        return
    if not b:
        return await call.answer("Xatolik yuz berdi", show_alert=True)

    matn = events.buyurtma_matni(b, f"🧾 <b>Buyurtma #{b['id']}</b> — {b['holat_nomi']}")
    await call.message.edit_text(matn, reply_markup=kb.kuryer_buyurtma_tugmalari(b))
    await call.answer(f"✅ Buyurtma #{b['id']} sizga biriktirildi!", show_alert=True)
    await events.on_kuryer_oldi(bot, b)


@router.callback_query(CourierCB.filter(F.action == "yetkazdim"))
async def yetkazdim(call: CallbackQuery, callback_data: CourierCB, user: dict, bot: Bot):
    b = await services.kuryer_yetkazdi(callback_data.order_id, user["telegram_id"])
    if not b:
        return await call.answer("Bu buyurtmani yopib bo'lmaydi.", show_alert=True)

    matn = events.buyurtma_matni(b, f"🧾 <b>Buyurtma #{b['id']}</b> — {b['holat_nomi']}")
    await call.message.edit_text(matn)
    await call.answer(f"📦 #{b['id']} yetkazildi. Mijoz tasdig'ini kutamiz.", show_alert=True)
    await events.on_kuryer_yetkazdi(bot, b)


@router.message(F.text == BTN_ORQAGA, StateFilter(None))
async def orqaga(message: Message, user: dict):
    dona = await services.savat_dona(user["telegram_id"])
    await message.answer("🏠 Asosiy menyu",
                         reply_markup=kb.bosh_menyu(user["rol"], dona))