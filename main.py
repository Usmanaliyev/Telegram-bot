# # ============================================================
# #  2-DARS — Reply klaviatura va menyu
# #  Maqsad: pastda doimiy tugmalar chiqsin
# #
# #  YOZISH TARTIBI:
# #    1-bosqich: data.py faylini yozing (mahsulotlar ro'yxati)
# #    2-bosqich: bosh_menyu() funksiyasi — klaviatura yasaydi
# #    3-bosqich: start() da reply_markup=bosh_menyu() qo'shing
# #    4-bosqich: har bir tugma uchun handler yozing
# #
# #  YANGI TUSHUNCHA: F.text == "🍽 Menyu"  — tugma bosilganda
# #                   oddiy MATN keladi, shuni tutamiz.
# # ============================================================
#
# import asyncio
# import logging
# import os
#
# from aiogram import Bot, Dispatcher, F
# from aiogram.client.default import DefaultBotProperties
# from aiogram.enums import ParseMode
# from aiogram.filters import CommandStart
# from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup
# from aiogram.utils.keyboard import ReplyKeyboardBuilder
# from dotenv import load_dotenv
#
# from data import CATEGORIES, narx
#
# load_dotenv()
# logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
#
# dp = Dispatcher()
#
# BTN_MENYU = "🍽 Menyu"
# BTN_SAVAT = "🧺 Savat"
# BTN_PROFIL = "👤 Profil"
# BTN_YORDAM = "ℹ️ Yordam"
#
#
# # ---------- 2-bosqich ----------
# def bosh_menyu() -> ReplyKeyboardMarkup:
#     kb = ReplyKeyboardBuilder()
#     kb.row(KeyboardButton(text=BTN_MENYU), KeyboardButton(text=BTN_SAVAT))
#     kb.row(KeyboardButton(text=BTN_PROFIL), KeyboardButton(text=BTN_YORDAM))
#     return kb.as_markup(resize_keyboard=True, input_field_placeholder="Bo'limni tanlang…")
#
#
# # ---------- 3-bosqich ----------
# @dp.message(CommandStart())
# async def start(message: Message):
#     await message.answer(
#         f"Salom, <b>{message.from_user.full_name}</b>!\n\nQuyidagi menyudan tanlang 👇",
#         reply_markup=bosh_menyu(),
#     )
#
#
# # ---------- 4-bosqich ----------
# @dp.message(F.text == BTN_MENYU)
# async def menyu(message: Message):
#     qatorlar = []
#     for kalit, kategoriya in CATEGORIES.items():
#         qatorlar.append(f"\n<b>{kategoriya['nom']}</b>")
#         for m in kategoriya["mahsulotlar"]:
#             qatorlar.append(f"  • {m['nom']} — {narx(m['narx'])}")
#     await message.answer("\n".join(qatorlar))
#
#
# @dp.message(F.text == BTN_SAVAT)
# async def savat(message: Message):
#     await message.answer("🧺 Savatingiz bo'sh.\n\n<i>Savatni 4-darsda yozamiz.</i>")
#
#
# @dp.message(F.text == BTN_PROFIL)
# async def profil(message: Message):
#     u = message.from_user
#     await message.answer(
#         f"👤 <b>Profil</b>\n\n"
#         f"Ism: <b>{u.full_name}</b>\n"
#         f"Username: @{u.username or '—'}\n"
#         f"ID: <code>{u.id}</code>"
#         # f"Jami{ u }"
#     )
#
#
# @dp.message(F.text == BTN_YORDAM)
# async def yordam(message: Message):
#     await message.answer("Menyudan tanlang yoki /start yozing.")
#
#
# # Tanilmagan matn — ENG OXIRIDA
# @dp.message(F.text)
# async def boshqa(message: Message):
#     await message.answer("Tushunmadim. Menyudan tanlang 👇", reply_markup=bosh_menyu())
#
#
# async def main():
#     bot = Bot(token=os.getenv("BOT_TOKEN"),
#               default=DefaultBotProperties(parse_mode=ParseMode.HTML))
#     logging.info("Bot ishga tushdi: @%s", (await bot.get_me()).username)
#     await dp.start_polling(bot)
#
#
# if __name__ == "__main__":
#     asyncio.run(main())
















# 3 dars

