from urllib import request
from django.shortcuts import render, get_object_or_404, redirect
from .models import Product,Category
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Order, OrderItem
from .models import ProductVariant
from .models import Product
from django.http import FileResponse
from .utils.invoice import generate_invoice
import os
from django.contrib import messages
from .models import Product, Order, OrderItem, ProductRating
from decimal import Decimal
from django.db.models import Q
from warehouse.models import ReturnDamage, WarehouseStock, StockOut
from django.db.models import Avg, Count, OuterRef, Subquery
from .models import ProductRating
from store.utils.whatsapp import send_whatsapp_message

from django.db.models import Avg, Count, OuterRef, Subquery
from .models import ProductRating


from django.shortcuts import render, redirect
from .models import Category, Product, Wishlist

from django.db.models import Avg, Count, Prefetch

def home(request):

    if request.user.is_authenticated and request.user.is_staff:
        return redirect('warehouse_dashboard')

    if request.user.is_authenticated and DeliveryPartner.objects.filter(user=request.user).exists():
        return redirect("/delivery/dashboard/")

    category_id = request.GET.get("category")
    query = request.GET.get("q")

    # Annotated products
    rated_products = Product.objects.annotate(
        avg_rating=Avg("productrating__rating"),
        review_count=Count("productrating", distinct=True)
    )

    # Prefetch products with ratings into categories
    categories = Category.objects.prefetch_related(
        Prefetch("products", queryset=rated_products)
    ).order_by("name")

    products = rated_products
    active_category = None

    if category_id:
        try:
            category_id = int(category_id)
            products = rated_products.filter(category_id=category_id)
            active_category = category_id
        except (ValueError, TypeError):
            products = Product.objects.none()

    if query:
        products = products.filter(name__icontains=query)

    wishlist_product_ids = []

    if request.user.is_authenticated:
        wishlist_product_ids = Wishlist.objects.filter(
            user=request.user
        ).values_list("product_id", flat=True)

    context = {
        "categories": categories,
        "products": products,
        "active_category": active_category,
        "query": query,
        "wishlist_product_ids": wishlist_product_ids,
    }

    return render(request, "store/home.html", context)

def with_ratings(queryset):
    return queryset.annotate(
        avg_rating=Avg('productrating__rating'),
        review_count=Count('productrating')
    )

def admin_dashboard(request):
    context = {
        "total_orders": Order.objects.count(),
        "total_products": Product.objects.count(),
        "total_revenue": Order.objects.filter(status="delivered")
                            .aggregate(Sum("total_amount"))["total_amount__sum"] or 0,
        "pending_orders": Order.objects.filter(status="placed").count(),
        "recent_orders": Order.objects.order_by("-id")[:5],
    }
    return render(request, "admin/dashboard.html", context)



from django.shortcuts import render, get_object_or_404
from .models import Product

def product_detail(request, product_id):
    product = Product.objects.annotate(
    avg_rating=Avg('productrating__rating'),
    review_count=Count('productrating')
).get(id=product_id)

    base_variants = product.variants.all().order_by("price")

    display_variants = []

    for v in base_variants:
        # 1x
        display_variants.append({
            "label": v.quantity,
            "price": v.price,
            "mrp": v.mrp,
            "variant_id": v.id,
            "multiplier": 1
        })

        # 2x
        display_variants.append({
            "label": f"2 × {v.quantity}",
            "price": v.price * 2,
            "mrp": v.mrp * 2,
            "variant_id": v.id,
            "multiplier": 2
        })

        # 4x
        display_variants.append({
            "label": f"4 × {v.quantity}",
            "price": v.price * 4,
            "mrp": v.mrp * 4,
            "variant_id": v.id,
            "multiplier": 4
        })

    # recommendations (keep your logic)
    recommendations = (
    Product.objects
    .exclude(id=product_id)
    .prefetch_related("variants")
    .annotate(
        avg_rating=Avg('productrating__rating'),
        review_count=Count('productrating__id')
    )
)

    for p in recommendations:
        p.sorted_variants = sorted(
            p.variants.all(),
            key=lambda v: v.price
        )

    return render(request, "store/product_detail.html", {
        "product": product,
        "variants": display_variants,
        "recommendations": recommendations,
    })



