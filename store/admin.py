






from django.contrib import admin
from django.utils.html import format_html
from django.utils.timezone import now
from datetime import timedelta

from .models import (
    Category,
    Product,
    ProductVariant,
    Order,
    OrderItem
)

# =========================
# CATEGORY ADMIN
# =========================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


# =========================
# ORDER ITEM INLINE
# =========================
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = ("variant", "quantity", "price")


# =========================
# ORDER ADMIN
# =========================
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
    date_hierarchy = "created_at"

    readonly_fields = (
        "user",
        "total_amount",
        "payment_method",
        "address",
        "created_at",
    )

    inlines = [OrderItemInline]
    actions = ["mark_shipped", "mark_delivered"]

    # 🔹 Address preview
    def short_address(self, obj):
        return obj.address[:40] + "..." if obj.address else "-"
    short_address.short_description = "Address"

    # 🔹 Order status badge
    def status_badge(self, obj):
        colors = {
            "placed": "#ff9800",
            "shipped": "#2196f3",
            "delivered": "#4caf50",
            "cancelled": "#f44336",
        }
        return format_html(
            '<span style="font-weight:600;color:{}">{}</span>',
            colors.get(obj.status, "black"),
            obj.status.upper()
        )
    status_badge.short_description = "Status"

    # 🔹 Admin Action: Mark Shipped
    def mark_shipped(self, request, queryset):
        queryset = queryset.filter(status="placed")
        updated = queryset.update(
            status="shipped",
            estimated_delivery=now().date() + timedelta(days=3)
        )
        self.message_user(request, f"{updated} order(s) marked as Shipped")
    mark_shipped.short_description = "🚚 Mark selected orders as Shipped"

    # 🔹 Admin Action: Mark Delivered
    def mark_delivered(self, request, queryset):
        queryset = queryset.filter(status="shipped")
        updated = queryset.update(status="delivered")
        self.message_user(request, f"{updated} order(s) marked as Delivered")
    mark_delivered.short_description = "✅ Mark selected orders as Delivered"


# =========================
# PRODUCT VARIANT INLINE
# =========================
class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ("quantity", "unit", "mrp", "price", "stock")
    show_change_link = True


# =========================
# PRODUCT ADMIN
# =========================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "supplier", "minimum_stock")
    list_editable = ('minimum_stock',)
    list_filter = ("category", "supplier")
    search_fields = ("name",)
    inlines = [ProductVariantInline]


# =========================
# PRODUCT VARIANT ADMIN
# =========================
@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "quantity",
        "unit",
        "mrp",
        "price",
        "stock",
        "stock_status",
    )
    list_filter = ("unit",)
    search_fields = ("product__name",)

    def stock_status(self, obj):
        if obj.stock <= 5:
            return format_html(
            '<span style="color:red">{}</span>',
            'LOW'
        )
        return format_html(
        '<span style="color:green">{}</span>',
        'OK'
    )



# =========================
# ORDER ITEM ADMIN
# =========================
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "variant",
        "quantity",
        "price",
        "return_status",
        "return_reason",
    )
    list_filter = ("return_status",)
    search_fields = ("order__id", "variant__product__name")


from django.contrib import admin
from .models import Product, Category
from warehouse.models import Supplier

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "phone")
    search_fields = ("name",)


