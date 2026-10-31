import pytest

from callbacks import CartCB, CategoryCB, ProductCB
from tests.conftest import MIJOZ_ID

pytestmark = pytest.mark.django_db(transaction=True)


async def test_start_javob_beradi(mijoz, talk):
    session = await talk(MIJOZ_ID).send("/start")
    assert session.contains("Salom")


async def test_menyu_bazadan_keladi(mijoz, talk, katalog):
    t = talk(MIJOZ_ID)
    await t.send("🍽 Menyu")
    assert any("Burgerlar" in text for text, _ in t.buttons())


async def test_savatga_qoshish(mijoz, talk, katalog):
    from shop.models import CartItem

    t = talk(MIJOZ_ID)
    await t.click(ProductCB(action="add", product_id=katalog["klassik"].pk, qty=2).pack())

    element = await CartItem.objects.select_related("mahsulot").afirst()
    assert element is not None
    assert element.soni == 2
    assert element.mahsulot_id == katalog["klassik"].pk


async def test_savat_matematikasi(mijoz, talk, katalog):
    t = talk(MIJOZ_ID)
    await t.click(ProductCB(action="add", product_id=katalog["klassik"].pk, qty=2).pack())
    await t.click(ProductCB(action="add", product_id=katalog["cola"].pk, qty=1).pack())

    session = await t.send("🧺 Savat")
    # 2 x 32000 + 1 x 12000 = 76000
    assert session.contains("76 000 so'm")


async def test_sonini_kamaytirish_nolda_ochiradi(mijoz, talk, katalog):
    from shop.models import CartItem

    t = talk(MIJOZ_ID)
    await t.click(ProductCB(action="add", product_id=katalog["klassik"].pk, qty=1).pack())
    await t.click(CartCB(action="dec", product_id=katalog["klassik"].pk).pack())

    assert not await CartItem.objects.aexists()


async def test_faolsiz_mahsulot_katalogda_yoq(mijoz, talk, katalog):
    katalog["klassik"].faol = False
    await katalog["klassik"].asave()

    t = talk(MIJOZ_ID)
    await t.send("🍽 Menyu")
    await t.click(CategoryCB(category_id=katalog["burgerlar"].pk).pack())
    assert not any("Klassik burger" in text for text, _ in t.buttons())


async def test_savat_bazada_saqlanadi(mijoz, talk, katalog):
    """Bot restart bo'lsa ham savat yo'qolmasin — u bazada."""
    from shop.models import CartItem

    await talk(MIJOZ_ID).click(
        ProductCB(action="add", product_id=katalog["klassik"].pk, qty=3).pack())

    yangi_sessiya = talk(MIJOZ_ID)
    session = await yangi_sessiya.send("🧺 Savat")
    assert session.contains("96 000 so'm")
    assert await CartItem.objects.acount() == 1