from .models import Product, Wishlist
from django.views.decorators.http import require_POST

@login_required
@require_POST
def toggle_wishlist(request, product_id):
    product = Product.objects.get(id=product_id)

    item = Wishlist.objects.filter(user=request.user, product=product)

    if item.exists():
        item.delete()
        return JsonResponse({"added": False})
    else:
        Wishlist.objects.create(user=request.user, product=product)
        return JsonResponse({"added": True})


# @login_required
# def wishlist_page(request):
#     wishlist_items = Wishlist.objects.filter(user=request.user).select_related("product")
#     return render(request, "store/wishlist.html", {
#     "wishlist_items": wishlist_items
# })
from django.db.models import Avg, Count



@login_required
def wishlist_page(request):

    wishlist_items = (
        Wishlist.objects
        .filter(user=request.user)
        .select_related("product")
        .annotate(
            avg_rating=Avg("product__productrating__rating"),
            review_count=Count("product__productrating")
        )
    )

    return render(request, "store/wishlist.html", {
        "wishlist_items": wishlist_items
    })



def add_to_cart(request):
    variant_id = request.GET.get("variant_id")
    qty = int(request.GET.get("qty", 1))

    if not variant_id or variant_id == "null":
        return redirect(request.META.get("HTTP_REFERER", "home"))

    cart = request.session.get("cart", {})

    variant_id = str(variant_id)  # ✅ always string

    cart[variant_id] = cart.get(variant_id, 0) + qty

    request.session["cart"] = cart
    request.session.modified = True

    return redirect(request.META.get("HTTP_REFERER", "home"))





@login_required
def cart_view(request):
    cart = request.session.get("cart", {})
    applied_coupon = request.session.get("coupon")

    items = []

    total_price = Decimal("0.00")   # total selling price
    total_mrp = Decimal("0.00")     # total MRP

    for variant_id, qty in cart.items():
        if not str(variant_id).isdigit():
            continue

        variant = ProductVariant.objects.select_related("product").get(id=variant_id)

        price_total = variant.price * qty
        mrp_total = (variant.mrp * qty) if variant.mrp else price_total

        total_price += price_total
        total_mrp += mrp_total

        items.append({
            "variant_id": variant.id,
            "product_name": variant.product.name,
            "variant": f"{variant.quantity} {variant.unit}",
            "price": variant.price,
            "mrp": variant.mrp,
            "discount": variant.discount_percent,
            "qty": qty,
            "subtotal": price_total,
            "image": variant.product.image.url if variant.product.image else "",
        })

    # 🟢 ITEM DISCOUNT (MRP - Selling)
    item_discount = total_mrp - total_price

    # 🎟️ AVAILABLE COUPONS (ADD MORE HERE)
    COUPONS = {
        "SAVE10": {
            "type": "flat",
            "value": Decimal("10"),
            "min_amount": Decimal("100"),
        },
        "SAVE20": {
            "type": "flat",
            "value": Decimal("20"),
            "min_amount": Decimal("200"),
        },
        "BIGSAVE": {
            "type": "percent",
            "value": Decimal("15"),   # 15% OFF
            "max_discount": Decimal("100"),
            "min_amount": Decimal("300"),
        },
        "FREESHIP": {
            "type": "shipping",
            "value": Decimal("0"),
            "min_amount": Decimal("150"),
        },
        "NEW50": {
            "type": "flat",
            "value": Decimal("50"),
            "min_amount": Decimal("500"),
        },
    
    }


     # 🚚 DELIVERY FEE LOGIC
    delivery_fee = Decimal("0.00")

# FREE delivery above ₹199
    if total_price >= Decimal("199"):
        delivery_fee = Decimal("0.00")

# ₹20 delivery for mid orders
    # elif total_price >= Decimal("99"):
    #     delivery_fee = Decimal("20.00")
# ₹40 delivery for small orders
    else:
        delivery_fee = Decimal("40.00")

