from django.db import models
from django.contrib.auth.models import User


class DeliveryPartner(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_online = models.BooleanField(default=False)
    phone = models.CharField(max_length=15)

    profile_photo = models.ImageField(
        upload_to='delivery_profiles/',
        null=True,
        blank=True
    )

    vehicle_type = models.CharField(max_length=50 ,null=True, blank=True)
    vehicle_number = models.CharField(max_length=20, null=True, blank=True)

    license_number = models.CharField(max_length=50, null=True, blank=True)

    id_proof = models.ImageField(
        upload_to='delivery_documents/',
        null=True,
        blank=True
    )

    availability = models.BooleanField(default=True)

    current_location = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    joined_date = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('suspended', 'Suspended')
        ],
        default='active'
    )

    def __str__(self):
        return self.user.username