# ============================================================
#  3-DARS — Inline klaviatura va callback
#  Maqsad: tugmalar bilan katalog aylansin, chat toza qolsin
#
#  YOZISH TARTIBI:
#    1-bosqich: kategoriyalar_kb()  -> inline tugmalar
#    2-bosqich: @dp.callback_query  -> tugma bosilishini tutish
#    3-bosqich: mahsulotlar_kb()    -> ichkariga kirish
#    4-bosqich: mahsulot_kb()       -> mahsulot kartasi + "Orqaga"
#
#  ENG MUHIM QOIDA: har bir callback handler oxirida
#                   await call.answer()  bo'lishi SHART.
#                   Unutsangiz — tugmada soat aylanaveradi.
# ============================================================
#
# import asyncio
# import logging
# import os
#
# from aiogram import Bot, Dispatcher, F
# from aiogram.client.default import DefaultBotProperties
# from aiogram.enums import ParseMode
# from aiogram.filters import Command, CommandStart
# from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
# from aiogram.utils.keyboard import InlineKeyboardBuilder
# from dotenv import load_dotenv
#
# from data import CATEGORIES, mahsulot_top, narx
#
# load_dotenv()
# logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
#
# dp = Dispatcher()
#
#
# # ---------- 1-bosqich ----------
# def kategoriyalar_kb() -> InlineKeyboardMarkup:
#     kb = InlineKeyboardBuilder()
#     for kalit, kategoriya in CATEGORIES.items():
#         # callback_data — tugma bosilganda bizga qaytadigan SATR (max 64 bayt)
#         kb.button(text=kategoriya["nom"], callback_data=f"kat:{kalit}")
#     kb.adjust(2)
#     return kb.as_markup()
#
#
# # ---------- 3-bosqich ----------
# def mahsulotlar_kb(kalit: str) -> InlineKeyboardMarkup:
#     kb = InlineKeyboardBuilder()
#     for m in CATEGORIES[kalit]["mahsulotlar"]:
#         kb.button(text=f"{m['nom']} — {narx(m['narx'])}", callback_data=f"mah:{m['id']}")
#     kb.adjust(1)
#     kb.row()
#     kb.button(text="🔙 Kategoriyalar", callback_data="orqaga")
#     return kb.as_markup()
#
#
# # ---------- 4-bosqich ----------
# def mahsulot_kb(kalit: str) -> InlineKeyboardMarkup:
#     kb = InlineKeyboardBuilder()
#     kb.button(text="🛒 Savatga qo'shish", callback_data="savatga")
#     kb.button(text="🔙 Orqaga", callback_data=f"kat:{kalit}")
#     kb.adjust(1)
#     return kb.as_markup()
#
#
# @dp.message(CommandStart())
# @dp.message(Command("menyu"))
# async def start(message: Message):
#     await message.answer("🍽 <b>Menyu</b>\n\nKategoriyani tanlang:", reply_markup=kategoriyalar_kb())
#
#
# # ---------- 2-bosqich ----------
# @dp.callback_query(F.data == "orqaga")
# async def orqaga(call: CallbackQuery):
#     # edit_text — YANGI xabar yubormaydi, borini o'zgartiradi. Chat toza qoladi.
#     await call.message.edit_text("🍽 <b>Menyu</b>\n\nKategoriyani tanlang:",
#                                  reply_markup=kategoriyalar_kb())
#     await call.answer()
#
#
# @dp.callback_query(F.data.startswith("kat:"))
# async def kategoriya(call: CallbackQuery):
#     kalit = call.data.split(":")[1]        # "kat:burger" -> "burger"
#     kategoriya = CATEGORIES.get(kalit)
#     if not kategoriya:
#         return await call.answer("Bunday kategoriya yo'q", show_alert=True)
#
#     await call.message.edit_text(f"<b>{kategoriya['nom']}</b>\n\nMahsulotni tanlang:",
#                                  reply_markup=mahsulotlar_kb(kalit))
#     await call.answer()
#
#
# @dp.callback_query(F.data.startswith("mah:"))
# async def mahsulot(call: CallbackQuery):
#     mahsulot_id = int(call.data.split(":")[1])
#     m = mahsulot_top(mahsulot_id)
#     if not m:
#         return await call.answer("Mahsulot topilmadi", show_alert=True)
#
#     # mahsulot qaysi kategoriyada ekanini topamiz (orqaga qaytish uchun)
#     kalit = next(k for k, v in CATEGORIES.items()
#                  if any(x["id"] == mahsulot_id for x in v["mahsulotlar"]))
#
#     await call.message.edit_text(
#         f"<b>{m['nom']}</b>\n\n{m['tavsif']}\n\n💰 Narxi: <b>{narx(m['narx'])}</b>",
#         reply_markup=mahsulot_kb(kalit),
#     )
#     await call.answer()
#
#
# @dp.callback_query(F.data == "savatga")
# async def savatga(call: CallbackQuery):
#     # show_alert=True — o'rtada oyna chiqadi. False bo'lsa — yuqorida kichik yozuv.
#     await call.answer("✅ Savatga qo'shildi!\n\n(Savatni 4-darsda yozamiz)", show_alert=True)
#
#
# async def main():
#     bot = Bot(token=os.getenv("BOT_TOKEN"),
#               default=DefaultBotProperties(parse_mode=ParseMode.HTML))
#     logging.info("Bot ishga tushdi: @%s", (await bot.get_me()).username)
#     await dp.start_polling(bot)
#
#
# if __name__ == "__main__":
#     asyncio.run(main())








