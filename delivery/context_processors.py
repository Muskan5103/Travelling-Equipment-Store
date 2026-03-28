from .models import DeliveryPartner

def delivery_partner(request):
    if request.user.is_authenticated:
        return {
            "is_delivery_partner": DeliveryPartner.objects.filter(user=request.user).exists()
        }
    return {"is_delivery_partner": False}