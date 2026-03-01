from django.db.models import F
from store.models import ProductVariant

def stock_notifications(request):

    low_stock_count = ProductVariant.objects.filter(
        stock__lte=F('product__minimum_stock'),
        stock__gt=0
    ).count()

    out_of_stock_count = ProductVariant.objects.filter(
        stock=0
    ).count()

    return {
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count
    }