# 🎟️ FREESHIP coupon override
    if applied_coupon == "FREESHIP" and total_price >= Decimal("150"):
        delivery_fee = Decimal("0.00")
    # 🟢 COUPON CALCULATION
    
    coupon_discount = Decimal("0.00")
    coupon_valid = False

    if applied_coupon in COUPONS:
        coupon = COUPONS[applied_coupon]

        if total_price >= coupon["min_amount"]:
            coupon_valid = True
            
            if coupon["type"] == "flat":
                coupon_discount = coupon["value"]

            elif coupon["type"] == "percent":
                coupon_discount = (total_price * coupon["value"]) / Decimal("100")
                if "max_discount" in coupon:
                    coupon_discount = min(coupon_discount, coupon["max_discount"])
            elif coupon["type"] == "shipping":
                delivery_fee = Decimal("0.00")

    else:
        # ❌ cart not eligible → REMOVE coupon
        request.session.pop("coupon", None)
        applied_coupon = None
    

    # 💰 FINAL AMOUNT
    final_amount = total_price - coupon_discount + delivery_fee
    total_savings = item_discount + coupon_discount


    request.session["final_amount"] = str(final_amount)
    request.session["delivery_fee"] = str(delivery_fee)
    request.session["coupon_discount"] = str(coupon_discount)

    AVAILABLE_COUPONS = [
    {
        "code": "SAVE10",
        "desc": "Save ₹10 on orders above ₹100"
    },
    {
        "code": "SAVE20",
        "desc": "Save ₹20 on orders above ₹200"
    },
    {
        "code": "BIGSAVE",
        "desc": "Get 15% OFF up to ₹100 on orders above ₹300"
    },
    {
        "code": "FREESHIP",
        "desc": "Free delivery on orders above ₹150"
    },
    {
        "code": "NEW50",
        "desc": "Flat ₹50 OFF on orders above ₹500"
    },
]
    
    context = {
        "items": items,
        "cart_empty": len(items) == 0,

        # price summary
        "total_price": total_price,
        "total_mrp": total_mrp,
        "item_discount": item_discount,
        "coupon_discount": coupon_discount,
        "delivery_fee": delivery_fee,
        "final_amount": final_amount,
        "total_savings": total_savings,
        "applied_coupon": applied_coupon,
        "available_coupons": AVAILABLE_COUPONS,
        "coupon_valid": coupon_valid,

        # recommendations
        "recommendations": (
    Product.objects.exclude(
        id__in=[
            v.product.id
            for v in ProductVariant.objects.filter(id__in=cart.keys())
        ]
    )
    .annotate(
        avg_rating=Avg("productrating__rating"),
        review_count=Count("productrating", distinct=True)
    )
    .select_related("category")
    .prefetch_related("variants")
),
    }

    return render(request, "store/cart.html", context)


@login_required
def apply_coupon(request):
    if request.method == "POST":
        code = request.POST.get("coupon", "").upper().strip()

        # list of valid coupons
        VALID_COUPONS = ["SAVE10", "SAVE20", "BIGSAVE", "FREESHIP", "NEW50"]

        if code in VALID_COUPONS:
            request.session["coupon"] = code
        else:
            request.session.pop("coupon", None)

    return redirect("cart")





def calculate_cart_totals(request):
    from decimal import Decimal
    from .models import ProductVariant

    cart = request.session.get("cart", {})
    applied_coupon = request.session.get("coupon")

    total_price = Decimal("0.00")
    total_mrp = Decimal("0.00")

    for variant_id, qty in cart.items():
        variant = ProductVariant.objects.get(id=int(variant_id))

        subtotal = variant.price * qty
        mrp_total = (variant.mrp * qty) if variant.mrp else subtotal

        total_price += subtotal
        total_mrp += mrp_total

    # ✅ Item Discount
    item_discount = total_mrp - total_price

    # ✅ Coupon Logic
    COUPONS = {
        "SAVE10": {"type": "flat", "value": Decimal("10"), "min_amount": Decimal("100")},
        "SAVE20": {"type": "flat", "value": Decimal("20"), "min_amount": Decimal("200")},
        "BIGSAVE": {
            "type": "percent",
            "value": Decimal("15"),
            "max_discount": Decimal("100"),
            "min_amount": Decimal("300"),
        },
    }

    coupon_discount = Decimal("0.00")

    if applied_coupon in COUPONS:
        c = COUPONS[applied_coupon]
        if total_price >= c["min_amount"]:
            if c["type"] == "flat":
                coupon_discount = c["value"]
            elif c["type"] == "percent":
                coupon_discount = min(
                    (total_price * c["value"]) / 100,
                    c.get("max_discount", Decimal("99999"))
                )

    # ✅ Delivery Fee (from session or fixed)
    delivery_fee = Decimal(request.session.get("delivery_fee", "0.00"))

    # ✅ Final Amount
    final_amount = total_price - coupon_discount + delivery_fee

    return {
        "total_price": total_price,
        "total_mrp": total_mrp,
        "item_discount": item_discount,
        "coupon_discount": coupon_discount,
        "delivery_fee": delivery_fee,
        "final_amount": final_amount,
    }

