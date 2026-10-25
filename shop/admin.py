min

# Register your models here.
from django.contrib import admin
from shop.models import Category, Product

admin.site.site_header = "Mening botim — boshqaruv"
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