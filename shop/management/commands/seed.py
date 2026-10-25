from decimal import Decimal
from django.core.management.base import BaseCommand

from data import CATEGORIES
from shop.models import Category, Product


class Command(BaseCommand):
    help = "data.py dagi mahsulotlarni bazaga ko'chiradi"

    def handle(self, *args, **options):
        for tartib, (kalit, kat) in enumerate(CATEGORIES.items(), 1):
            emoji, _, nom = kat["nom"].partition(" ")
            kategoriya, _ = Category.objects.get_or_create(
                nom=nom or kalit, defaults={"emoji": emoji, "tartib": tartib})

            for i, m in enumerate(kat["mahsulotlar"], 1):
                Product.objects.get_or_create(
                    kategoriya=kategoriya, nom=m["nom"],
                    defaults={"tavsif": m["tavsif"], "narx": Decimal(m["narx"]), "tartib": i})

        self.stdout.write(self.style.SUCCESS(
            f"Bazada: {Category.objects.count()} kategoriya, {Product.objects.count()} mahsulot."))