@login_required
def update_cart(request, variant_id):
    action = request.GET.get("action")
    cart = request.session.get("cart", {})

    variant_id = str(variant_id)  # ✅ FIX

    if variant_id in cart:
        if action == "increase":
            cart[variant_id] += 1
        elif action == "decrease":
            cart[variant_id] -= 1
            if cart[variant_id] <= 0:
                del cart[variant_id]

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("cart")


@login_required
def remove_coupon(request):
    request.session.pop("coupon", None)
    return redirect("cart")


def remove_from_cart(request, variant_id):
    cart = request.session.get("cart", {})
    cart.pop(str(variant_id), None)
    request.session["cart"] = cart
    return redirect("cart")





from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from delivery.models import DeliveryPartner

def login_view(request):

    if request.method == "POST":

        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            return render(request, "store/login.html", {"error": "Invalid Email or Password"})

        user = authenticate(request, username=user_obj.username, password=password)

        if user is not None:
            login(request, user)

            # ✅ Handle "next" parameter FIRST
            next_url = request.GET.get("next")
            if next_url:
                return redirect(next_url)

            # ✅ Then role-based redirect
            if DeliveryPartner.objects.filter(user=user).exists():
                return redirect("/delivery/dashboard/")   # direct URL (no reverse issue)

            # Normal customer
            return redirect("home")

        else:
            return render(request, "store/login.html", {"error": "Invalid Email or Password"})

    return render(request, "store/login.html")

from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.shortcuts import render, redirect

def signup_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if User.objects.filter(email=email).exists():
            return render(request, "store/signup.html", {
                "error": "Email already registered"
            })

        username = email


        # ✅ If username exists, modify it
        if User.objects.filter(username=username).exists():
            username = username + str(User.objects.count())

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=name
        )

        # Authenticate
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("home")

    return render(request, "store/signup.html")




def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def checkout(request):
    cart = request.session.get("cart", {})
    applied_coupon = request.session.get("coupon")

    if not cart:
        return redirect("cart")

    items = []
    total_price = Decimal("0.00")
    total_mrp = Decimal("0.00")

    for variant_id, qty in cart.items():
        if not str(variant_id).isdigit():
            continue

        variant = ProductVariant.objects.select_related("product").get(id=int(variant_id))

        subtotal = variant.price * qty
        mrp_total = (variant.mrp * qty) if variant.mrp else subtotal

        total_price += subtotal
        total_mrp += mrp_total

        items.append({
            "variant": variant,
            "product": variant.product,
            "quantity": qty,
            "subtotal": subtotal,
        })

    # 🟢 ITEM DISCOUNT
    item_discount = total_mrp - total_price

    # 🎟️ SAME COUPONS AS CART
    COUPONS = {
        "SAVE10": {"type": "flat", "value": Decimal("10"), "min_amount": Decimal("100")},
        "SAVE20": {"type": "flat", "value": Decimal("20"), "min_amount": Decimal("200")},
        "BIGSAVE": {
            "type": "percent",
            "value": Decimal("15"),
            "max_discount": Decimal("100"),
            "min_amount": Decimal("300"),
        },
        "FREESHIP": {"type": "shipping", "value": Decimal("0"), "min_amount": Decimal("150")},
        "NEW50": {"type": "flat", "value": Decimal("50"), "min_amount": Decimal("500")},
    }

    # 🟢 COUPON DISCOUNT
    coupon_discount = Decimal("0.00")

    if applied_coupon in COUPONS:
        coupon = COUPONS[applied_coupon]

        if total_price >= coupon["min_amount"]:
            if coupon["type"] == "flat":
                coupon_discount = coupon["value"]

            elif coupon["type"] == "percent":
                coupon_discount = (total_price * coupon["value"]) / Decimal("100")
                coupon_discount = min(coupon_discount, coupon.get("max_discount", coupon_discount))

    # 💰 FINAL TOTAL
    # final_amount = total_price - coupon_discount
    total_savings = item_discount + coupon_discount
    final_amount = Decimal(request.session.get("final_amount", "0.00"))
    coupon_discount = Decimal(request.session.get("coupon_discount", "0.00"))
    delivery_fee = Decimal(request.session.get("delivery_fee", "0.00"))

    # 📮 ADDRESS HANDLING
    if request.method == "POST":
        address = request.POST.get("address")
        phone = request.POST.get("phone") 
        if not address:
            return render(request, "store/checkout.html", {
                "items": items,
                "final_amount": final_amount,
                "error": "Address is required",
            })

        request.session["address"] = address
        request.session["phone"] = phone
        return redirect("payment")

    return render(request, "store/checkout.html", {
        "items": items,
        "total_price": total_price,
        "item_discount": item_discount,
        "coupon_discount": coupon_discount,
        "final_amount": final_amount,
        "total_savings": total_savings,
        "applied_coupon": applied_coupon,
        "delivery_fee": delivery_fee,
    })





