"""Tests for vehicle module."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from ninja_jwt.tokens import RefreshToken

from users.models import UserRole
from vehicles.models import Vehicle, VehicleMedia, VehicleSpecification

User = get_user_model()


class TestVehicleModel(TestCase):
    """Tests for Vehicle model."""

    def test_create_vehicle(self):
        """Test creating a vehicle."""
        vehicle = Vehicle.objects.create(
            title="Test Car",
            brand="Toyota",
            model="Corolla",
            year=2022,
            mileage=15000,
            price=Decimal("22000.00"),
        )
        self.assertEqual(vehicle.title, "Test Car")
        self.assertEqual(vehicle.brand, "Toyota")
        self.assertTrue(vehicle.is_active)
        self.assertTrue(vehicle.slug)  # Auto-generated

    def test_vehicle_slug_generation(self):
        """Test automatic slug generation."""
        vehicle = Vehicle.objects.create(
            title="Great Car",
            brand="Honda",
            model="Civic",
            year=2023,
            mileage=5000,
            price=Decimal("25000.00"),
        )
        self.assertIn("honda", vehicle.slug.lower())
        self.assertIn("civic", vehicle.slug.lower())

    def test_vehicle_with_media(self):
        """Test vehicle with media."""
        vehicle = Vehicle.objects.create(
            title="Car with Images",
            brand="BMW",
            model="3 Series",
            year=2021,
            mileage=20000,
            price=Decimal("35000.00"),
        )
        media = VehicleMedia.objects.create(
            vehicle=vehicle,
            media_type="IMAGE",
            url="https://example.com/image.jpg",
            is_primary=True,
        )
        self.assertEqual(vehicle.primary_image, media.url)

    def test_vehicle_specifications(self):
        """Test vehicle specifications."""
        vehicle = Vehicle.objects.create(
            title="Feature Car",
            brand="Audi",
            model="A4",
            year=2022,
            mileage=10000,
            price=Decimal("40000.00"),
        )
        VehicleSpecification.objects.create(
            vehicle=vehicle,
            key="Climatisation",
            value="Automatique bi-zone",
            group="Confort",
        )
        self.assertEqual(vehicle.specifications.count(), 1)
        self.assertEqual(vehicle.specifications.first().key, "Climatisation")


class TestVehicleAPI(TestCase):
    """Tests for Vehicle API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.password = "TestPass123!"

        # Create admin user
        self.admin_user = User.objects.create_user(
            email="admin@test.com",
            password=self.password,
            first_name="Admin",
            last_name="User",
            role=UserRole.ADMIN,
            is_staff=True,
            is_superuser=True,
        )
        refresh = RefreshToken.for_user(self.admin_user)
        self.admin_auth_headers = {"HTTP_AUTHORIZATION": f"Bearer {refresh.access_token}"}

        # Create test vehicle
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

    def test_list_vehicles(self):
        """Test listing vehicles."""
        response = self.client.get("/api/v1/vehicles/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(data["total"], 1)
        self.assertGreaterEqual(len(data["items"]), 1)

    def test_get_vehicle(self):
        """Test getting a specific vehicle."""
        response = self.client.get(f"/api/v1/vehicles/{self.vehicle.id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["title"], self.vehicle.title)
        self.assertEqual(data["brand"], self.vehicle.brand)

    def test_get_vehicle_by_slug(self):
        """Test getting vehicle by slug."""
        response = self.client.get(f"/api/v1/vehicles/slug/{self.vehicle.slug}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], str(self.vehicle.id))

    def test_create_vehicle_as_admin(self):
        """Test creating vehicle as admin."""
        response = self.client.post(
            "/api/v1/vehicles/",
            data={
                "title": "New Test Vehicle",
                "brand": "Mercedes",
                "model": "C-Class",
                "year": 2023,
                "mileage": 5000,
                "price": "45000.00",
            },
            content_type="application/json",
            **self.admin_auth_headers
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["brand"], "Mercedes")

    def test_filter_vehicles(self):
        """Test filtering vehicles."""
        response = self.client.get(f"/api/v1/vehicles/?brand={self.vehicle.brand}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(all(v["brand"] == self.vehicle.brand for v in data["items"]))
