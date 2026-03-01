from django.shortcuts import render
from .models import Product, Order

def admin_dashboard(request):
    context = {
        'total_products': Product.objects.count(),
        'total_orders': Order.objects.count(),
        'pending_orders': Order.objects.filter(status='Pending').count(),
    }
    return render(request, 'admin/dashboard.html', context)
