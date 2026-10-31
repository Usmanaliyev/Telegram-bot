from django.core.management.base import BaseCommand, CommandError

from shop.models import Role, TgUser


class Command(BaseCommand):
    help = "Foydalanuvchi rolini o'zgartiradi: python manage.py setrole 123456789 kuryer"

    def add_arguments(self, parser):
        parser.add_argument("telegram_id", type=int)
        parser.add_argument("rol", choices=[r.value for r in Role])

    def handle(self, *args, **options):
        user = TgUser.objects.filter(telegram_id=options["telegram_id"]).first()
        if not user:
            raise CommandError("Bunday foydalanuvchi topilmadi. Avval botga /start yuborsin.")
        user.rol = options["rol"]
        user.save(update_fields=["rol"])
        self.stdout.write(self.style.SUCCESS(f"{user.ism} -> {user.get_rol_display()}"))