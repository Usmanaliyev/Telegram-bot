# ============================================================
#  7-DARS — SERVIS QATLAMI
#
#  Bu — bot bilan baza orasidagi YAGONA ko'prik.
#  Handler hech qachon to'g'ridan-to'g'ri Product.objects ga tegmaydi.
#
#  IKKI QOIDA:
#   1. Har bir funksiya @sync_to_async bilan o'ralgan
#   2. Har bir funksiya dict qaytaradi, model obyektini EMAS
# ============================================================

from asgiref.sync import sync_to_async

from shop.models import Category, Product


def narx(son) -> str:
    """Decimal(32000) -> '32 000 so'm'"""
    return f"{int(son):,}".replace(",", " ") + " so'm"


def _kategoriya_dict(k: Category) -> dict:
    return {"id": k.pk, "nom": k.nom, "emoji": k.emoji,
            "toliq_nom": f"{k.emoji} {k.nom}".strip()}


def _mahsulot_dict(m: Product) -> dict:
    return {"id": m.pk, "nom": m.nom, "tavsif": m.tavsif,
            "narx": int(m.narx), "kategoriya_id": m.kategoriya_id}


@sync_to_async
def kategoriyalar() -> list[dict]:
    """Faqat ichida mahsuloti bor kategoriyalar."""
    qs = Category.objects.filter(faol=True, mahsulotlar__faol=True).distinct()
    return [_kategoriya_dict(k) for k in qs]


@sync_to_async
def kategoriya_top(kategoriya_id: int) -> dict | None:
    k = Category.objects.filter(pk=kategoriya_id, faol=True).first()
    return _kategoriya_dict(k) if k else None


@sync_to_async
def mahsulotlar(kategoriya_id: int) -> list[dict]:
    qs = Product.objects.filter(kategoriya_id=kategoriya_id, faol=True)
    return [_mahsulot_dict(m) for m in qs]


@sync_to_async
def mahsulot_top(mahsulot_id: int) -> dict | None:
    m = Product.objects.filter(pk=mahsulot_id, faol=True).first()
    return _mahsulot_dict(m) if m else None


@sync_to_async
def mahsulotlar_by_ids(idlar: list[int]) -> dict[int, dict]:
    """Savat uchun: {id: mahsulot_dict} ko'rinishida qaytaradi."""
    qs = Product.objects.filter(pk__in=idlar, faol=True)
    return {m.pk: _mahsulot_dict(m) for m in qs}


# ============================================================
#  8-DARS — Foydalanuvchi, savat va buyurtma servislari
# ============================================================

from decimal import Decimal

from django.db import transaction
from django.db.models import F

from shop.models import Cart, CartItem, Order, OrderItem, OrderStatus, TgUser


def _user_dict(u: TgUser) -> dict:
    return {"id": u.pk, "telegram_id": u.telegram_id, "ism": u.ism,
            "telefon": u.telefon, "rol": u.rol,
            "bloklangan": u.bloklangan, "smenada": u.smenada}


@sync_to_async
def user_olish(telegram_id: int, ism: str) -> dict:
    from django.conf import settings
    from shop.models import Role

    rol = Role.ADMIN if telegram_id in settings.ADMIN_IDS else Role.MIJOZ
    user, _ = TgUser.objects.get_or_create(
        telegram_id=telegram_id, defaults={"ism": ism[:255], "rol": rol})

    # .env dagi ADMIN_IDS har doim adminlikni kafolatlaydi
    if telegram_id in settings.ADMIN_IDS and user.rol != Role.ADMIN:
        user.rol = Role.ADMIN
        user.save(update_fields=["rol"])

    Cart.objects.get_or_create(user=user)
    return _user_dict(user)


@sync_to_async
def smena_almashtirish(telegram_id: int) -> bool:
    user = TgUser.objects.filter(telegram_id=telegram_id).first()
    if not user:
        return False
    user.smenada = not user.smenada
    user.save(update_fields=["smenada"])
    return user.smenada


def _savat(telegram_id: int) -> Cart | None:
    user = TgUser.objects.filter(telegram_id=telegram_id).first()
    if not user:
        return None
    savat, _ = Cart.objects.get_or_create(user=user)
    return savat


