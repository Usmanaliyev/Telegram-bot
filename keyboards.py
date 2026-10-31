# ============================================================
#  7-DARS — Klaviaturalar endi BAZADAN kelgan dict'lar bilan ishlaydi.
#
#  MUHIM: bu fayl bazani BILMAYDI. Unga tayyor ma'lumot beriladi.
#  Shuning uchun bu yerda hech qanday `.objects.` yoki `await` yo'q.
# ============================================================

from aiogram.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from callbacks import (AdminCB, CartCB, CategoryCB, CourierCB, MenuCB,
                       OrderCB, ProductCB)
from services import narx

BTN_MENYU = "🍽 Menyu"
BTN_SAVAT = "🧺 Savat"
BTN_PROFIL = "👤 Profil"
BTN_BUYURTMALAR = "📦 Buyurtmalarim"
BTN_ADMIN = "⚙️ Admin panel"
BTN_KURYER = "🛵 Kuryer paneli"


def bosh_menyu(rol: str = "mijoz", savatda: int = 0) -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    savat_matni = f"{BTN_SAVAT} ({savatda})" if savatda else BTN_SAVAT
    kb.row(KeyboardButton(text=BTN_MENYU), KeyboardButton(text=savat_matni))
    kb.row(KeyboardButton(text=BTN_BUYURTMALAR), KeyboardButton(text=BTN_PROFIL))
    if rol == "kuryer":
        kb.row(KeyboardButton(text=BTN_KURYER))
    elif rol == "admin":
        kb.row(KeyboardButton(text=BTN_ADMIN), KeyboardButton(text=BTN_KURYER))
    return kb.as_markup(resize_keyboard=True)


def kategoriyalar(royxat: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for k in royxat:
        kb.button(text=k["toliq_nom"], callback_data=CategoryCB(category_id=k["id"]))
    kb.adjust(2)
    kb.row()
    kb.button(text="🧺 Savat", callback_data=MenuCB(action="cart"))
    return kb.as_markup()


def mahsulotlar(royxat: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for m in royxat:
        kb.button(text=f"{m['nom']} — {narx(m['narx'])}",
                  callback_data=ProductCB(action="open", product_id=m["id"]))
    kb.adjust(1)
    kb.row()
    kb.button(text="🔙 Kategoriyalar", callback_data=MenuCB(action="categories"))
    kb.button(text="🧺 Savat", callback_data=MenuCB(action="cart"))
    return kb.as_markup()


def mahsulot_kartasi(mahsulot_id: int, qty: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="➖", callback_data=ProductCB(action="dec", product_id=mahsulot_id, qty=qty))
    kb.button(text=f"{qty} ta", callback_data=MenuCB(action="noop"))
    kb.button(text="➕", callback_data=ProductCB(action="inc", product_id=mahsulot_id, qty=qty))
    kb.adjust(3)
    pastki = InlineKeyboardBuilder()
    pastki.button(text=f"🛒 Savatga qo'shish ({qty})",
                  callback_data=ProductCB(action="add", product_id=mahsulot_id, qty=qty))
    pastki.button(text="🔙 Orqaga", callback_data=MenuCB(action="categories"))
    pastki.adjust(1)
    kb.attach(pastki)
    return kb.as_markup()


def savat(elementlar: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for e in elementlar:
        kb.button(text="➖", callback_data=CartCB(action="dec", product_id=e["id"]))
        kb.button(text=f"{e['nom'][:14]} · {e['soni']}", callback_data=MenuCB(action="noop"))
        kb.button(text="➕", callback_data=CartCB(action="inc", product_id=e["id"]))
        kb.button(text="🗑", callback_data=CartCB(action="del", product_id=e["id"]))
    kb.adjust(4)
    pastki = InlineKeyboardBuilder()
    pastki.button(text="✅ Buyurtma berish", callback_data=CartCB(action="checkout"))
    pastki.button(text="🍽 Menyu", callback_data=MenuCB(action="categories"))
    pastki.button(text="🗑 Tozalash", callback_data=CartCB(action="clear"))
    pastki.adjust(1, 2)
    kb.attach(pastki)
    return kb.as_markup()


# ============================================================
#  10-DARS — admin klaviaturalari
# ============================================================


def admin_buyurtma_tugmalari(b: dict) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if b["holat"] == "yangi":
        kb.button(text="✅ Tasdiqlash", callback_data=AdminCB(action="tasdiq", order_id=b["id"]))
        kb.button(text="❌ Bekor qilish", callback_data=AdminCB(action="bekor", order_id=b["id"]))
    elif b["holat"] == "tasdiqlandi":
        kb.button(text="❌ Bekor qilish", callback_data=AdminCB(action="bekor", order_id=b["id"]))
    kb.button(text="🔄 Yangilash", callback_data=AdminCB(action="korish", order_id=b["id"]))
    kb.adjust(2)
    return kb.as_markup()


def admin_panel() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🆕 Yangi buyurtmalar", callback_data=AdminCB(action="royxat", value="yangi"))
    kb.button(text="📦 Barcha buyurtmalar", callback_data=AdminCB(action="royxat", value=""))
    kb.button(text="📊 Statistika", callback_data=AdminCB(action="statistika"))
    kb.adjust(1)
    return kb.as_markup()


def admin_royxat(buyurtmalar: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for b in buyurtmalar:
        kb.button(text=f"#{b['id']} • {b['holat_nomi']} • {narx(b['jami'])}",
                  callback_data=AdminCB(action="korish", order_id=b["id"]))
    kb.button(text="🔙 Admin panel", callback_data=AdminCB(action="panel"))
    kb.adjust(1)
    return kb.as_markup()


def kuryer_olish_tugmasi(buyurtma_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🛵 Men olaman", callback_data=CourierCB(action="olaman", order_id=buyurtma_id))
    return kb.as_markup()


def kuryer_royxat(buyurtmalar: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for b in buyurtmalar:
        kb.button(text=f"#{b['id']} • {narx(b['jami'])} • {b['manzil'][:20]}",
                  callback_data=CourierCB(action="korish", order_id=b["id"]))
    kb.adjust(1)
    return kb.as_markup()


def kuryer_buyurtma_tugmalari(b: dict) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if b["kuryer_id"] is None and b["holat"] == "tasdiqlandi":
        kb.button(text="🛵 Men olaman", callback_data=CourierCB(action="olaman", order_id=b["id"]))
    elif b["holat"] == "yolda":
        kb.button(text="📦 Yetkazdim", callback_data=CourierCB(action="yetkazdim", order_id=b["id"]))
    kb.button(text="📞 Mijozga qo'ng'iroq", url=f"tel:{b['telefon']}")
    kb.button(text="🔙 Ro'yxat", callback_data=CourierCB(action="bosh"))
    kb.adjust(1)
    return kb.as_markup()


def qabul_qilish_tugmasi(buyurtma_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Qabul qildim", callback_data=OrderCB(action="qabul", order_id=buyurtma_id))
    kb.adjust(1)
    return kb.as_markup()