import time

import razorpay
from django.conf import settings
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

@login_required
def payment(request):
    
    print("KEY:", settings.RAZORPAY_KEY_ID)
    print("SECRET:", settings.RAZORPAY_KEY_SECRET)
    cart = request.session.get("cart", {})
    applied_coupon = request.session.get("coupon")

    if not cart:
        return redirect("cart")

    items = []
    total_price = Decimal("0.00")
    total_mrp = Decimal("0.00")

    for variant_id, qty in cart.items():
        if not str(variant_id).isdigit():
            continue

        variant = ProductVariant.objects.select_related("product").get(id=int(variant_id))

        subtotal = variant.price * qty
        mrp_total = (variant.mrp * qty) if variant.mrp else subtotal

        total_price += subtotal
        total_mrp += mrp_total

        items.append({
            "variant": variant,
            "product": variant.product,
            "quantity": qty,
            "subtotal": subtotal,
        })

    item_discount = total_mrp - total_price

    final_amount = Decimal(request.session.get("final_amount", "0.00"))
    coupon_discount = Decimal(request.session.get("coupon_discount", "0.00"))
    delivery_fee = Decimal(request.session.get("delivery_fee", "0.00"))

    total_savings = item_discount + coupon_discount

    # 🔥 RAZORPAY ORDER CREATION
    # Razorpay client
    if "razorpay_order_id" in request.session:
        del request.session["razorpay_order_id"]

# Razorpay client
    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    razorpay_amount = int(final_amount * 100)

    try:
        # Always create fresh order
        razorpay_order = client.order.create({
            "amount": razorpay_amount,
            "currency": "INR",
            "payment_capture": 1,
            "receipt": f"order_{request.user.id}_{int(time.time())}"
        })

        request.session["razorpay_order_id"] = razorpay_order["id"]

    except Exception as e:
        print("Razorpay Error:", e)
        messages.error(request, "Payment gateway error")
        return redirect("checkout")
        

   
        
    print("FINAL AMOUNT:", final_amount)
    print("RAZORPAY AMOUNT:", razorpay_amount)

    request.session["razorpay_order_id"] = razorpay_order["id"]
    request.session["total_mrp"] = str(total_mrp)
    request.session["item_discount"] = str(item_discount)
    request.session["coupon_discount"] = str(coupon_discount)
    request.session["delivery_fee"] = str(delivery_fee)
    request.session["final_amount"] = str(final_amount)
    

    return render(request, "store/payment.html", {
        "items": items,
        "total_price": total_price,
        "item_discount": item_discount,
        "coupon_discount": coupon_discount,
        "final_amount": final_amount,
        "total_savings": total_savings,
        "applied_coupon": applied_coupon,
        "delivery_fee": delivery_fee,

        # 👇 Razorpay data
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "razorpay_order_id": razorpay_order["id"],
        "razorpay_amount": razorpay_amount,
    })


