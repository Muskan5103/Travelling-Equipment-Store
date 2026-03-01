# def cart_count(request):
#     cart = request.session.get("cart", {})
#     return {
#         "cart_count": sum(cart.values())
#     }


def cart_count(request):
    cart = request.session.get("cart", {})

    # ✅ CLEAN INVALID / ZERO ITEMS
    clean_cart = {
        str(k): int(v)
        for k, v in cart.items()
        if str(k).isdigit() and isinstance(v, int) and v > 0
    }

    # ✅ Update session only if needed
    if cart != clean_cart:
        request.session["cart"] = clean_cart
        request.session.modified = True

    return {
        "cart_count": sum(clean_cart.values())
    }

from .models import Order, Product
from django.db.models import Sum, Count
from django.db.models.functions import TruncDay, TruncMonth

def admin_dashboard_data(request):
    if not request.user.is_staff:
        return {}

    orders_per_day = (
        Order.objects
        .annotate(day=TruncDay("created_at"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )

    revenue_per_month = (
        Order.objects
        .filter(status="delivered")
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(total=Sum("total_amount"))
        .order_by("month")
    )

    return {
        "total_orders": Order.objects.count(),
        "pending_orders": Order.objects.filter(status="placed").count(),
        "total_products": Product.objects.count(),
        "total_revenue": Order.objects.filter(status="delivered")
            .aggregate(Sum("total_amount"))["total_amount__sum"] or 0,
        "recent_orders": Order.objects.order_by("-id")[:5],
        "orders_per_day": list(orders_per_day),
        "revenue_per_month": list(revenue_per_month),
    }

