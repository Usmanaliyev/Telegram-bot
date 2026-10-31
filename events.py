"""Rollar bir-biriga qanday xabar berishi — hammasi shu yerda.

Handler faqat "nima bo'ldi" ni biladi, "kimga xabar berish" ni emas.
"""
from aiogram import Bot

import keyboards as kb
import services
from notify import fan_out, safe_send


def buyurtma_matni(b: dict, sarlavha: str) -> str:
    qatorlar = "\n".join(
        f"{i}. {e['nom']} — {e['soni']} x {services.narx(e['narx'])}"
        for i, e in enumerate(b["elementlar"], 1))
    return (
        f"{sarlavha}\n\n{qatorlar}\n\n"
        f"➖➖➖➖➖➖➖➖\n"
        f"💳 Jami: <b>{services.narx(b['jami'])}</b> ({b['tolov']})\n\n"
        f"👤 {b['ism']}\n📱 {b['telefon']}\n📍 {b['manzil']}"
    )


async def on_buyurtma_yaratildi(bot: Bot, b: dict) -> None:
    matn = buyurtma_matni(b, f"🔔 <b>YANGI BUYURTMA #{b['id']}</b>")
    for admin_id in await services.admin_idlar():
        await safe_send(bot, admin_id, matn, kb.admin_buyurtma_tugmalari(b))


async def on_tasdiqlandi(bot: Bot, b: dict) -> None:
    await safe_send(bot, b["mijoz_id"],
                    f"✅ <b>Buyurtmangiz #{b['id']} tasdiqlandi!</b>\n\n"
                    f"Tez orada kuryer yo'lga chiqadi. 🛵")

    kuryerlar = await services.kuryer_idlar(faqat_smenada=True)
    if not kuryerlar:
        kuryerlar = await services.kuryer_idlar(faqat_smenada=False)
    if kuryerlar:
        matn = buyurtma_matni(b, f"🆕 <b>Yangi buyurtma #{b['id']}</b>")
        await fan_out(bot, kuryerlar, matn, kb.kuryer_olish_tugmasi(b["id"]))


async def on_bekor_qilindi(bot: Bot, b: dict, sabab: str = "") -> None:
    qoshimcha = f"\n\nSabab: <i>{sabab}</i>" if sabab else ""
    await safe_send(bot, b["mijoz_id"],
                    f"❌ <b>Buyurtma #{b['id']} bekor qilindi.</b>{qoshimcha}")
    if b.get("kuryer_id"):
        await safe_send(bot, b["kuryer_id"], f"❌ Buyurtma #{b['id']} bekor qilindi.")


async def on_kuryer_oldi(bot: Bot, b: dict) -> None:
    await safe_send(bot, b["mijoz_id"],
                    f"🛵 <b>Buyurtma #{b['id']} yo'lga chiqdi!</b>\n\n"
                    f"Kuryer: <b>{b['kuryer_ismi']}</b>")
    for admin_id in await services.admin_idlar():
        await safe_send(bot, admin_id, f"🛵 #{b['id']} — {b['kuryer_ismi']} oldi.")


async def on_kuryer_yetkazdi(bot: Bot, b: dict) -> None:
    await safe_send(bot, b["mijoz_id"],
                    f"📦 <b>Buyurtma #{b['id']} yetkazildi!</b>\n\n"
                    f"Iltimos, olganingizni tasdiqlang 👇",
                    kb.qabul_qilish_tugmasi(b["id"]))


async def on_mijoz_qabul_qildi(bot: Bot, b: dict) -> None:
    if b.get("kuryer_id"):
        await safe_send(bot, b["kuryer_id"], f"🎉 #{b['id']} mijoz tomonidan tasdiqlandi.")
    for admin_id in await services.admin_idlar():
        await safe_send(bot, admin_id,
                        f"🎉 #{b['id']} yakunlandi — {services.narx(b['jami'])}")