@sync_to_async
def savatga_qoshish(telegram_id: int, mahsulot_id: int, soni: int = 1) -> int:
    savat = _savat(telegram_id)
    if not savat or soni < 1:
        return 0
    if not Product.objects.filter(pk=mahsulot_id, faol=True).exists():
        return 0
    with transaction.atomic():
        element, yangi = CartItem.objects.get_or_create(
            savat=savat, mahsulot_id=mahsulot_id, defaults={"soni": soni})
        if not yangi:
            # F() — ikki tugma bir vaqtda bosilsa ham son to'g'ri qoladi
            CartItem.objects.filter(pk=element.pk).update(soni=F("soni") + soni)
            element.refresh_from_db(fields=["soni"])
    return element.soni


@sync_to_async
def savat_ozgartirish(telegram_id: int, mahsulot_id: int, farq: int) -> int:
    savat = _savat(telegram_id)
    if not savat:
        return 0
    element = CartItem.objects.filter(savat=savat, mahsulot_id=mahsulot_id).first()
    if not element:
        return 0
    yangi = element.soni + farq
    if yangi < 1:
        element.delete()
        return 0
    element.soni = yangi
    element.save(update_fields=["soni"])
    return yangi


@sync_to_async
def savatdan_ochirish(telegram_id: int, mahsulot_id: int) -> None:
    savat = _savat(telegram_id)
    if savat:
        CartItem.objects.filter(savat=savat, mahsulot_id=mahsulot_id).delete()


@sync_to_async
def savat_tozalash(telegram_id: int) -> None:
    savat = _savat(telegram_id)
    if savat:
        CartItem.objects.filter(savat=savat).delete()


@sync_to_async
def savat_olish(telegram_id: int) -> list[dict]:
    """To'liq savat — bitta so'rov bilan, mahsulot ma'lumoti qo'shilgan."""
    savat = _savat(telegram_id)
    if not savat:
        return []
    qatorlar = CartItem.objects.filter(savat=savat).select_related("mahsulot")
    return [
        {"id": q.mahsulot_id, "nom": q.mahsulot.nom, "narx": int(q.mahsulot.narx),
         "soni": q.soni, "summa": int(q.mahsulot.narx) * q.soni}
        for q in qatorlar
    ]


@sync_to_async
def savat_dona(telegram_id: int) -> int:
    savat = _savat(telegram_id)
    if not savat:
        return 0
    return sum(CartItem.objects.filter(savat=savat).values_list("soni", flat=True))


@sync_to_async
def mahsulot_soni_savatda(telegram_id: int, mahsulot_id: int) -> int:
    savat = _savat(telegram_id)
    if not savat:
        return 0
    return (CartItem.objects.filter(savat=savat, mahsulot_id=mahsulot_id)
            .values_list("soni", flat=True).first() or 0)


@sync_to_async
def buyurtma_yaratish(telegram_id: int, ism: str, telefon: str,
                      manzil: str, tolov: str) -> dict | None:
    """Savatni buyurtmaga aylantiradi va savatni tozalaydi."""
    user = TgUser.objects.filter(telegram_id=telegram_id).first()
    if not user:
        return None
    savat, _ = Cart.objects.get_or_create(user=user)
    qatorlar = list(CartItem.objects.filter(savat=savat).select_related("mahsulot"))
    if not qatorlar:
        return None

    jami = sum((q.mahsulot.narx * q.soni for q in qatorlar), Decimal("0"))

    with transaction.atomic():
        buyurtma = Order.objects.create(
            user=user, ism=ism[:255], telefon=telefon[:32],
            manzil=manzil[:255], tolov=tolov, jami=jami)
        OrderItem.objects.bulk_create([
            OrderItem(buyurtma=buyurtma, mahsulot=q.mahsulot,
                      mahsulot_nomi=q.mahsulot.nom,   # ← NUSXA
                      narx=q.mahsulot.narx,           # ← NUSXA
                      soni=q.soni)
            for q in qatorlar
        ])
        user.ism, user.telefon = ism[:255], telefon[:32]
        user.save(update_fields=["ism", "telefon"])
        CartItem.objects.filter(savat=savat).delete()

    return {"id": buyurtma.pk, "jami": int(jami),
            "elementlar": [{"nom": q.mahsulot.nom, "soni": q.soni,
                            "narx": int(q.mahsulot.narx)} for q in qatorlar]}