# 4dars
#  ============================================================
#  4-DARS — Strukturaga bo'lish + CallbackData factory + savat
#
#  NIMA O'ZGARDI (3-darsga nisbatan):
#    - Bitta main.py o'rniga 7 ta fayl
#    - callback_data satri o'rniga TIPLI CallbackData
#    - Ishlaydigan savat (hozircha xotirada)
#
#  FAYLLAR VAZIFASI:
#    data.py       — mahsulotlar (keyin Django modeli bo'ladi)
#    storage.py    — savat (keyin Django modeli bo'ladi)
#    callbacks.py  — tugma "manzillari"
#    keyboards.py  — barcha tugmalar
#    handlers/     — mantiq, mavzu bo'yicha bo'lingan
#    main.py       — faqat yig'ish va ishga tushirish
#
#  ISHGA TUSHIRISH:  python main.py
# ============================================================

# import asyncio
# import logging
# import os
#
# from aiogram import Bot, Dispatcher
# from aiogram.client.default import DefaultBotProperties
# from aiogram.enums import ParseMode
# from dotenv import load_dotenv
#
# from handlers import register
#
# load_dotenv()
# logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
#
#
# async def main():
#     bot = Bot(token=os.getenv("BOT_TOKEN"),
#               default=DefaultBotProperties(parse_mode=ParseMode.HTML))
#     dp = Dispatcher()
#     register(dp)
#
#     logging.info("Bot ishga tushdi: @%s", (await bot.get_me()).username)
#     await dp.start_polling(bot)
#
#
# if __name__ == "__main__":
#     asyncio.run(main())



# 5dars
# ============================================================
#  5-DARS — FSM: buyurtma rasmiylashtirish
#
#  NIMA O'ZGARDI (3-darsga nisbatan):
#    - Bitta main.py o'rniga 7 ta fayl
#    - callback_data satri o'rniga TIPLI CallbackData
#    - Ishlaydigan savat (hozircha xotirada)
#
#  FAYLLAR VAZIFASI:
#    data.py       — mahsulotlar (keyin Django modeli bo'ladi)
#    storage.py    — savat (keyin Django modeli bo'ladi)
#    callbacks.py  — tugma "manzillari"
#    keyboards.py  — barcha tugmalar
#    handlers/     — mantiq, mavzu bo'yicha bo'lingan
#    main.py       — faqat yig'ish va ishga tushirish
#
#  ISHGA TUSHIRISH:  python main.py
# ============================================================

# import asyncio
# import logging
# import os
#
# from aiogram import Bot, Dispatcher
# from aiogram.client.default import DefaultBotProperties
# from aiogram.enums import ParseMode
# from dotenv import load_dotenv
#
# from handlers import register
#
# load_dotenv()
# logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
#
#
# async def main():
#     bot = Bot(token=os.getenv("BOT_TOKEN"),
#               default=DefaultBotProperties(parse_mode=ParseMode.HTML))
#     dp = Dispatcher()
#     register(dp)
#
#     logging.info("Bot ishga tushdi: @%s", (await bot.get_me()).username)
#     await dp.start_polling(bot)
#
#
# if __name__ == "__main__":
#     asyncio.run(main())


# 6dars
# ============================================================
#  5-DARS — FSM: buyurtma rasmiylashtirish
#
#  NIMA O'ZGARDI (3-darsga nisbatan):
#    - Bitta main.py o'rniga 7 ta fayl
#    - callback_data satri o'rniga TIPLI CallbackData
#    - Ishlaydigan savat (hozircha xotirada)
#
#  FAYLLAR VAZIFASI:
#    data.py       — mahsulotlar (keyin Django modeli bo'ladi)
#    storage.py    — savat (keyin Django modeli bo'ladi)
#    callbacks.py  — tugma "manzillari"
#    keyboards.py  — barcha tugmalar
#    handlers/     — mantiq, mavzu bo'yicha bo'lingan
#    main.py       — faqat yig'ish va ishga tushirish
#
#  ISHGA TUSHIRISH:  python main.py
# ============================================================

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv

from handlers import register

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


async def main():
    bot = Bot(token=os.getenv("BOT_TOKEN"),
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    register(dp)

    logging.info("Bot ishga tushdi: @%s", (await bot.get_me()).username)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())