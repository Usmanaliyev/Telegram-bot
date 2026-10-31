# ============================================================
#  Admin panel sozlamalari.
#  Bu 30 qator kod evaziga to'liq boshqaruv paneli olamiz.
# ============================================================

from django.contrib import admin

from shop.models import Category, Product

admin.site.site_header = "Mening botim — boshqaruv"
admin.site.site_title = "Bot admin"
admin.site.index_title = "Boshqaruv paneli"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("__str__", "tartib", "faol", "mahsulot_soni")
    list_editable = ("tartib", "faol")
    search_fields = ("nom",)

    @admin.display(description="Mahsulotlar")
    def mahsulot_soni(self, obj):
        return obj.mahsulotlar.count()


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("nom", "kategoriya", "narx", "faol", "tartib")
    list_editable = ("narx", "faol", "tartib")
    list_filter = ("kategoriya", "faol")
    search_fields = ("nom", "tavsif")


from shop.models import (Cart, CartItem, Order, OrderItem, OrderStatusLog,
                         Role, TgUser)


@admin.register(TgUser)
class TgUserAdmin(admin.ModelAdmin):
    list_display = ("ism", "telegram_id", "telefon", "rol", "smenada",
                    "bloklangan", "buyurtma_soni")
    list_filter = ("rol", "bloklangan", "smenada")
    list_editable = ("rol", "bloklangan")
    search_fields = ("ism", "telefon", "telegram_id")
    actions = ("kuryer_qil", "mijoz_qil", "bloklash", "blokdan_chiqarish")

    @admin.action(description="Kuryer qilish")
    def kuryer_qil(self, request, queryset):
        self.message_user(request, f"{queryset.update(rol=Role.KURYER)} ta kuryer bo'ldi.")

    @admin.action(description="Mijoz qilish")
    def mijoz_qil(self, request, queryset):
        self.message_user(request, f"{queryset.update(rol=Role.MIJOZ)} ta mijoz bo'ldi.")

    @admin.action(description="Bloklash")
    def bloklash(self, request, queryset):
        self.message_user(request, f"{queryset.update(bloklangan=True)} ta bloklandi.")

    @admin.action(description="Blokdan chiqarish")
    def blokdan_chiqarish(self, request, queryset):
        self.message_user(request, f"{queryset.update(bloklangan=False)} ta blokdan chiqdi.")

    @admin.display(description="Buyurtmalar")
    def buyurtma_soni(self, obj):
        return obj.buyurtmalar.count()


class OrderStatusLogInline(admin.TabularInline):
    model = OrderStatusLog
    extra = 0
    can_delete = False
    readonly_fields = ("holat", "kim", "izoh", "vaqt")

    def has_add_permission(self, request, obj=None):
        return False


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("mahsulot_nomi", "narx", "soni")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "holat", "ism", "telefon", "kuryer", "jami", "yaratilgan")
    list_filter = ("holat", "yaratilgan")
    search_fields = ("id", "ism", "telefon", "manzil")
    readonly_fields = ("jami", "yaratilgan")
    inlines = (OrderItemInline, OrderStatusLogInline)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "kuryer")


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("user",)
    inlines = (CartItemInline,)