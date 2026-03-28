from django.urls import path
from . import views
app_name = "delivery"

urlpatterns = [
    path("dashboard/", views.delivery_dashboard, name="delivery_dashboard"),
    path('update-status/<int:order_id>/<str:status>/', views.update_status, name='update_status'),
    path('edit-profile/', views.edit_delivery_profile, name='edit_delivery_profile'),
    path("profile/", views.delivery_profile, name="delivery_profile"),
    path("history/", views.delivery_history, name="delivery_history"),
    path("accept/<int:order_id>/", views.accept_order, name="accept_order"),
path("reject/<int:order_id>/", views.reject_order, name="reject_order"),
path("api/check-orders/", views.check_new_orders, name="check_orders"),
path("orders/<int:order_id>/", views.order_detail, name="delivery_order_detail"),
path('toggle-status/', views.toggle_status, name='toggle_status'),
    path('get-status/', views.get_status, name='get_status'),
    path('verify-delivery/<int:order_id>/', views.verify_delivery, name='verify_delivery'),
]