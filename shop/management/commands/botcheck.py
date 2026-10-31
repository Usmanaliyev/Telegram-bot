"""Ishga tushirishdan oldin hamma narsa joyidami — bitta buyruq bilan tekshiradi."""
import json
import urllib.error
import urllib.request

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from shop.models import Category, Order, OrderStatus, Product, Role, TgUser

OK, WARN, BAD = "✅", "⚠️ ", "❌"


class Command(BaseCommand):
    help = "Bot va admin panel ishga tushishga tayyorligini tekshiradi"

    def handle(self, *args, **options):
        self.muammolar = []
        self.ogohlantirishlar = []

        self.stdout.write(self.style.MIGRATE_HEADING("\n  TAYYORLIK TEKSHIRUVI\n"))

        self._bolim("Sozlamalar")
        token = self._token()
        self._admin_ids()
        self._debug()

        self._bolim("Ma'lumotlar bazasi")
        self._baza()
        self._migratsiyalar()
        self._superuser()

        self._bolim("Katalog")
        self._katalog()

        self._bolim("Rollar")
        self._rollar()

        if token:
            self._bolim("Telegram")
            self._telegram(token)

        self._xulosa()

    def _bolim(self, sarlavha):
        self.stdout.write(self.style.MIGRATE_LABEL(f"\n  {sarlavha}"))
        self.stdout.write("  " + "─" * 58)

    def _qator(self, belgi, matn, maslahat=""):
        self.stdout.write(f"  {belgi} {matn}")
        if maslahat:
            self.stdout.write(self.style.WARNING(f"      → {maslahat}"))

    def _xato(self, matn, maslahat=""):
        self.muammolar.append(matn)
        self._qator(BAD, matn, maslahat)

    def _ogoh(self, matn, maslahat=""):
        self.ogohlantirishlar.append(matn)
        self._qator(WARN, matn, maslahat)

    def _token(self):
        token = settings.BOT_TOKEN
        if not token:
            self._xato("BOT_TOKEN topilmadi",
                       ".env faylini oching va BOT_TOKEN=... qatorini to'ldiring")
            return None
        if ":" not in token or not token.split(":")[0].isdigit():
            self._xato("BOT_TOKEN formati noto'g'ri",
                       "To'g'ri ko'rinish: 123456789:AAH...")
            return None
        self._qator(OK, f"BOT_TOKEN o'qildi (bot id: {token.split(':')[0]})")
        return token

    def _admin_ids(self):
        if not settings.ADMIN_IDS:
            self._ogoh("ADMIN_IDS bo'sh",
                       "@userinfobot dan ID oling va .env ga ADMIN_IDS=123456789 deb yozing")
        else:
            self._qator(OK, f"ADMIN_IDS: {', '.join(map(str, settings.ADMIN_IDS))}")

    def _debug(self):
        if settings.DEBUG:
            self._ogoh("DEBUG=True — bu faqat development uchun",
                       "Serverda .env ga DJANGO_DEBUG=0 yozing")
        else:
            self._qator(OK, f"DEBUG=False, ALLOWED_HOSTS: {', '.join(settings.ALLOWED_HOSTS)}")

    def _baza(self):
        try:
            connection.ensure_connection()
            dvigatel = connection.settings_dict["ENGINE"].rsplit(".", 1)[-1]
            self._qator(OK, f"Baza ulanishi ishlaydi ({dvigatel})")
            if dvigatel == "sqlite3" and not settings.DEBUG:
                self._ogoh("Production'da SQLite ishlatilyapti",
                           "PostgreSQL ga o'ting: .env ga DB_NAME, DB_USER, DB_PASSWORD")
        except Exception as exc:  # noqa: BLE001
            self._xato(f"Bazaga ulanib bo'lmadi: {exc}")

    def _migratsiyalar(self):
        try:
            executor = MigrationExecutor(connection)
            reja = executor.migration_plan(executor.loader.graph.leaf_nodes())
        except Exception as exc:  # noqa: BLE001
            self._xato(f"Migratsiyalarni tekshirib bo'lmadi: {exc}")
            return
        if reja:
            self._xato(f"{len(reja)} ta migratsiya qo'llanmagan", "python manage.py migrate")
        else:
            self._qator(OK, "Barcha migratsiyalar qo'llangan")

    def _superuser(self):
        from django.contrib.auth import get_user_model

        soni = get_user_model().objects.filter(is_superuser=True).count()
        if soni:
            self._qator(OK, f"Admin panel foydalanuvchisi: {soni} ta")
        else:
            self._ogoh("Superuser yo'q", "python manage.py createsuperuser")

    def _katalog(self):
        kategoriyalar = Category.objects.filter(faol=True).count()
        mahsulotlar = Product.objects.filter(faol=True).count()
        if not mahsulotlar:
            self._xato("Katalog bo'sh — botda ko'rsatadigan narsa yo'q",
                       "python manage.py seed")
            return
        self._qator(OK, f"Katalog: {kategoriyalar} kategoriya, {mahsulotlar} mahsulot")

        bosh = Category.objects.filter(faol=True, mahsulotlar__isnull=True).count()
        if bosh:
            self._ogoh(f"{bosh} ta kategoriyada mahsulot yo'q",
                       "Ular botda ko'rinmaydi — admin paneldan mahsulot qo'shing")

    def _rollar(self):
        adminlar = TgUser.objects.filter(rol=Role.ADMIN).count()
        kuryerlar = TgUser.objects.filter(rol=Role.KURYER)
        smenada = kuryerlar.filter(smenada=True).count()

        if adminlar or settings.ADMIN_IDS:
            self._qator(OK, f"Adminlar: bazada {adminlar} ta, .env da {len(settings.ADMIN_IDS)} ta")
        else:
            self._xato("Admin yo'q — yangi buyurtmani hech kim tasdiqlay olmaydi",
                       ".env ga ADMIN_IDS qo'shing yoki: python manage.py setrole <id> admin")

        if not kuryerlar.exists():
            self._ogoh("Kuryer yo'q — buyurtmani olib ketadigan odam yo'q",
                       "Kuryer /start yuborsin, keyin: python manage.py setrole <id> kuryer")
        else:
            self._qator(OK, f"Kuryerlar: {kuryerlar.count()} ta ({smenada} tasi smenada)")
            if not smenada:
                self._ogoh("Hech bir kuryer smenada emas",
                           "Kuryer botda «🟢 Smenani boshlash» tugmasini bossin")

        kutayotgan = Order.objects.filter(holat=OrderStatus.YANGI).count()
        if kutayotgan:
            self._ogoh(f"{kutayotgan} ta buyurtma tasdiqlanmagan",
                       "Admin panelda ko'rib chiqing")

    def _telegram(self, token):
        me = self._api(token, "getMe")
        if not me:
            self._xato("Telegram API javob bermadi",
                       "Internet yoki token noto'g'ri. BotFather → /mybots → API Token")
            return
        if not me.get("ok"):
            self._xato(f"Token rad etildi: {me.get('description')}",
                       "BotFather → /mybots → botni tanlang → API Token")
            return

        bot = me["result"]
        self._qator(OK, f"Bot topildi: @{bot['username']} ({bot['first_name']})")

        hook = self._api(token, "getWebhookInfo")
        if hook and hook.get("ok"):
            url = hook["result"].get("url") or ""
            kutayotgan = hook["result"].get("pending_update_count", 0)
            if url:
                self._xato(f"Webhook o'rnatilgan: {url}",
                           "Polling ishlamaydi. Yechim: bot.delete_webhook() yoki webhook rejimiga o'ting")
            else:
                self._qator(OK, "Webhook o'rnatilmagan — long polling uchun tayyor")
            if kutayotgan > 20:
                self._ogoh(f"{kutayotgan} ta kutilayotgan update bor",
                           "Bot uzoq vaqt o'chiq turgan")

    @staticmethod
    def _api(token, method):
        try:
            with urllib.request.urlopen(
                f"https://api.telegram.org/bot{token}/{method}", timeout=10
            ) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            try:
                return json.loads(exc.read().decode())
            except Exception:  # noqa: BLE001
                return None
        except Exception:  # noqa: BLE001
            return None

    def _xulosa(self):
        self.stdout.write("\n  " + "═" * 58)
        if self.muammolar:
            self.stdout.write(self.style.ERROR(
                f"\n  {len(self.muammolar)} ta jiddiy muammo — bot to'liq ishlamaydi:\n"))
            for m in self.muammolar:
                self.stdout.write(self.style.ERROR(f"    • {m}"))
        elif self.ogohlantirishlar:
            self.stdout.write(self.style.WARNING(
                f"\n  Bot ishga tushadi, lekin {len(self.ogohlantirishlar)} ta ogohlantirish bor.\n"))
        else:
            self.stdout.write(self.style.SUCCESS(
                "\n  🎉 Hammasi joyida. Ishga tushiring:\n"
                "\n     python manage.py runbot"
                "\n     python manage.py runserver\n"))
        self.stdout.write("")