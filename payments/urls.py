# orders/urls.py
from django.urls import path
from .views import CreatePaymentAPIView
from .s_views import payment_success, payment_cancel

urlpatterns = [
    path("create-checkout-session/", CreatePaymentAPIView.as_view(), name="create-checkout-session"),
    # path("webhook/stripe/", StripeWebhookAPIView.as_view(), name="stripe-webhook"),
    path('success/', payment_success, name='payment-success'),
    path('cancel/', payment_cancel, name='payment-cancel'),
]
