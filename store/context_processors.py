# def cart_count(request):
#     cart = request.session.get("cart", {})
#     return {
#         "cart_count": sum(cart.values())
#     }


def cart_count(request):
    cart = request.session.get("cart", {})

    # ✅ CLEAN INVALID / ZERO ITEMS
    clean_cart = {
        str(k): int(v)
        for k, v in cart.items()
        if str(k).isdigit() and isinstance(v, int) and v > 0
    }

    # ✅ Update session only if needed
    if cart != clean_cart:
        request.session["cart"] = clean_cart
        request.session.modified = True

    return {
        "cart_count": sum(clean_cart.values())
    }