@sync_to_async
def buyurtmalarim(telegram_id: int, limit: int = 10) -> list[dict]:
    qs = (Order.objects.filter(user__telegram_id=telegram_id)
          .prefetch_related("elementlar")[:limit])
    return [
        {"id": o.pk, "holat": o.get_holat_display(), "jami": int(o.jami),
         "sana": o.yaratilgan.strftime("%d.%m.%Y %H:%M"),
         "elementlar": [{"nom": e.mahsulot_nomi, "soni": e.soni, "narx": int(e.narx)}
                        for e in o.elementlar.all()]}
        for o in qs
    ]


@sync_to_async
def admin_statistika() -> dict:
    from shop.models import Role

    return {
        "yangi": Order.objects.filter(holat=OrderStatus.YANGI).count(),
        "jami": Order.objects.count(),
        "mijozlar": TgUser.objects.filter(rol=Role.MIJOZ).count(),
        "kuryerlar": TgUser.objects.filter(rol=Role.KURYER).count(),
    }


# ============================================================
#  10-DARS — buyurtma holati va rol bo'yicha ID lar
# ============================================================


def _buyurtma_dict(o: Order) -> dict:
    return {
        "id": o.pk,
        "holat": o.holat,
        "holat_nomi": o.get_holat_display(),
        "ism": o.ism,
        "telefon": o.telefon,
        "manzil": o.manzil,
        "tolov": o.tolov,
        "jami": int(o.jami),
        "sana": o.yaratilgan.strftime("%d.%m.%Y %H:%M"),
        "mijoz_id": o.user.telegram_id,
        "kuryer_id": o.kuryer.telegram_id if getattr(o, "kuryer", None) else None,
        "kuryer_ismi": o.kuryer.ism if getattr(o, "kuryer", None) else None,
        "elementlar": [{"nom": e.mahsulot_nomi, "soni": e.soni, "narx": int(e.narx)}
                       for e in o.elementlar.all()],
    }


def _yuklash(buyurtma_id: int) -> Order | None:
    qs = Order.objects.select_related("user").prefetch_related("elementlar")
    if hasattr(Order, "kuryer"):
        qs = qs.select_related("kuryer")
    return qs.filter(pk=buyurtma_id).first()


@sync_to_async
def buyurtma_olish(buyurtma_id: int) -> dict | None:
    o = _yuklash(buyurtma_id)
    return _buyurtma_dict(o) if o else None


@sync_to_async
def buyurtmalar_royxati(holat: str | None = None, limit: int = 15) -> list[dict]:
    qs = Order.objects.select_related("user").prefetch_related("elementlar")
    if hasattr(Order, "kuryer"):
        qs = qs.select_related("kuryer")
    if holat:
        qs = qs.filter(holat=holat)
    return [_buyurtma_dict(o) for o in qs[:limit]]


@sync_to_async
def holat_ozgartirish(buyurtma_id: int, holat: str,
                      kim_tg_id: int | None = None, izoh: str = "") -> dict | None:
    from shop.models import OrderStatusLog

    o = _yuklash(buyurtma_id)
    if not o:
        return None
    kim = TgUser.objects.filter(telegram_id=kim_tg_id).first() if kim_tg_id else None
    o.holat = holat
    o.save(update_fields=["holat"])
    OrderStatusLog.objects.create(buyurtma=o, holat=holat, kim=kim, izoh=izoh[:255])
    return _buyurtma_dict(_yuklash(buyurtma_id))


@sync_to_async
def admin_idlar() -> list[int]:
    from django.conf import settings
    from shop.models import Role

    bazadan = set(TgUser.objects.filter(rol=Role.ADMIN, bloklangan=False)
                  .values_list("telegram_id", flat=True))
    return sorted(bazadan | set(settings.ADMIN_IDS))


@sync_to_async
def kuryer_idlar(faqat_smenada: bool = True) -> list[int]:
    from shop.models import Role

    qs = TgUser.objects.filter(rol=Role.KURYER, bloklangan=False)
    if faqat_smenada:
        qs = qs.filter(smenada=True)
    return list(qs.values_list("telegram_id", flat=True))


