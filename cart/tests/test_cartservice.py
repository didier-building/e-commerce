from django.test import TestCase, RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth import get_user_model
from decimal import Decimal
from product.models import Product, Category
from cart.service import CartService

User = get_user_model()

class CartServiceTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="testuser2", email="user2@example.com", password="testpass")
        cls.category = Category.objects.create(name="Books")
        cls.product1 = Product.objects.create(
            name="Book 1",
            price=Decimal("15.00"),
            qty=10,
            seller=cls.user,
            category=cls.category
        )
        cls.product2 = Product.objects.create(
            name="Book 2",
            price=Decimal("25.00"),
            qty=5,
            seller=cls.user,
            category=cls.category
        )

    def setUp(self):
        self.factory = RequestFactory()

    def _get_request_with_session(self, user=None):
        request = self.factory.get("/")
        request.user = user or User()
        # Attach session
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        return request

    def test_add_item_authenticated_user(self):
        request = self._get_request_with_session(user=self.user)
        cart_service = CartService(request)
        cart_service.add(self.product1, quantity=2)
        items = list(cart_service)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["quantity"], 2)
        self.assertEqual(items[0]["total_price"], Decimal("30.00"))

    def test_remove_item_authenticated_user(self):
        request = self._get_request_with_session(user=self.user)
        cart_service = CartService(request)
        cart_service.add(self.product1, quantity=2)
        cart_service.remove(self.product1)
        self.assertEqual(len(list(cart_service)), 0)

    def test_clear_cart_authenticated_user(self):
        request = self._get_request_with_session(user=self.user)
        cart_service = CartService(request)
        cart_service.add(self.product1, quantity=1)
        cart_service.add(self.product2, quantity=1)
        cart_service.clear()
        self.assertEqual(len(list(cart_service)), 0)

    def test_cart_total_price_authenticated_user(self):
        request = self._get_request_with_session(user=self.user)
        cart_service = CartService(request)
        cart_service.add(self.product1, quantity=1)
        cart_service.add(self.product2, quantity=2)
        total = cart_service.get_total_price()
        expected_total = Decimal("15.00") * 1 + Decimal("25.00") * 2
        self.assertEqual(total, expected_total)

    def test_group_by_vendor(self):
        request = self._get_request_with_session(user=self.user)
        cart_service = CartService(request)
        cart_service.add(self.product1, quantity=1)
        cart_service.add(self.product2, quantity=2)
        grouped = cart_service.group_by_vendor()
        self.assertEqual(len(grouped.keys()), 1)  # Only 1 vendor (same seller)
        self.assertEqual(len(grouped[self.user.id]), 2)
