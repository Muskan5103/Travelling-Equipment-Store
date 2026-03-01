from django.db import models


class WarehouseStock(models.Model):
    product = models.OneToOneField('store.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    min_stock = models.PositiveIntegerField(default=5)
    def stock_status(self):
        if self.quantity == 0:
            return "Out of Stock"
        elif self.quantity <= self.min_stock:
            return "Low Stock"
        return "In Stock"

    def __str__(self):
        return f"{self.product.name} - {self.quantity}"


class Supplier(models.Model):
    supplier_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True
    )
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address = models.TextField()
    equipment_supplied = models.TextField()

    def __str__(self):
        return self.name


class StockIn(models.Model):
    product = models.ForeignKey('store.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now_add=True)

    


# class StockOut(models.Model):
#     product = models.ForeignKey('store.Product', on_delete=models.CASCADE)
#     quantity = models.PositiveIntegerField()
#     date = models.DateTimeField(auto_now_add=True)
#     reason = models.CharField(max_length=100, default="Order")
from django.db import transaction
from django.core.exceptions import ValidationError




class StockOut(models.Model):
    variant = models.ForeignKey(
    'store.ProductVariant',
    on_delete=models.CASCADE,
    null=True,
    blank=True
)


    quantity = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=100, default="Order")

    def save(self, *args, **kwargs):

        # Only reduce stock when creating new record
        if not self.pk:

            if self.variant.stock < self.quantity:
                raise ValidationError("Not enough stock available!")

            with transaction.atomic():

                # 🔻 Reduce stock
                self.variant.stock -= self.quantity
                self.variant.save()

                super().save(*args, **kwargs)

                # 🔁 Create stock transaction entry
                StockTransaction.objects.create(
                    product_variant=self.variant,
                    quantity=self.quantity,
                    transaction_type='OUT'
                )
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return f"Stock Out - {self.variant} ({self.quantity})"


class InwardStock(models.Model):
    supplier = models.ForeignKey(
        'warehouse.Supplier',
        on_delete=models.SET_NULL,
        null=True
    )

    variant = models.ForeignKey(
        'store.ProductVariant',
        on_delete=models.CASCADE
    )

    quantity_received = models.PositiveIntegerField()
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    invoice_number = models.CharField(max_length=50, blank=True)
    received_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Inward - {self.variant} ({self.quantity_received})"




from django.db import transaction
from django.core.exceptions import ValidationError

class OutwardStock(models.Model):
    order_item = models.ForeignKey(
        'store.OrderItem',
        on_delete=models.CASCADE
    )

    variant = models.ForeignKey(
        'store.ProductVariant',
        on_delete=models.CASCADE
    )

    quantity_issued = models.PositiveIntegerField()
    issued_date = models.DateTimeField(auto_now_add=True)

    destination = models.CharField(
        max_length=50,
        choices=[
            ("customer", "Customer"),
            ("store", "Store"),
        ]
    )

    
def save(self, *args, **kwargs):

    # Only reduce stock when creating NEW record
    if not self.pk:

        if self.variant.stock < self.quantity_issued:
            raise ValidationError("Not enough stock available!")

        with transaction.atomic():

            # 🔻 Reduce stock
            self.variant.stock -= self.quantity_issued
            self.variant.save()

            super().save(*args, **kwargs)

            # 📊 Create transaction history
            StockTransaction.objects.create(
                product_variant=self.variant,
                quantity=self.quantity_issued,
                transaction_type='OUT'
            )

    else:
        # If updating existing record → just save normally
        super().save(*args, **kwargs)



    def __str__(self):
        return f"Outward - {self.variant} ({self.quantity_issued})"

from django.db import models
from django.utils import timezone