@login_required
def process_payment(request):
    if request.method == "POST":
        payment_method = request.POST.get("payment_method")

        # ✅ Later: integrate Razorpay / Stripe
        request.session["cart"] = {}
        request.session.modified = True

        return redirect("order_success")






import json
from decimal import Decimal
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

@login_required
def place_order(request):
    if request.method != "POST":
        return redirect("cart")

    payment_method = request.POST.get("payment")  # 👈 FORM DATA

    if payment_method != "cod":
        return redirect("payment")

    cart = request.session.get("cart")
    address = request.session.get("address")

    if not cart or not address:
        return redirect("cart")

    mrp_total = Decimal("0.00")
    subtotal = Decimal("0.00")

    for variant_id, qty in cart.items():
        variant = ProductVariant.objects.get(id=int(variant_id))
        mrp_total += variant.mrp * qty
        subtotal += variant.price * qty

    delivery_fee = Decimal("40.00") if mrp_total < 199 else Decimal("0.00")
    coupon_discount = Decimal(request.session.get("coupon_discount", "0.00"))
    total_amount = subtotal - coupon_discount + delivery_fee

    order = Order.objects.create(
        user=request.user,
        payment_method="cod",
        payment_status="pending",
        address=address,
        phone=request.session.get("phone"),
        mrp_total=mrp_total,
        item_discount=mrp_total - subtotal,
        coupon_discount=coupon_discount,
        delivery_fee=delivery_fee,
        total_amount=total_amount,
    )

    for variant_id, qty in cart.items():
        variant = ProductVariant.objects.get(id=int(variant_id))
        product = variant.product

        # try:
        #     stock = WarehouseStock.objects.get(product=product)
        # except WarehouseStock.DoesNotExist:
        #     messages.error(request, f"{product.name} stock not found")
        #     return redirect("cart")

        # if stock.quantity < qty:
        #     messages.error(request, f"{product.name} is out of stock")
        #     return redirect("cart")
        if variant.stock < qty:
            messages.error(request, f"{variant.product.name} is out of stock")
            return redirect("cart")

        OrderItem.objects.create(
        order=order,
        variant=variant,
        quantity=qty,
        price=variant.price,
    )
        variant.stock -= qty
        variant.save()

    


    clear_checkout_session(request)

    return redirect("order_success")


from django.views.decorators.csrf import csrf_exempt




import json
import razorpay
from decimal import Decimal
from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt



@login_required
@csrf_exempt
def verify_razorpay_payment(request):

    if request.method != "POST":
        return JsonResponse({"status": "failed"})

    data = json.loads(request.body)

    payment_id = data.get("razorpay_payment_id")
    order_id = data.get("razorpay_order_id")
    signature = data.get("razorpay_signature")

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    # ✅ Verify Signature
    try:
        client.utility.verify_payment_signature({
            "razorpay_payment_id": payment_id,
            "razorpay_order_id": order_id,
            "razorpay_signature": signature,
        })
    except:
        return JsonResponse({"status": "failed"})

    cart = request.session.get("cart", {})
    address = request.session.get("address")

    if not cart:
        return JsonResponse({"status": "failed"})

    totals = calculate_cart_totals(request)

    # 🔥 CREATE ORDER HERE
    order = Order.objects.create(
        user=request.user,
        payment_method="razorpay",
        payment_status="completed",
        razorpay_payment_id=payment_id,
        razorpay_order_id=order_id,
        address=address,
        total_amount=totals["final_amount"],
        mrp_total=totals["total_mrp"],
        item_discount=totals["item_discount"],
        coupon_discount=totals["coupon_discount"],
        delivery_fee=totals["delivery_fee"],
    )

    # 🔥 CREATE ORDER ITEMS
    for variant_id, qty in cart.items():
        variant = ProductVariant.objects.get(id=int(variant_id))
        if variant.stock < qty:
                return JsonResponse({
                    "status": "failed",
                    "message": "Out of stock"
                })

        OrderItem.objects.create(
            order=order,
            variant=variant,
            quantity=qty,
            price=variant.price,
        )
        variant.stock -= qty
        variant.save()

    # Clear session
    clear_checkout_session(request)

    return JsonResponse({
        "status": "success",
        "order_id": order.id
    })



