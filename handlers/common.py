from aiogram import F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.types import Message

import keyboards as kb
import services

router = Router(name="common")


@router.message(CommandStart())
async def start(message: Message, user: dict):
    dona = await services.savat_dona(user["telegram_id"])
    await message.answer(
        f"Salom, <b>{user['ism']}</b>!\n\nMenyudan tanlang 👇",
        reply_markup=kb.bosh_menyu(user["rol"], dona),
    )


@router.message(Command("menyu"))
@router.message(F.text == kb.BTN_MENYU)
async def menyu(message: Message):
    royxat = await services.kategoriyalar()
    if not royxat:
        return await message.answer("😕 Hozircha katalog bo'sh.")
    await message.answer("🍽 <b>Menyu</b>\n\nKategoriyani tanlang:",
                         reply_markup=kb.kategoriyalar(royxat))


@router.message(Command("buyurtmalarim"))
@router.message(F.text == kb.BTN_BUYURTMALAR)
async def buyurtmalarim(message: Message, user: dict):
    royxat = await services.buyurtmalarim(user["telegram_id"])
    if not royxat:
        return await message.answer("📦 Sizda hali buyurtma yo'q.")

    qismlar = []
    for b in royxat:
        elementlar = "\n".join(f"    • {e['nom']} x{e['soni']}" for e in b["elementlar"])
        qismlar.append(
            f"🧾 <b>#{b['id']}</b> — {b['holat']}\n{b['sana']}\n{elementlar}\n"
            f"    💳 <b>{services.narx(b['jami'])}</b>")
    await message.answer("📦 <b>Buyurtmalarim</b>\n\n" + "\n\n".join(qismlar))


@router.message(F.text == kb.BTN_PROFIL)
async def profil(message: Message, user: dict):
    dona = await services.savat_dona(user["telegram_id"])
    rollar = {"mijoz": "Mijoz", "kuryer": "Kuryer", "admin": "Admin"}
    await message.answer(
        f"👤 <b>Profil</b>\n\nIsm: <b>{user['ism']}</b>\n"
        f"Telefon: <b>{user['telefon'] or '—'}</b>\n"
        f"Rol: <b>{rollar.get(user['rol'], user['rol'])}</b>\n"
        f"ID: <code>{user['telegram_id']}</code>\nSavatda: <b>{dona}</b> dona"
    )


@router.message(F.text, StateFilter(None))
async def boshqa(message: Message, user: dict):
    dona = await services.savat_dona(user["telegram_id"])
    await message.answer("Menyudan tanlang 👇",
                         reply_markup=kb.bosh_menyu(user["rol"], dona))