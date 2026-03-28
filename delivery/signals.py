from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import DeliveryPartner

@receiver(post_save, sender=User)
def create_partner(sender, instance, created, **kwargs):
    if created:
        DeliveryPartner.objects.create(user=instance)