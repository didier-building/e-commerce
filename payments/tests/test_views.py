from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from product.models import Product
from cart.models import Cart, CartItem

User = get_user_model()

class CreatePaymentAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass123")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Create products
        self.product1 = Product.objects.create(
            name="Product 1",
            price=Decimal("50.00"),
            qty=10,
            seller=self.user
        )
        self.product2 = Product.objects.create(
            name="Product 2",
            price=Decimal("30.00"),
            qty=5,
            seller=self.user
        )

        # URL of the API view
        self.url = reverse("create-checkout-session")  # make sure to match your urls.py name

    def test_empty_cart_returns_error(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Cart is empty")

    def test_create_checkout_session_success(self):
        # Add items to user's cart
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product1, quantity=2)
        CartItem.objects.create(cart=cart, product=self.product2, quantity=1)

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("checkout_url", response.data)

    def test_product_qty_exceeded_skips_product(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product1, quantity=100)  # exceeds qty
        CartItem.objects.create(cart=cart, product=self.product2, quantity=1)

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Only product2 should be valid
        self.assertIn("checkout_url", response.data)

    def test_invalid_product_skipped(self):
        cart = Cart.objects.create(user=self.user)
        # CartItem with product id that does not exist
        CartItem.objects.create(cart=cart, product_id=9999, quantity=1)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "No valid products available")
        
    def test_success_url_and_cancel_url(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product1, quantity=2)
        CartItem.objects.create(cart=cart, product=self.product2, quantity=1)

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("checkout_url", response.data)
        self.assertIn("success_url", response.data)
        self.assertIn("cancel_url", response.data)