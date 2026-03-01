from django.db.models.signals import post_save
from django.dispatch import receiver
from store.models import Product
from .models import WarehouseStock

@receiver(post_save, sender=Product)
def create_warehouse_stock(sender, instance, created, **kwargs):
    if created:
        WarehouseStock.objects.create(product=instance)


from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import InwardStock
from .models import OutwardStock

@receiver(post_save, sender=InwardStock)
def increase_stock(sender, instance, created, **kwargs):
    if created:
        variant = instance.variant
        variant.stock += instance.quantity_received
        variant.save()


@receiver(post_save, sender=OutwardStock)
def decrease_stock(sender, instance, created, **kwargs):
    if created:
        variant = instance.variant
        variant.stock -= instance.quantity_issued
        variant.save()


from django.db.models.signals import post_save
from django.dispatch import receiver
from store.models import OrderItem
from .models import OutwardStock

@receiver(post_save, sender=OrderItem)
def create_outward_stock(sender, instance, created, **kwargs):
    if created:
        OutwardStock.objects.create(
            order_item=instance,
            variant=instance.variant,
            quantity_issued=instance.quantity,
            destination="customer"
        )

        # 🔽 Reduce stock
        instance.variant.stock -= instance.quantity
        instance.variant.save()
