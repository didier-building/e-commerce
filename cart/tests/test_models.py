from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from product.models import Product, Category
from cart.models import Cart, CartItem
from cart.service import CartService
from django.test import RequestFactory

User = get_user_model()


class CartModelTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create a user
        cls.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass")
        # Create a cart
        cls.cart = Cart.objects.create(user=cls.user)
        # Create a category
        cls.category = Category.objects.create(name="Electronics")
        # Create products
        cls.product1 = Product.objects.create(
            name="Product 1",
            price=Decimal("10.00"),
            qty=5,
            seller=cls.user,
            category=cls.category
        )
        cls.product2 = Product.objects.create(
            name="Product 2",
            price=Decimal("20.00"),
            qty=3,
            seller=cls.user,
            category=cls.category
        )

    def test_cart_creation(self):
        self.assertEqual(self.cart.user, self.user)
        self.assertEqual(str(self.cart), f"Cart for {self.user.username}")

    def test_add_cart_item(self):
        item = CartItem.objects.create(
            cart=self.cart,
            product=self.product1,
            vendor_id=self.product1.seller.id,
            quantity=2,
            price=self.product1.price
        )
        self.assertEqual(item.cart, self.cart)
        self.assertEqual(item.product, self.product1)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.price, Decimal("10.00"))
        self.assertEqual(item.total_price, Decimal("20.00"))
        self.assertEqual(str(item), f"{self.product1} x 2")

    def test_cart_total_price(self):
        CartItem.objects.create(cart=self.cart, product=self.product1, vendor_id=self.product1.seller.id, quantity=2, price=self.product1.price)
        CartItem.objects.create(cart=self.cart, product=self.product2, vendor_id=self.product2.seller.id, quantity=1, price=self.product2.price)
        total = self.cart.get_total_price()
        expected_total = (Decimal("10.00") * 2) + (Decimal("20.00") * 1)
        self.assertEqual(total, expected_total)


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

    def test_add_item_authenticated_user(self):
        request = self.factory.get("/")
        request.user = self.user
        cart_service = CartService(request)

        cart_service.add(self.product1, quantity=2)
        items = list(cart_service)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["quantity"], 2)
        self.assertEqual(items[0]["total_price"], Decimal("30.00"))

    def test_remove_item_authenticated_user(self):
        request = self.factory.get("/")
        request.user = self.user
        cart_service = CartService(request)
        cart_service.add(self.product1, quantity=2)
        cart_service.remove(self.product1)
        self.assertEqual(len(list(cart_service)), 0)

    def test_clear_cart_authenticated_user(self):
        request = self.factory.get("/")
        request.user = self.user
        cart_service = CartService(request)
        cart_service.add(self.product1, quantity=1)
        cart_service.add(self.product2, quantity=1)
        cart_service.clear()
        self.assertEqual(len(list(cart_service)), 0)

    def test_cart_total_price_authenticated_user(self):
        request = self.factory.get("/")
        request.user = self.user
        cart_service = CartService(request)
        cart_service.add(self.product1, quantity=1)
        cart_service.add(self.product2, quantity=2)
        total = cart_service.get_total_price()
        expected_total = Decimal("15.00") * 1 + Decimal("25.00") * 2
        self.assertEqual(total, expected_total)

    def test_group_by_vendor(self):
        request = self.factory.get("/")
        request.user = self.user
        cart_service = CartService(request)
        cart_service.add(self.product1, quantity=1)
        cart_service.add(self.product2, quantity=2)
        grouped = cart_service.group_by_vendor()
        # There is only 1 vendor (same seller)
        self.assertEqual(len(grouped.keys()), 1)
        self.assertEqual(len(grouped[self.user.id]), 2)
