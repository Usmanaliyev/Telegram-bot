"""Qatlam qoidalarini qulflaydi — kelajakda tasodifan buzilmasin."""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent


def qatorlar(*fayllar: str) -> list[tuple[str, int, str]]:
    natija = []
    for nom in fayllar:
        yol = ROOT / nom
        if not yol.exists():
            continue
        for i, qator in enumerate(yol.read_text().splitlines(), 1):
            if qator.strip().startswith("#"):
                continue
            natija.append((nom, i, qator))
    return natija


def buzganlar(fayllar: list[str], naqsh: str) -> list[str]:
    rx = re.compile(naqsh)
    return [f"{nom}:{i}: {q.strip()}" for nom, i, q in qatorlar(*fayllar) if rx.search(q)]


HANDLERLAR = [f"handlers/{p.name}" for p in (ROOT / "handlers").glob("*.py")]


def test_servis_telegramni_bilmaydi():
    assert not buzganlar(["services.py"], r"\bimport aiogram|from aiogram\b")


def test_handlerlarda_orm_yoq():
    assert not buzganlar(HANDLERLAR, r"\.objects\.|sync_to_async")


def test_klaviaturalar_bazaga_bormaydi():
    assert not buzganlar(["keyboards.py"], r"\.objects\.|sync_to_async")


def test_middleware_update_ni_ochadi():
    """Outer middleware Update oladi — Message emas."""
    matn = (ROOT / "middlewares.py").read_text()
    assert "event.event if isinstance(event, Update)" in matn


def test_router_tartibi(dp):
    tartib = [r.name for r in dp.sub_routers]
    assert tartib[0] == "checkout", "FSM + /bekor eng birinchi"
    birinchi_umumiy = tartib.index("common")
    assert tartib.index("admin") < birinchi_umumiy
    assert tartib.index("courier") < birinchi_umumiy
    assert tartib[-1] == "common", "fallback eng oxirida"


def test_barcha_routerlar_royxatdan_otgan(dp):
    royxatda = {r.name for r in dp.sub_routers}
    elon_qilingan = set()
    for nom, _, qator in qatorlar(*HANDLERLAR):
        for m in re.finditer(r'Router\(name="([^"]+)"\)', qator):
            elon_qilingan.add(m.group(1))
    assert elon_qilingan == royxatda, f"Ulanmagan router: {elon_qilingan - royxatda}"