class ReturnDamage(models.Model):

    STATUS_CHOICES = [
        ('Returned', 'Returned'),
        ('Damaged', 'Damaged'),
    ]

    ACTION_CHOICES = [
        ('Pending', 'Pending'),
        ('Repairing', 'Repairing'),
        ('Repaired', 'Repaired'),
        ('Replaced', 'Replaced'),
        ('Discarded', 'Discarded'),
    ]

    product = models.ForeignKey("store.Product", on_delete=models.CASCADE)

    customer_name = models.CharField(max_length=200)
    quantity = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    damage_description = models.TextField(blank=True, null=True)
    action_status = models.CharField(max_length=20, choices=ACTION_CHOICES, default='Pending')
    date_reported = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.status}"

from django.utils import timezone

class Warehouse(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    capacity = models.IntegerField(default=0)  # ✅ important
    created_at = models.DateTimeField(default=timezone.now)  # ✅ important


    def __str__(self):
        return self.name

class Section(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="sections")
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=timezone.now)
    def __str__(self):
        return f"{self.warehouse.name} - {self.name}"


class Rack(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="racks")
    rack_number = models.CharField(max_length=50)
    capacity = models.IntegerField(default=100)
    created_at = models.DateTimeField(default=timezone.now)
    def __str__(self):
        return f"{self.section.name} - Rack {self.rack_number}"

class ProductLocation(models.Model):
    product = models.ForeignKey("store.Product", on_delete=models.CASCADE)
    rack = models.ForeignKey(Rack, on_delete=models.CASCADE)
    quantity = models.IntegerField()

    def __str__(self):
        return f"{self.product.name} → {self.rack}"


from django.conf import settings
from django.utils import timezone

class StockTransaction(models.Model):

    TRANSACTION_TYPE = (
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
    )

    product_variant = models.ForeignKey(
        'store.ProductVariant',
        on_delete=models.CASCADE
    )

    quantity = models.PositiveIntegerField()
    transaction_type = models.CharField(
        max_length=3,
        choices=TRANSACTION_TYPE
    )

    created_at = models.DateTimeField(default=timezone.now)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.product_variant.product.name} - {self.transaction_type} - {self.quantity}"

from django.db import transaction
from django.core.exceptions import ValidationError
class StockTransfer(models.Model):

    variant = models.ForeignKey(
        'store.ProductVariant',
        on_delete=models.CASCADE
    )

    from_rack = models.ForeignKey(
        'warehouse.Rack',
        on_delete=models.CASCADE,
        related_name="transfer_from"
    )

    to_rack = models.ForeignKey(
        'warehouse.Rack',
        on_delete=models.CASCADE,
        related_name="transfer_to"
    )

    quantity = models.PositiveIntegerField()

    transferred_at = models.DateTimeField(default=timezone.now)
    

    def save(self, *args, **kwargs):

        if not self.pk:

            with transaction.atomic():

                # 🔍 Get source location
                try:
                    source_location = ProductLocation.objects.get(
                        product=self.variant.product,
                        rack=self.from_rack
                    )
                except ProductLocation.DoesNotExist:
                    raise ValidationError("Product not found in source rack!")

                if source_location.quantity < self.quantity:
                    raise ValidationError("Not enough stock in source rack!")

                # 🔻 Reduce stock from source
                source_location.quantity -= self.quantity
                source_location.save()

                # 🔺 Add stock to destination
                destination_location, created = ProductLocation.objects.get_or_create(
                    product=self.variant.product,
                    rack=self.to_rack,
                    defaults={'quantity': 0}
                )

                destination_location.quantity += self.quantity
                destination_location.save()

                # 📊 Create OUT transaction
                StockTransaction.objects.create(
                    product_variant=self.variant,
                    quantity=self.quantity,
                    transaction_type='OUT'
                )

                # 📊 Create IN transaction
                StockTransaction.objects.create(
                    product_variant=self.variant,
                    quantity=self.quantity,
                    transaction_type='IN'
                )

                super().save(*args, **kwargs)

        else:
            super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.variant} → {self.quantity}"
