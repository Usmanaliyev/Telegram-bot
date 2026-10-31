# ============================================================
#  6-DARS — Django modellari
#
#  data.py dagi lug'at endi BAZA jadvaliga aylanadi.
#
#  Har bir class  -> bitta jadval
#  Har bir field  -> bitta ustun
# ============================================================

from django.db import models


class Category(models.Model):
    nom = models.CharField("Nomi", max_length=120, unique=True)
    emoji = models.CharField("Emoji", max_length=8, blank=True, default="")
    tartib = models.PositiveIntegerField("Tartib", default=0)
    faol = models.BooleanField("Faol", default=True)

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"
        ordering = ("tartib", "nom")

    def __str__(self):
        return f"{self.emoji} {self.nom}".strip()


class Product(models.Model):
    kategoriya = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="mahsulotlar",
        verbose_name="Kategoriya",
    )
    nom = models.CharField("Nomi", max_length=180)
    tavsif = models.TextField("Tavsif", blank=True, default="")
    narx = models.DecimalField("Narx", max_digits=12, decimal_places=2)
    faol = models.BooleanField("Faol", default=True)
    tartib = models.PositiveIntegerField("Tartib", default=0)
    yaratilgan = models.DateTimeField("Yaratilgan", auto_now_add=True)

    class Meta:
        verbose_name = "Mahsulot"
        verbose_name_plural = "Mahsulotlar"
        ordering = ("tartib", "nom")

    def __str__(self):
        return self.nom


# ============================================================
#  8-DARS — Foydalanuvchi, savat va buyurtma
# ============================================================


class Role(models.TextChoices):
    MIJOZ = "mijoz", "Mijoz"
    KURYER = "kuryer", "Kuryer"
    ADMIN = "admin", "Admin"


class TgUser(models.Model):
    telegram_id = models.BigIntegerField("Telegram ID", unique=True, db_index=True)
    ism = models.CharField("Ism", max_length=255)
    telefon = models.CharField("Telefon", max_length=32, blank=True, default="")
    rol = models.CharField("Rol", max_length=16, choices=Role.choices, default=Role.MIJOZ)
    bloklangan = models.BooleanField("Bloklangan", default=False)
    smenada = models.BooleanField("Smenada", default=False)
    yaratilgan = models.DateTimeField("Ro'yxatdan o'tgan", auto_now_add=True)

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"
        ordering = ("-yaratilgan",)

    def __str__(self):
        return f"{self.ism} ({self.telegram_id})"


class Cart(models.Model):
    user = models.OneToOneField(TgUser, on_delete=models.CASCADE,
                                related_name="savat", verbose_name="Foydalanuvchi")

    class Meta:
        verbose_name = "Savat"
        verbose_name_plural = "Savatlar"

    def __str__(self):
        return f"{self.user.ism} savati"


class CartItem(models.Model):
    savat = models.ForeignKey(Cart, on_delete=models.CASCADE,
                              related_name="elementlar", verbose_name="Savat")
    mahsulot = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Mahsulot")
    soni = models.PositiveIntegerField("Soni", default=1)

    class Meta:
        verbose_name = "Savat elementi"
        verbose_name_plural = "Savat elementlari"
        constraints = [
            models.UniqueConstraint(fields=("savat", "mahsulot"), name="uniq_savat_mahsulot")
        ]

    def __str__(self):
        return f"{self.mahsulot.nom} x{self.soni}"


class OrderStatus(models.TextChoices):
    YANGI = "yangi", "Yangi"
    TASDIQLANDI = "tasdiqlandi", "Tasdiqlandi"
    YOLDA = "yolda", "Yo'lda"
    KUTILMOQDA = "kutilmoqda", "Mijoz tasdig'i kutilmoqda"
    YAKUNLANDI = "yakunlandi", "Yakunlandi"
    BEKOR = "bekor", "Bekor qilindi"


class Order(models.Model):
    user = models.ForeignKey(TgUser, on_delete=models.PROTECT,
                             related_name="buyurtmalar", verbose_name="Mijoz")
    kuryer = models.ForeignKey(TgUser, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name="yetkazishlar", verbose_name="Kuryer")
    holat = models.CharField("Holat", max_length=16, choices=OrderStatus.choices,
                             default=OrderStatus.YANGI, db_index=True)
    ism = models.CharField("Ism", max_length=255)
    telefon = models.CharField("Telefon", max_length=32)
    manzil = models.CharField("Manzil", max_length=255)
    tolov = models.CharField("To'lov", max_length=16, default="naqd")
    jami = models.DecimalField("Jami", max_digits=12, decimal_places=2, default=0)
    yaratilgan = models.DateTimeField("Yaratilgan", auto_now_add=True)

    class Meta:
        verbose_name = "Buyurtma"
        verbose_name_plural = "Buyurtmalar"
        ordering = ("-yaratilgan",)

    def __str__(self):
        return f"Buyurtma #{self.pk}"


class OrderItem(models.Model):
    buyurtma = models.ForeignKey(Order, on_delete=models.CASCADE,
                                 related_name="elementlar", verbose_name="Buyurtma")
    # PROTECT: buyurtmada turgan mahsulotni o'chirib bo'lmaydi
    mahsulot = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name="Mahsulot")
    # NUSXA: narx va nom o'zgarsa ham eski chek o'zgarmaydi
    mahsulot_nomi = models.CharField("Mahsulot nomi", max_length=180)
    narx = models.DecimalField("Dona narxi", max_digits=12, decimal_places=2)
    soni = models.PositiveIntegerField("Soni", default=1)

    class Meta:
        verbose_name = "Buyurtma elementi"
        verbose_name_plural = "Buyurtma elementlari"

    def __str__(self):
        return f"{self.mahsulot_nomi} x{self.soni}"

    @property
    def summa(self):
        return self.narx * self.soni


class OrderStatusLog(models.Model):
    buyurtma = models.ForeignKey(Order, on_delete=models.CASCADE,
                                 related_name="loglar", verbose_name="Buyurtma")
    holat = models.CharField("Holat", max_length=16, choices=OrderStatus.choices)
    kim = models.ForeignKey(TgUser, on_delete=models.SET_NULL, null=True, blank=True,
                            verbose_name="Kim o'zgartirdi")
    izoh = models.CharField("Izoh", max_length=255, blank=True, default="")
    vaqt = models.DateTimeField("Vaqt", auto_now_add=True)

    class Meta:
        verbose_name = "Holat tarixi"
        verbose_name_plural = "Holatlar tarixi"
        ordering = ("vaqt",)

    def __str__(self):
        return f"#{self.buyurtma_id} -> {self.holat}"