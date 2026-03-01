from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from warehouse.models import Supplier



class Category(models.Model):
    name = models.CharField(max_length=100)
    icon = models.ImageField(upload_to="category_icons/", blank=True, null=True)
    def __str__(self):
        return self.name




class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="products/", blank=True, null=True)

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products"
    )

    # ✅ Added to match admin.py
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products"
    )

    # ✅ Added to match admin.py
    minimum_stock = models.PositiveIntegerField(default=5)

    def __str__(self):
        return self.name

    # Cheapest / default variant
    @property
    def first_variant(self):
        return self.variants.order_by("price").first()

    @property
    def display_price(self):
        v = self.first_variant
        return v.price if v else None

    @property
    def display_mrp(self):
        v = self.first_variant
        return v.mrp if v else None

    @property
    def discount_percent(self):
        v = self.first_variant
        if v and v.mrp and v.mrp > v.price:
            return int(((v.mrp - v.price) / v.mrp) * 100)
        return 0

    @property
    def display_quantity(self):
        v = self.first_variant
        return f"{v.quantity}{v.unit}" if v else None


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wishlist")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlisted")
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"
    
class ProductVariant(models.Model):
    UNIT_CHOICES = [
        ("ml", "Millilitre"),
        ("l", "Litre"),
        ("g", "Gram"),
        ("kg", "Kilogram"),
        ("pcs", "Pieces"),
    ]

    product = models.ForeignKey(
        Product,
        related_name="variants",
        on_delete=models.CASCADE
    )

    quantity = models.DecimalField(max_digits=6, decimal_places=2)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES)

    mrp = models.DecimalField(

        
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )

    price = models.DecimalField(max_digits=8, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} - {self.quantity}{self.unit}"

    @property
    def discount_percent(self):
        if self.mrp and self.mrp > self.price:
            return int(((self.mrp - self.price) / self.mrp) * 100)
        return 0



class Order(models.Model):
    STATUS_CHOICES = [
        ("placed", "Placed"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
        ("returned", "Returned"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_amount = models.DecimalField(
    max_digits=10,
    decimal_places=2,
    default=0
)
    PAYMENT_CHOICES = [
        ("cod", "Cash on Delivery"),
        ("upi", "UPI"),
        ("razorpay", "Razorpay"), 
        ("card", "Card"),
        ("netbanking", "Net Banking"),
    ]

    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
    upi_app = models.CharField(max_length=20, blank=True, null=True)
    estimated_delivery = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="placed"
    )
    PAYMENT_STATUS_CHOICES = [
    ("pending", "Pending"),
    ("completed", "Completed"),
    ("failed", "Failed"),
]

    payment_status = models.CharField(
    max_length=20,
    choices=PAYMENT_STATUS_CHOICES,
    default="pending"
)

    created_at = models.DateTimeField(auto_now_add=True)
    mrp_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    item_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    coupon_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    return_requested = models.BooleanField(default=False)
    return_reason = models.CharField(max_length=100, blank=True, null=True)
    return_comment = models.TextField(blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_order_id = models.CharField(max_length=255, blank=True, null=True)


    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    return_status = models.CharField(
        max_length=30,
        choices=[
            ('none', 'None'),
            ('requested', 'Requested'),
            ('pickup_scheduled', 'Pickup Scheduled'),
            ('picked', 'Picked'),
            ('refund_initiated', 'Refund Initiated'),
            ('refund_completed', 'Refund Completed'),
        ],
        default='none'
    )
    return_reason = models.CharField(max_length=100, blank=True, null=True)
    return_comment = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.variant} x {self.quantity}"

from django.utils import timezone

class ProductRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    rating = models.IntegerField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("user", "product")

    def __str__(self):
        return f"{self.product.name} - {self.rating}★ by {self.user.username}"


