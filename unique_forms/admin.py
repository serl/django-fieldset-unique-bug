from django.contrib import admin
from .models import Design, Product


class ProductInlineAdmin(admin.TabularInline):
    model = Product
    extra = 0


@admin.register(Design)
class DesignAdmin(admin.ModelAdmin):
    inlines = [ProductInlineAdmin]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    ...
