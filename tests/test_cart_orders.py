"""Tests for cart and order modules."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from ninja_jwt.tokens import RefreshToken

from cart.services import CartService
from inventory.models import InventoryItem
from orders.models import OrderStatus
from orders.services import OrderService
from users.models import Address
from vehicles.models import Vehicle

User = get_user_model()


class BaseTestCase(TestCase):
    """Base test case with common setup."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.password = "TestPass123!"

        # Create user
        self.user = User.objects.create_user(
            email="user@test.com",
            password=self.password,
            first_name="Test",
            last_name="User",
        )
        refresh = RefreshToken.for_user(self.user)
        self.auth_headers = {"HTTP_AUTHORIZATION": f"Bearer {refresh.access_token}"}

        # Create vehicle
        self.vehicle = Vehicle.objects.create(
            title="Test Vehicle",
            description="A test vehicle",
            brand="TestBrand",
            model="TestModel",
            year=2023,
            mileage=10000,
            price=Decimal("25000.00"),
            condition="GOOD",
        )

        # Create inventory for vehicle
        InventoryItem.objects.create(vehicle=self.vehicle)

        # Create address
        self.address = Address.objects.create(
            user=self.user,
            street="123 Test Street",
            city="Paris",
            postal_code="75001",
            country="France",
            is_default_shipping=True,
        )


class TestCartService(BaseTestCase):
    """Tests for Cart service."""

    def test_get_or_create_cart(self):
        """Test getting or creating a cart."""
        cart = CartService.get_or_create_cart(self.user)
        self.assertIsNotNone(cart)
        self.assertEqual(cart.user, self.user)
        self.assertEqual(cart.status, "ACTIVE")

        # Should return same cart
        cart2 = CartService.get_or_create_cart(self.user)
        self.assertEqual(cart.id, cart2.id)

    def test_add_to_cart(self):
        """Test adding item to cart."""
        item, message = CartService.add_to_cart(self.user, str(self.vehicle.id))
        self.assertIsNotNone(item)
        self.assertEqual(item.vehicle, self.vehicle)
        self.assertEqual(item.price_snapshot, self.vehicle.price)

    def test_add_duplicate_to_cart(self):
        """Test adding same vehicle twice to cart."""
        CartService.add_to_cart(self.user, str(self.vehicle.id))
        item, message = CartService.add_to_cart(self.user, str(self.vehicle.id))
        self.assertIsNone(item)
        self.assertIn("déjà dans votre panier", message)

    def test_remove_from_cart(self):
        """Test removing item from cart."""
        item, _ = CartService.add_to_cart(self.user, str(self.vehicle.id))
        success, message = CartService.remove_from_cart(self.user, item.id)
        self.assertTrue(success)
        self.assertIn("retiré", message)

    def test_cart_total(self):
        """Test cart total calculation."""
        CartService.add_to_cart(self.user, str(self.vehicle.id))
        cart = CartService.get_active_cart(self.user)
        self.assertEqual(cart.total_amount, self.vehicle.price)


class TestOrderService(BaseTestCase):
    """Tests for Order service."""

    def test_create_order_from_cart(self):
        """Test creating order from cart."""
        CartService.add_to_cart(self.user, str(self.vehicle.id))

        order, message = OrderService.create_order_from_cart(
            self.user,
            shipping_address_id=self.address.id,
        )

        self.assertIsNotNone(order)
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.status, OrderStatus.PENDING)
        self.assertEqual(order.items.count(), 1)
        self.assertIn("succès", message)

    def test_create_order_empty_cart(self):
        """Test creating order from empty cart."""
        order, message = OrderService.create_order_from_cart(self.user)
        self.assertIsNone(order)
        self.assertIn("vide", message)

    def test_order_status_transitions(self):
        """Test order status transitions."""
        CartService.add_to_cart(self.user, str(self.vehicle.id))
        order, _ = OrderService.create_order_from_cart(self.user, shipping_address_id=self.address.id)

        # PENDING -> CONFIRMED
        order, _ = OrderService.update_status(order, OrderStatus.CONFIRMED)
        self.assertEqual(order.status, OrderStatus.CONFIRMED)
        self.assertIsNotNone(order.confirmed_at)

        # CONFIRMED -> PAID
        order, _ = OrderService.update_status(order, OrderStatus.PAID)
        self.assertEqual(order.status, OrderStatus.PAID)
        self.assertIsNotNone(order.paid_at)

    def test_cancel_order(self):
        """Test cancelling an order."""
        CartService.add_to_cart(self.user, str(self.vehicle.id))
        order, _ = OrderService.create_order_from_cart(self.user, shipping_address_id=self.address.id)

        order, message = OrderService.cancel_order(order)
        self.assertEqual(order.status, OrderStatus.CANCELLED)
        self.assertIsNotNone(order.cancelled_at)


class TestCartAPI(BaseTestCase):
    """Tests for Cart API endpoints."""

    def test_get_cart(self):
        """Test getting cart."""
        response = self.client.get("/api/v1/cart/", **self.auth_headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("items", data)
        self.assertIn("total_amount", data)

    def test_add_to_cart_api(self):
        """Test adding to cart via API."""
        response = self.client.post(
            "/api/v1/cart/items",
            data={"vehicle_id": str(self.vehicle.id)},
            content_type="application/json",
            **self.auth_headers
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(str(data["vehicle"]["id"]), str(self.vehicle.id))


class TestOrderAPI(BaseTestCase):
    """Tests for Order API endpoints."""

    def test_list_orders(self):
        """Test listing orders."""
        response = self.client.get("/api/v1/orders/", **self.auth_headers)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_create_order_api(self):
        """Test creating order via API."""
        # First add to cart
        self.client.post(
            "/api/v1/cart/items",
            data={"vehicle_id": str(self.vehicle.id)},
            content_type="application/json",
            **self.auth_headers
        )

        # Create order
        response = self.client.post(
            "/api/v1/orders/",
            data={
                "shipping_address_id": str(self.address.id),
                "customer_notes": "Test order"
            },
            content_type="application/json",
            **self.auth_headers
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["status"], "PENDING")
        self.assertEqual(data["items_count"], 1)