# ============================================================
#  11-DARS — kuryer oqimi
# ============================================================


@sync_to_async
def bosh_buyurtmalar(limit: int = 20) -> list[dict]:
    """Tasdiqlangan, lekin hali hech kim olmagan buyurtmalar."""
    qs = (Order.objects.select_related("user", "kuryer").prefetch_related("elementlar")
          .filter(holat=OrderStatus.TASDIQLANDI, kuryer__isnull=True)
          .order_by("yaratilgan")[:limit])
    return [_buyurtma_dict(o) for o in qs]


@sync_to_async
def kuryer_buyurtmalari(kuryer_tg_id: int) -> list[dict]:
    qs = (Order.objects.select_related("user", "kuryer").prefetch_related("elementlar")
          .filter(kuryer__telegram_id=kuryer_tg_id,
                  holat__in=[OrderStatus.YOLDA, OrderStatus.KUTILMOQDA])[:20])
    return [_buyurtma_dict(o) for o in qs]


@sync_to_async
def kuryer_olish(buyurtma_id: int, kuryer_tg_id: int) -> tuple[dict | None, str]:
    """Poyga holatiga chidamli: tekshiruv va yozish BITTA SQL da."""
    from shop.models import OrderStatusLog

    kuryer = TgUser.objects.filter(telegram_id=kuryer_tg_id).first()
    if not kuryer:
        return None, "kuryer_yoq"

    with transaction.atomic():
        olindi = Order.objects.filter(
            pk=buyurtma_id,
            kuryer__isnull=True,                 # shart SQL ichida
            holat=OrderStatus.TASDIQLANDI,
        ).update(kuryer=kuryer, holat=OrderStatus.YOLDA)

        if not olindi:                           # 0 qator = kimdir oldin ulgurdi
            return None, "band"

        OrderStatusLog.objects.create(buyurtma_id=buyurtma_id, holat=OrderStatus.YOLDA,
                                      kim=kuryer, izoh="Kuryer oldi")
    return _buyurtma_dict(_yuklash(buyurtma_id)), "ok"


@sync_to_async
def kuryer_yetkazdi(buyurtma_id: int, kuryer_tg_id: int) -> dict | None:
    from shop.models import OrderStatusLog

    o = _yuklash(buyurtma_id)
    if not o or not o.kuryer or o.kuryer.telegram_id != kuryer_tg_id:
        return None
    if o.holat != OrderStatus.YOLDA:
        return None

    o.holat = OrderStatus.KUTILMOQDA          # YAKUNLANDI emas!
    o.save(update_fields=["holat"])
    OrderStatusLog.objects.create(buyurtma=o, holat=OrderStatus.KUTILMOQDA,
                                  kim=o.kuryer, izoh="Kuryer yetkazdi")
    return _buyurtma_dict(_yuklash(buyurtma_id))


@sync_to_async
def mijoz_qabul_qildi(buyurtma_id: int, telegram_id: int) -> dict | None:
    from shop.models import OrderStatusLog

    o = _yuklash(buyurtma_id)
    if not o or o.user.telegram_id != telegram_id:      # faqat EGASI
        return None
    if o.holat not in (OrderStatus.KUTILMOQDA, OrderStatus.YOLDA):
        return None

    o.holat = OrderStatus.YAKUNLANDI
    o.save(update_fields=["holat"])
    OrderStatusLog.objects.create(buyurtma=o, holat=OrderStatus.YAKUNLANDI,
                                  kim=o.user, izoh="Mijoz qabul qildi")
    return _buyurtma_dict(_yuklash(buyurtma_id))


@sync_to_async
def kuryer_statistikasi(kuryer_tg_id: int) -> dict:
    qs = Order.objects.filter(kuryer__telegram_id=kuryer_tg_id)
    return {
        "yakunlangan": qs.filter(holat=OrderStatus.YAKUNLANDI).count(),
        "faol": qs.filter(holat__in=[OrderStatus.YOLDA, OrderStatus.KUTILMOQDA]).count(),
        "jami": qs.count(),
    }