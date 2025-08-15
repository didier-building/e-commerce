from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from product.models import Product,Category
from payments.models import Order, OrderItem

User = get_user_model()

class OrderModelTestCase(TestCase):
    def setUp(self):
        # Create a user
        self.user_email = "test@example.com"
        self.user = User.objects.create_user(username="testuser", email=self.user_email, password="testpass123")
        # Create a category
        self.category = Category.objects.create(name="Electronics")

        # Create products
        self.product1 = Product.objects.create(
            name="Product 1",
            price=Decimal("50.00"),
            seller=self.user,
            qty=10,
            category=self.category
        )
        self.product2 = Product.objects.create(
            name="Product 2",
            price=Decimal("30.00"),
            seller=self.user,
            category=self.category,
            qty=5,
        )

        # Create an order
        self.order = Order.objects.create(
            stripe_checkout_id="cs_test_123",
            amount=Decimal("130.00"),
            currency="usd",
            customer_email=self.user_email,
            status="Pending"
        )

        # Create order items
        self.item1 = OrderItem.objects.create(
            order=self.order,
            product=self.product1,
            quantity=2
        )
        self.item2 = OrderItem.objects.create(
            order=self.order,
            product=self.product2,
            quantity=1
        )

    def test_order_creation(self):
        self.assertEqual(self.order.customer_email, self.user_email)
        self.assertEqual(self.order.status, "Pending")
        self.assertEqual(str(self.order), f"Order {self.order.stripe_checkout_id} - {self.order.status}")

    def test_order_item_creation(self):
        self.assertEqual(self.item1.order, self.order)
        self.assertEqual(self.item1.product, self.product1)
        self.assertEqual(self.item1.quantity, 2)
        self.assertEqual(str(self.item1), f"Order {self.item1.product.name} - {self.order.stripe_checkout_id}")

    def test_order_items_count(self):
        self.assertEqual(self.order.items.count(), 2)

    def test_total_order_amount(self):
        total = sum(item.product.price * item.quantity for item in self.order.items.all())
        self.assertEqual(total, Decimal("130.00"))
