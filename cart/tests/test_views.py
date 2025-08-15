from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from product.models import Product
from cart.models import Cart, CartItem

User = get_user_model()

class CartAPITestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass")

        # Create some products
        self.product1 = Product.objects.create(
            name="Product 1",
            price=10.00,
            qty=5,
            seller=self.user
        )
        self.product2 = Product.objects.create(
            name="Product 2",
            price=20.00,
            qty=3,
            seller=self.user
        )

        self.cart_url = reverse("cart-api")  # Adjust if your URL name is different

    def test_get_cart_empty_guest(self):
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"], [])
        self.assertEqual(response.data["cart_total_price"], 0)
        self.assertEqual(response.data["cart_grouped_by_vendor"], {})

    def test_add_item_guest_cart(self):
        data = {"action": "add", "product_id": self.product1.id, "quantity": 2}
        response = self.client.post(self.cart_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data["message"], "Cart updated successfully")

        # Check if the cart item exists in session
        session = self.client.session
        cart_session = session.get("cart", {})
        self.assertIn(str(self.product1.id), cart_session)
        self.assertEqual(cart_session[str(self.product1.id)]["quantity"], 2)

    def test_remove_item_guest_cart(self):
        # First add an item
        self.client.post(self.cart_url, {"action": "add", "product_id": self.product1.id, "quantity": 2}, format="json")
        # Now remove
        response = self.client.post(self.cart_url, {"action": "remove", "product_id": self.product1.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data["message"], "Cart updated successfully")

        session = self.client.session
        cart_session = session.get("cart", {})
        self.assertNotIn(str(self.product1.id), cart_session)

    def test_clear_cart_guest(self):
        # Add items first
        self.client.post(self.cart_url, {"action": "add", "product_id": self.product1.id, "quantity": 2}, format="json")
        self.client.post(self.cart_url, {"action": "add", "product_id": self.product2.id, "quantity": 1}, format="json")

        # Clear cart
        response = self.client.post(self.cart_url, {"action": "clear"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        session = self.client.session
        self.assertEqual(session.get("cart", {}), {})

    def test_cart_operations_logged_in_user(self):
        self.client.force_authenticate(user=self.user)

        # Add item
        response = self.client.post(self.cart_url, {"action": "add", "product_id": self.product1.id, "quantity": 3}, format="json")
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        # Check CartItem exists in DB
        cart = Cart.objects.get(user=self.user)
        cart_item = CartItem.objects.get(cart=cart, product=self.product1)
        self.assertEqual(cart_item.quantity, 3)

        # Remove item
        response = self.client.post(self.cart_url, {"action": "remove", "product_id": self.product1.id}, format="json")
        self.assertFalse(CartItem.objects.filter(cart=cart, product=self.product1).exists())

        # Add multiple items and clear cart
        self.client.post(self.cart_url, {"action": "add", "product_id": self.product1.id, "quantity": 1}, format="json")
        self.client.post(self.cart_url, {"action": "add", "product_id": self.product2.id, "quantity": 2}, format="json")
        response = self.client.post(self.cart_url, {"action": "clear"}, format="json")
        self.assertEqual(CartItem.objects.filter(cart=cart).count(), 0)
