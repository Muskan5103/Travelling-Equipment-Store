from pyexpat.errors import messages

from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from store.models import Order
from warehouse import models
from .models import DeliveryPartner
from django.shortcuts import render, redirect
from .models import DeliveryPartner
from django.utils import timezone
from datetime import timedelta



from django.contrib import messages


from django.utils import timezone
from datetime import timedelta

@login_required
def delivery_dashboard(request):

    if not DeliveryPartner.objects.filter(user=request.user).exists():
        return redirect("home")

    partner = DeliveryPartner.objects.get(user=request.user)

    orders = Order.objects.filter(
    delivery_partner=partner
).exclude(status="delivered")

    delivered_orders = Order.objects.filter(
        delivery_partner=partner,
        status="delivered"
    )
    new_orders = orders.filter(delivery_response="pending")

    if new_orders.exists() and not request.session.get("notified"):
        messages.info(request, "🔔 New order available!")
        request.session["notified"] = True
    today_completed = delivered_orders.count()
    today_earnings = today_completed * 30

    weekly_completed = delivered_orders.count()
    weekly_earnings = weekly_completed * 30

    return render(request, "delivery/dashboard.html", {
        "partner": partner,
        "orders": orders,
        "today_completed": today_completed,
        "today_earnings": today_earnings,
        "weekly_completed": weekly_completed,
        "weekly_earnings": weekly_earnings
    })

from django.shortcuts import get_object_or_404

@login_required
def update_status(request, order_id, status):

    partner = DeliveryPartner.objects.get(user=request.user)

    order = get_object_or_404(
        Order,
        id=order_id,
        delivery_partner=partner
    )

    order.status = status
    order.save()

    return redirect("/delivery/dashboard/")


from django.shortcuts import render, redirect
from .models import DeliveryPartner

def edit_delivery_profile(request):

    partner = DeliveryPartner.objects.get(user=request.user)

    if request.method == "POST":

        partner.phone = request.POST.get("phone")
        partner.vehicle_type = request.POST.get("vehicle_type")
        partner.vehicle_number = request.POST.get("vehicle_number")
        partner.license_number = request.POST.get("license_number")
        partner.current_location = request.POST.get("current_location")

        availability = request.POST.get("availability")
        partner.availability = True if availability == "True" else False

        if request.FILES.get("profile_photo"):
            partner.profile_photo = request.FILES.get("profile_photo")

        if request.FILES.get("id_proof"):
            partner.id_proof = request.FILES.get("id_proof")

        partner.save()

        return redirect("/delivery/profile/")

    return render(request,"delivery/edit_profile.html",{"partner":partner})

from django.shortcuts import render
from .models import DeliveryPartner

def delivery_profile(request):

    partner = DeliveryPartner.objects.get(user=request.user)

    return render(request, "delivery/profile.html", {
        "partner": partner
    })



from django.contrib.auth.decorators import login_required
from store.models import Order
from .models import DeliveryPartner

@login_required
def delivery_history(request):

    partner = DeliveryPartner.objects.get(user=request.user)

    history_orders = Order.objects.filter(
        delivery_partner=partner,
        status="delivered"
    ).order_by("-created_at")

    return render(request, "delivery/history.html", {
        "orders": history_orders
    })

from django.shortcuts import get_object_or_404, redirect
from django.core.mail import send_mail
@login_required
def accept_order(request, order_id):

    partner = DeliveryPartner.objects.get(user=request.user)

    order = get_object_or_404(Order, id=order_id)

    order.delivery_partner = partner
    order.delivery_response = "accepted"
    order.status = "packed"
    if not order.delivery_otp:
        order.generate_otp()
        order.save()
        send_mail(
        subject="Delivery OTP",
        message=f"""
    Hello {order.user.username},

    Your delivery OTP is: {order.delivery_otp}

    Please share this OTP with delivery partner.

    Thanks,
    Trek Ready 🚚
    """,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[order.user.email],
        fail_silently=False,
    )
    
    return redirect("/delivery/dashboard/")


@login_required
def reject_order(request, order_id):

    order = get_object_or_404(Order, id=order_id)

    order.delivery_partner = None
    order.delivery_response = "rejected"

    order.save()

    return redirect("/delivery/dashboard/")


from django.http import JsonResponse

@login_required



def check_new_orders(request):
    try:
        partner = DeliveryPartner.objects.get(user=request.user)

        count = Order.objects.filter(
            delivery_partner=partner,
            status="packed"
        ).count()

        return JsonResponse({
            "new_orders": count
        })

    except DeliveryPartner.DoesNotExist:
        return JsonResponse({"new_orders": 0})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

from django.shortcuts import render, get_object_or_404
from store.models import Order

def order_detail(request, order_id):

    order = get_object_or_404(Order, id=order_id)
    

    return render(request, "delivery/order_detail.html", {
    "order": order,
    "items": order.items.all()
})


from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import DeliveryPartner

@login_required
def toggle_status(request):
    partner = DeliveryPartner.objects.get(user=request.user)

    # 🔥 TOGGLE STATUS (IMPORTANT)
    partner.is_online = not partner.is_online
    partner.save()

    return JsonResponse({
        "status": "online" if partner.is_online else "offline"
    })


@login_required
def get_status(request):
    partner = DeliveryPartner.objects.get(user=request.user)
    return JsonResponse({
        "status": "online" if partner.is_online else "offline"
    })


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

def verify_delivery(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == "POST":
        entered_otp = request.POST.get("otp")
        photo = request.FILES.get("photo")

        if entered_otp == order.delivery_otp:
            order.delivery_image = photo
            order.status = "delivered"
            order.save()

            messages.success(request, "✅ Delivery completed successfully!")
            return redirect("/delivery/dashboard/")

        else:
            messages.error(request, "❌ Invalid OTP")

    return render(request, 'delivery/verify_delivery.html', {'order': order})