def clear_checkout_session(request):
    for key in [
        "cart", "coupon", "address",
        "final_amount", "coupon_discount", "delivery_fee"
    ]:
        request.session.pop(key, None)


def send_whatsapp(order):
    try:
        phone_number = "919878441443"
        message = (
            "🎉 *Order Confirmed!*\n\n"
            f"🧾 Order ID: {order.id}\n"
            f"💳 Payment: {order.payment_method.upper()}\n"
            f"💰 Total: ₹{order.total_amount}\n"
        )
        send_whatsapp_message(phone_number, message)
    except Exception as e:
        print("WhatsApp error:", e)


from .utils.email_utils import send_user_email
    
@login_required
def order_success(request):
    order = Order.objects.filter(user=request.user).latest("created_at")

    
    
    send_user_email(
    subject="🛒 Order Placed Successfully",
    message=f"""
    Hi {request.user.username},

    Your order #{order.id} has been placed successfully.

    Total Amount: ₹{order.total_amount}

    We will notify you once it is delivered.
    """,
        to_email=request.user.email
    )
        
    return render(request, "store/order_success.html", {
        "order": order
    })

from django.http import JsonResponse
from decimal import Decimal
from store.models import ProductVariant

def add_to_cart_ajax(request):
    variant_id = request.GET.get("variant_id")
    qty = int(request.GET.get("qty", 1))

    if not variant_id or not variant_id.isdigit():
        return JsonResponse({"success": False})

    cart = request.session.get("cart", {})

    cart[variant_id] = cart.get(variant_id, 0) + qty

    request.session["cart"] = cart
    request.session.modified = True

    cart_count = sum(cart.values())

    return JsonResponse({
        "success": True,
        "cart_count": cart_count,
    })



from django.http import JsonResponse
from django.db.models import Q

def ajax_search(request):
    query = request.GET.get("q", "").strip()

    if not query:
        return JsonResponse({"results": []})

    products = Product.objects.filter(
        Q(name__icontains=query) |
        Q(description__icontains=query)
    )[:6]

    results = []
    for product in products:
        results.append({
            "id": product.id,
            "name": product.name,
            "price": str(product.display_price) if product.display_price else "",
            "quantity": product.display_quantity,
            "image": product.image.url if product.image else "",
        })

    return JsonResponse({"results": results})




from django.template.loader import get_template
from xhtml2pdf import pisa
from django.http import HttpResponse

def download_invoice(request, order_id):
    order = Order.objects.get(id=order_id, user=request.user)
    items = order.items.all()


    template = get_template("store/invoice.html")
    html = template.render({"order": order, "items": items})

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="invoice_{order.id}.pdf"'

    pisa.CreatePDF(html, dest=response)
    return response


@login_required
def my_orders(request):
    orders = (
        Order.objects
        .filter(user=request.user)
        .order_by("-created_at")
        .prefetch_related("items__variant__product")
    )

    return render(request, "store/my_orders.html", {
        "orders": orders
    })




from .models import ProductRating

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # Customer / delivery logic (keep as it is)
    if order.user == request.user:
        template = "store/order_detail.html"
    elif DeliveryPartner.objects.filter(user=request.user).exists():
        partner = DeliveryPartner.objects.get(user=request.user)

        if order.delivery_partner != partner:
            return redirect("home")

        template = "delivery/order_detail.html"
    else:
        return redirect("home")

    items = order.items.select_related('variant__product')

    # ✅ ADD THIS BLOCK (IMPORTANT)
    for item in items:
        item.user_rating = ProductRating.objects.filter(
            user=request.user,
            product=item.variant.product
        ).first()

    return render(request, template, {
        "order": order,
        "items": items
    })



@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.status != "placed":
        messages.error(request, "Order cannot be cancelled after shipping")
        return redirect("order_detail", order_id=order.id)

    order.status = "cancelled"
    order.save()

    messages.success(request, "Order cancelled successfully")
    return redirect("my_orders")






