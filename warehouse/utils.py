from django.core.mail import send_mail
from .models import ProductLocation


def send_low_stock_alert():

    low_items = ProductLocation.objects.filter(quantity__lte=5)

    if low_items.exists():
        message = "Low Stock Alert:\n\n"

        for item in low_items:
            message += f"{item.product.name} - {item.quantity}\n"

        send_mail(
            "Low Stock Alert",
            message,
            "your_email@gmail.com",
            ["admin@email.com"],
        )