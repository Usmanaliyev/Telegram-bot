import pytest

from callbacks import AdminCB, CartCB, CheckoutCB, CourierCB, OrderCB, ProductCB
from tests.conftest import ADMIN_ID, KURYER_ID, MIJOZ_ID

pytestmark = pytest.mark.django_db(transaction=True)


async def buyurtma_ber(t, katalog, qty: int = 2):
    await t.click(ProductCB(action="add", product_id=katalog["klassik"].pk, qty=qty).pack())
    await t.click(CartCB(action="checkout").pack())
    await t.send("Ali Valiyev")
    await t.send("+998901112233")
    await t.send("Chilonzor 9-kvartal, 42-uy")
    await t.click(CheckoutCB(action="payment", value="naqd").pack())
    return await t.click(CheckoutCB(action="submit").pack())


async def test_buyurtma_yaratiladi(mijoz, admin, talk, katalog):
    from shop.models import CartItem, Order, OrderStatus

    session = await buyurtma_ber(talk(MIJOZ_ID), katalog)
    assert session.contains("qabul qilindi")

    order = await Order.objects.afirst()
    assert order.holat == OrderStatus.YANGI
    assert order.jami == 64000
    assert order.manzil == "Chilonzor 9-kvartal, 42-uy"
    assert not await CartItem.objects.aexists(), "Savat tozalanishi kerak"


async def test_narx_muzlatiladi(mijoz, admin, talk, katalog):
    """Buyurtma tarixi keyingi narx o'zgarishidan ta'sirlanmasin."""
    from shop.models import Order, OrderItem

    await buyurtma_ber(talk(MIJOZ_ID), katalog)

    katalog["klassik"].narx = 99000
    await katalog["klassik"].asave()

    order = await Order.objects.afirst()
    element = await OrderItem.objects.afirst()
    assert order.jami == 64000
    assert element.narx == 32000
    assert element.mahsulot_nomi == "Klassik burger"


async def test_adminga_bildirishnoma(mijoz, admin, talk, katalog):
    session = await buyurtma_ber(talk(MIJOZ_ID), katalog)
    adminga = [m for m in session.calls("SendMessage") if m.chat_id == ADMIN_ID]
    assert adminga, "Admin yangi buyurtma haqida xabar olishi kerak"
    assert "YANGI BUYURTMA" in adminga[0].text
    assert "Ali Valiyev" in adminga[0].text


async def test_toliq_sikl(mijoz, admin, kuryer, talk, katalog):
    """Mijoz → admin → kuryer → mijoz tasdig'i."""
    from shop.models import Order, OrderStatus, OrderStatusLog

    m, a, k = talk(MIJOZ_ID), talk(ADMIN_ID), talk(KURYER_ID)

    await buyurtma_ber(m, katalog)
    order = await Order.objects.afirst()
    assert order.holat == OrderStatus.YANGI

    session = await a.click(AdminCB(action="tasdiq", order_id=order.pk).pack())
    await order.arefresh_from_db()
    assert order.holat == OrderStatus.TASDIQLANDI
    assert [x for x in session.calls("SendMessage") if x.chat_id == KURYER_ID], \
        "Smenadagi kuryer taklif olishi kerak"

    await k.click(CourierCB(action="olaman", order_id=order.pk).pack())
    await order.arefresh_from_db()
    assert order.holat == OrderStatus.YOLDA
    assert order.kuryer_id == kuryer.pk

    session = await k.click(CourierCB(action="yetkazdim", order_id=order.pk).pack())
    await order.arefresh_from_db()
    assert order.holat == OrderStatus.KUTILMOQDA, "Kuryer emas, MIJOZ yakunlaydi"

    prompt = [x for x in session.calls("SendMessage") if x.chat_id == MIJOZ_ID]
    assert any("Qabul qildim" in b.text for x in prompt if x.reply_markup
               for row in x.reply_markup.inline_keyboard for b in row)

    await m.click(OrderCB(action="qabul", order_id=order.pk).pack())
    await order.arefresh_from_db()
    assert order.holat == OrderStatus.YAKUNLANDI

    zanjir = [log.holat async for log in OrderStatusLog.objects.order_by("vaqt")]
    assert zanjir == ["tasdiqlandi", "yolda", "kutilmoqda", "yakunlandi"]


async def test_ikki_kuryer_bitta_buyurtmani_ololmaydi(mijoz, admin, kuryer, talk, katalog):
    from shop.models import Cart, Order, OrderStatus, Role, TgUser

    ikkinchi = await TgUser.objects.acreate(telegram_id=100004, ism="Ikkinchi kuryer",
                                            rol=Role.KURYER, smenada=True)
    await Cart.objects.acreate(user=ikkinchi)

    await buyurtma_ber(talk(MIJOZ_ID), katalog)
    order = await Order.objects.afirst()
    await talk(ADMIN_ID).click(AdminCB(action="tasdiq", order_id=order.pk).pack())

    await talk(KURYER_ID).click(CourierCB(action="olaman", order_id=order.pk).pack())
    session = await talk(100004).click(CourierCB(action="olaman", order_id=order.pk).pack())

    await order.arefresh_from_db()
    assert order.kuryer_id == kuryer.pk
    assert order.holat == OrderStatus.YOLDA
    assert any("band" in a.text.lower() for a in session.calls("AnswerCallbackQuery") if a.text)


async def test_begona_odam_qabul_qila_olmaydi(mijoz, admin, kuryer, talk, katalog):
    from shop.models import Order, OrderStatus

    await buyurtma_ber(talk(MIJOZ_ID), katalog)
    order = await Order.objects.afirst()
    await talk(ADMIN_ID).click(AdminCB(action="tasdiq", order_id=order.pk).pack())
    await talk(KURYER_ID).click(CourierCB(action="olaman", order_id=order.pk).pack())
    await talk(KURYER_ID).click(CourierCB(action="yetkazdim", order_id=order.pk).pack())

    await talk(KURYER_ID).click(OrderCB(action="qabul", order_id=order.pk).pack())
    await order.arefresh_from_db()
    assert order.holat == OrderStatus.KUTILMOQDA, "Faqat buyurtma EGASI tasdiqlaydi"


async def test_bosh_savatdan_buyurtma_bolmaydi(mijoz, talk, katalog):
    from shop.models import Order

    session = await talk(MIJOZ_ID).click(CartCB(action="checkout").pack())
    assert any("bo'sh" in a.text.lower() for a in session.calls("AnswerCallbackQuery") if a.text)
    assert not await Order.objects.aexists()