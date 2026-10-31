import pytest

from callbacks import AdminCB, CourierCB
from tests.conftest import ADMIN_ID, KURYER_ID, MIJOZ_ID

pytestmark = pytest.mark.django_db(transaction=True)


async def test_mijozda_admin_tugmasi_yoq(mijoz, talk):
    session = await talk(MIJOZ_ID).send("/start")
    tugmalar = [b.text for m in session.requests
                if getattr(getattr(m, "reply_markup", None), "keyboard", None)
                for row in m.reply_markup.keyboard for b in row]
    assert not any("Admin panel" in t for t in tugmalar)
    assert not any("Kuryer paneli" in t for t in tugmalar)


async def test_adminda_ikkala_panel_bor(admin, talk):
    session = await talk(ADMIN_ID).send("/start")
    tugmalar = [b.text for m in session.requests
                if getattr(getattr(m, "reply_markup", None), "keyboard", None)
                for row in m.reply_markup.keyboard for b in row]
    assert any("Admin panel" in t for t in tugmalar)
    assert any("Kuryer paneli" in t for t in tugmalar)


async def test_mijoz_admin_panelga_kira_olmaydi(mijoz, talk):
    session = await talk(MIJOZ_ID).send("⚙️ Admin panel")
    assert not session.contains("Bo'limni tanlang")


async def test_mijoz_admin_callbackini_ishlata_olmaydi(mijoz, admin, talk, katalog):
    from shop.models import Order, OrderStatus, TgUser

    user = await TgUser.objects.aget(telegram_id=MIJOZ_ID)
    order = await Order.objects.acreate(user=user, ism="Ali", telefon="+998901112233",
                                        manzil="Test", jami=64000)

    await talk(MIJOZ_ID).click(AdminCB(action="tasdiq", order_id=order.pk).pack())
    await order.arefresh_from_db()
    assert order.holat == OrderStatus.YANGI


async def test_mijoz_kuryer_callbackini_ishlata_olmaydi(mijoz, admin, talk):
    from shop.models import Order, OrderStatus, TgUser

    user = await TgUser.objects.aget(telegram_id=MIJOZ_ID)
    order = await Order.objects.acreate(user=user, ism="Ali", telefon="+998901112233",
                                        manzil="Test", jami=64000,
                                        holat=OrderStatus.TASDIQLANDI)

    await talk(MIJOZ_ID).click(CourierCB(action="olaman", order_id=order.pk).pack())
    await order.arefresh_from_db()
    assert order.kuryer_id is None


async def test_bloklangan_foydalanuvchi_toxtatiladi(mijoz, talk):
    mijoz.bloklangan = True
    await mijoz.asave()

    session = await talk(MIJOZ_ID).send("🍽 Menyu")
    assert session.contains("bloklangansiz")
    assert not session.contains("Kategoriyani tanlang")


async def test_smena_almashadi(kuryer, talk):
    from shop.models import TgUser

    session = await talk(KURYER_ID).send("🔴 Smenani tugatish")
    assert session.contains("Smena tugadi")
    assert not (await TgUser.objects.aget(telegram_id=KURYER_ID)).smenada

    session = await talk(KURYER_ID).send("🟢 Smenani boshlash")
    assert (await TgUser.objects.aget(telegram_id=KURYER_ID)).smenada


async def test_admin_kuryer_paneliga_ham_kiradi(admin, talk):
    session = await talk(ADMIN_ID).send("🛵 Kuryer paneli")
    assert session.contains("Kuryer paneli")