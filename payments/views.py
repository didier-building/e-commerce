from django.conf import settings
from django.db import transaction
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import stripe

from .models import Order, OrderItem
from product.models import Product
from cart.service import CartService  

stripe.api_key = settings.STRIPE_SECRET_KEY

class CreatePaymentAPIView(APIView):
    """
    Create a Stripe Checkout Session for multiple vendors.
    If one product fails (e.g., qty issue), skip and continue.
    """
    permission_classes = []  # or [IsAuthenticated] if you want logged-in users only

    def post(self, request, *args, **kwargs):
        cart = CartService(request)
        cart_items = list(cart)  # use __iter__()

        if not cart_items:
            return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        line_items = []
        valid_items = []

        for item in cart_items:
            try:
                product_id = item["product"]["id"]
                product = Product.objects.get(pk=product_id)

                if item["quantity"] > product.qty:
                    continue  # skip if not enough qty

                line_items.append({
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": int(product.price * 100),
                        "product_data": {"name": product.name},
                    },
                    "quantity": item["quantity"],
                })

                valid_items.append(item)

            except Product.DoesNotExist:
                continue  # skip missing product

        if not line_items:
            return Response({"error": "No valid products available"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                mode="payment",
                line_items=line_items,
                success_url=settings.SITE_URL + "api/success?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=settings.SITE_URL + "api/cancel",

                payment_intent_data={
                    "capture_method": "manual"  # hold funds until manually captured
                }
            )

            with transaction.atomic():
                order = Order.objects.create(
                    stripe_checkout_id=checkout_session.id,
                    amount=sum(Product.objects.get(pk=i["product"]["id"]).price * i["quantity"] for i in valid_items),
                    currency="usd",
                    customer_email=request.user.email if request.user.is_authenticated else "",
                    status="Pending"
                )

                for item in valid_items:
                    product = Product.objects.get(pk=item["product"]["id"])
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=item["quantity"]
                    )

            return Response({"checkout_url": checkout_session.url}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


