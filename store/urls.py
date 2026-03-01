from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),

    path('add-to-cart/<int:variant_id>/', views.add_to_cart, name='add_to_cart'),

    path('cart/', views.cart_view, name='cart'),
    path("update-cart/<int:variant_id>/", views.update_cart, name="update_cart"),
path("remove-from-cart/<int:variant_id>/", views.remove_from_cart, name="remove_from_cart"),


    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("logout/", views.logout_view, name="logout"),
    path("checkout/", views.checkout, name="checkout"),
    path("payment/", views.payment, name="payment"),
path("process-payment/", views.process_payment, name="process_payment"),
path("place-order/", views.place_order, name="place_order"),
path("order-success/", views.order_success, name="order_success"),
path("add-to-cart-ajax/", views.add_to_cart_ajax, name="add_to_cart_ajax"),
path("ajax/search/", views.ajax_search, name="ajax_search"),
path("apply-coupon/", views.apply_coupon, name="apply_coupon"),
path("remove-coupon/", views.remove_coupon, name="remove_coupon"),
path("invoice/<int:order_id>/", views.download_invoice, name="download_invoice"),
path("my-orders/", views.my_orders, name="my_orders"),
path("order/<int:order_id>/", views.order_detail, name="order_detail"),
path("cancel-order/<int:order_id>/", views.cancel_order, name="cancel_order"),
path(
    "rate-product/<int:item_id>/",
    views.rate_product,
    name="rate_product"
),
#  path("return-order/<int:order_id>/", views.return_order, name="return_order"),
#  path('order/<int:order_id>/return/', views.return_order, name='return_order'),
 # urls.py
path("return-item/<int:item_id>/", views.return_item, name="return_item"),
path("category/<int:category_id>/", views.category_products, name="category_products"),

path("wishlist/", views.wishlist_page, name="wishlist"),
path("wishlist/toggle/<int:product_id>/", views.toggle_wishlist, name="toggle_wishlist"),
path("rzp-test/", views.razorpay_health_check),
path(
    "verify-razorpay-payment/",
    views.verify_razorpay_payment,
    name="verify_razorpay_payment"
),

]
