from decimal import Decimal

import pytest
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from tests.mocked import Conversation, MockedSession

MIJOZ_ID = 100001
KURYER_ID = 100002
ADMIN_ID = 100003


@pytest.fixture
def session():
    return MockedSession()


@pytest.fixture
def bot(session):
    return Bot(token="42:TEST", session=session,
               default=DefaultBotProperties(parse_mode=ParseMode.HTML))


@pytest.fixture(scope="session")
def dp():
    """Router'lar modul singleton — sessiyaga BITTA Dispatcher."""
    from shop.management.commands.runbot import dispatcher_yasash

    return dispatcher_yasash(throttle_rate=0)


@pytest.fixture(autouse=True)
def _fsm_tozalash(dp):
    dp.storage.storage.clear()
    yield
    dp.storage.storage.clear()


@pytest.fixture
def katalog(transactional_db):
    from shop.models import Category, Product

    burgerlar = Category.objects.create(nom="Burgerlar", emoji="🍔", tartib=1)
    ichimliklar = Category.objects.create(nom="Ichimliklar", emoji="🥤", tartib=2)
    return {
        "burgerlar": burgerlar,
        "klassik": Product.objects.create(kategoriya=burgerlar, nom="Klassik burger",
                                          tavsif="Mol go'shti", narx=Decimal("32000")),
        "cola": Product.objects.create(kategoriya=ichimliklar, nom="Coca-Cola",
                                       tavsif="0.5L", narx=Decimal("12000")),
    }


def _user(telegram_id: int, ism: str, rol: str, smenada: bool = False):
    from shop.models import Cart, TgUser

    u = TgUser.objects.create(telegram_id=telegram_id, ism=ism, telefon="+998901112233",
                              rol=rol, smenada=smenada)
    Cart.objects.create(user=u)
    return u


@pytest.fixture
def mijoz(katalog):
    from shop.models import Role

    return _user(MIJOZ_ID, "Mijoz Mijozov", Role.MIJOZ)


@pytest.fixture
def kuryer(katalog):
    from shop.models import Role

    return _user(KURYER_ID, "Kuryer Kuryerov", Role.KURYER, smenada=True)


@pytest.fixture
def admin(katalog):
    from shop.models import Role

    return _user(ADMIN_ID, "Admin Adminov", Role.ADMIN)


@pytest.fixture
def talk(dp, bot, session):
    def factory(user_id: int, ism: str = "Sinov"):
        return Conversation(dp, bot, session, user_id, ism)

    return factory