from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from .models import OrderItem
from warehouse.models import ReturnDamage

@login_required
def return_item(request, item_id):
    item = get_object_or_404(
        OrderItem,
        id=item_id,
        order__user=request.user
    )

    # ❌ Only delivered items can be returned
    if item.order.status != "delivered":
        messages.error(request, "This item cannot be returned.")
        return redirect("order_detail", order_id=item.order.id)

    # ❌ Prevent duplicate return
    if item.return_status != "none":
        messages.warning(request, "Return already requested for this item.")
        return redirect("order_detail", order_id=item.order.id)

    if request.method == "POST":
        reason = request.POST.get("reason")
        comment = request.POST.get("comment")

        if not reason:
            messages.error(request, "Please select a return reason.")
            return redirect("return_item", item_id=item.id)

        # ✅ Update ONLY the item
        item.return_status = "requested"
        item.return_reason = reason
        item.return_comment = comment
        item.save()
        
        item.order.return_requested = True
        item.order.return_reason = reason
        item.order.return_comment = comment
        item.order.status = "returned"
        item.order.save()

        return_obj = ReturnDamage.objects.create(
        order_item=item,
        customer=item.order.user,
        equipment=item.variant.product.name,
        quantity=item.quantity,
        status="Returned",
        action_status="Requested"
    )
        print("RETURN CREATED:", return_obj.id)

        messages.success(
            request,
            "✅ Return request received for this item."
        )

        return redirect("order_detail", order_id=item.order.id)
    
    send_user_email(
    subject="🔄 Return Request Received",
    message=f"""
Hi {item.order.user.username},

We have received your return request for:/

Product: {item.variant.product.name}
Order ID: {item.order.id}

Our team will review and update you soon.
""",
    to_email=item.order.user.email
)

 
    # GET request → show reason page
    return render(
        request,
        "store/return_reason.html",
        {"item": item}
    )


@login_required
def rate_product(request, item_id):
    if request.method == "POST":

        order_item = get_object_or_404(OrderItem, id=item_id)

        # Allow rating only after delivery
        if order_item.order.status != "delivered":
            messages.error(request, "You can only rate delivered items")
            return redirect("order_detail", order_id=order_item.order.id)

        rating_value = request.POST.get("rating")

        if not rating_value:
            messages.error(request, "Please select a rating.")
            return redirect("order_detail", order_id=order_item.order.id)

        rating = int(rating_value)

        if rating < 1 or rating > 5:
            messages.error(request, "Invalid rating")
            return redirect("order_detail", order_id=order_item.order.id)

        product = order_item.variant.product

        ProductRating.objects.update_or_create(
            user=request.user,
            product=product,
            defaults={"rating": rating},
        )

        messages.success(request, "Thank you for your rating!")

        return redirect("order_detail", order_id=order_item.order.id)


from django.shortcuts import render, get_object_or_404
from .models import Category, Product

from django.db.models import Avg, Count

def category_products(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    products = (
        Product.objects
        .filter(category=category)
        .select_related("category")
        .prefetch_related("variants")
        .annotate(
            avg_rating=Avg('productrating__rating'),
            review_count=Count('productrating')
        )
    )

    wishlist_product_ids = []

    if request.user.is_authenticated:
        wishlist_product_ids = Wishlist.objects.filter(
            user=request.user
        ).values_list("product_id", flat=True)

    context = {
        "category": category,
        "products": products,
        "wishlist_product_ids": wishlist_product_ids,
    }

    return render(request, "store/category_products.html", context)



from django.http import JsonResponse
import razorpay
from django.conf import settings

def razorpay_health_check(request):
    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )
    order = client.order.create({
        "amount": 100,
        "currency": "INR",
        "payment_capture": 1
    })
    return JsonResponse(order)


import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Review, Product

@login_required
def submit_review(request):
    if request.method == "POST":
        data = json.loads(request.body)

        product = Product.objects.get(id=data.get("product_id"))

        Review.objects.create(
            user=request.user,
            product=product,
            rating=data.get("rating"),
            comment=data.get("comment")
        )

        return JsonResponse({"status": "success"})


