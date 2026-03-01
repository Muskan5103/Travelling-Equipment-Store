from django import forms
from .models import InwardStock

class InwardStockForm(forms.ModelForm):
    class Meta:
        model = InwardStock
        fields = [
            "supplier",
            "variant",
            "quantity_received",
            "purchase_price",
            "invoice_number",
        ]

from django import forms
from .models import Supplier

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = '__all__'

from django import forms
from .models import ReturnDamage


class ReturnDamageForm(forms.ModelForm):
    class Meta:
        model = ReturnDamage
        fields = '__all__'

