from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import OrderItem
from .utils.email_utils import send_user_email
from .models import Order

@receiver(post_save, sender=Order)
def order_status_email(sender, instance, created, **kwargs):
    if instance.status == "shipped":
        send_user_email(
            subject="🚚 Your Order Has Been Shipped",
            message=f"""
Hi {instance.user.username},

Good news! 🎉  
Your order #{instance.id} has been shipped.

It will reach you soon.

Thank you for shopping with us!
""",
            to_email=instance.user.email
        )

    elif instance.status == "delivered":
        send_user_email(
            subject="📦 Order Delivered",
            message=f"""
Hi {instance.user.username},

Your order #{instance.id} has been delivered successfully.

Thank you for shopping with us!
""",
            to_email=instance.user.email
        )



@receiver(post_save, sender=OrderItem)
def return_status_email(sender, instance, created, **kwargs):

    if instance.return_status == "pickup_scheduled":
        subject = "📦 Return Pickup Scheduled"
        msg = f"Pickup has been scheduled for {instance.variant.product.name}"

    elif instance.return_status == "picked":
        subject = "🚚 Item Picked Successfully"
        msg = f"Your item {instance.variant.product.name} has been picked."

    elif instance.return_status == "refund_initiated":
        subject = "💸 Refund Initiated"
        msg = f"Refund initiated for {instance.variant.product.name}"

    elif instance.return_status == "refund_completed":
        subject = "✅ Refund Completed"
        msg = f"Refund completed for {instance.variant.product.name}"

    else:
        return

    send_user_email(
        subject=subject,
        message=f"""
Hi {instance.order.user.username},

{msg}

Order ID: {instance.order.id}
""",
        to_email=instance.order.user.email
    )

from warehouse.models import OutwardStock


@receiver(post_save, sender=OrderItem)
def create_outward_stock(sender, instance, created, **kwargs):
    if created:
        OutwardStock.objects.create(
            order_item=instance,
            variant=instance.variant,
            quantity_issued=instance.quantity,
            destination="customer"
        )
