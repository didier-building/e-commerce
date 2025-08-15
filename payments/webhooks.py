import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from .models import Order

stripe.api_key = settings.STRIPE_SECRET_KEY

@csrf_exempt
def stripe_webhook(request):
    """
    Stripe -> Your API
    - checkout.session.completed: payment authorized (funds held). Keep Order 'Pending'.
    - charge.captured or payment_intent.succeeded: mark Order 'Paid' after capture.
    """
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    etype = event.get("type")
    data = event.get("data", {}).get("object", {})

    if etype == "checkout.session.completed":
        # Session completed = authorized, not captured. Keep 'Pending'.
        session_id = data.get("id")
        metadata = data.get("metadata") or {}
        order_id = metadata.get("order_id")
        if order_id:
            try:
                # Ensure the session matches our stored one
                Order.objects.get(id=order_id, stripe_checkout_id=session_id)
                # Optionally store PI for later use:
                # pi_id = data.get("payment_intent")
                # order.some_field = pi_id
                # order.save(update_fields=["some_field"])
            except Order.DoesNotExist:
                pass

    # When captured, Stripe fires payment_intent.succeeded and/or charge.captured
    if etype in ("payment_intent.succeeded", "charge.captured"):
        if etype == "payment_intent.succeeded":
            pi_id = data.get("id")
        else:
            # charge.captured -> need PI id nested
            pi_id = data.get("payment_intent")

        if not pi_id:
            return HttpResponse(status=200)

        # Find pending orders and match by retrieving their sessions
        for order in Order.objects.filter(status="Pending"):
            try:
                s = stripe.checkout.Session.retrieve(order.stripe_checkout_id)
                if s and s.payment_intent == pi_id:
                    order.status = "Paid"
                    order.save(update_fields=["status"])
            except Exception:
                continue

    return HttpResponse(status=200)
