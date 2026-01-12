

from django.contrib import admin
from .models import Category, Product, Order, OrderItem
from .models import ProductVariant
from django.utils.html import format_html

from django.utils.timezone import now
from datetime import timedelta



@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")


# @admin.register(Product)
# class ProductAdmin(admin.ModelAdmin):
#     list_display = ("id", "name", "price")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("variant", "quantity", "price")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "total_amount",
        "payment_method",
        "status_badge",
        "short_address",
        "created_at",
    )

    list_filter = ("status", "payment_method", "created_at")
    search_fields = ("user__username", "address")
    inlines = [OrderItemInline]

    readonly_fields = (
        "user",
        "total_amount",
        "payment_method",
        "address",
        "created_at",
    )

    actions = ["mark_shipped", "mark_delivered"]

    # 🔹 Address preview
    def short_address(self, obj):
        return obj.address[:40] + "..." if obj.address else "-"
    short_address.short_description = "Address"

    # 🔹 Admin Action: Mark Shipped
    def mark_shipped(self, request, queryset):
        queryset = queryset.filter(status="placed")
        updated = queryset.update(
            status="shipped",
            estimated_delivery=now().date() + timedelta(days=3)
        )
        self.message_user(
            request,
            f"{updated} order(s) marked as Shipped"
        )
    mark_shipped.short_description = "Mark selected orders as Shipped"

    # 🔹 Admin Action: Mark Delivered
    def mark_delivered(self, request, queryset):
        queryset = queryset.filter(status="shipped")
        updated = queryset.update(status="delivered")
        self.message_user(
            request,
            f"{updated} order(s) marked as Delivered"
        )
    mark_delivered.short_description = "Mark selected orders as Delivered"

    def status_badge(self, obj):
        colors = {
        "placed": "orange",
        "shipped": "blue",
        "delivered": "green",
        "cancelled": "red",
    }
        return format_html(
        '<b style="color:{}">{}</b>',
        colors.get(obj.status, "black"),
        obj.status.upper()
    )


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ("quantity", "unit", "price")

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category")
    search_fields = ("name",)
    inlines = [ProductVariantInline]

class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("product", "quantity", "unit", "mrp", "price", "stock")

admin.site.register(ProductVariant, ProductVariantAdmin)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "variant",
        "return_status",
        "return_reason",
    )
    list_filter = ("return_status",)