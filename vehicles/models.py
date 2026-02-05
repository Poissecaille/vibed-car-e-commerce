"""Vehicle models for the catalog."""
from decimal import Decimal

from django.conf import settings
from django.db import models

from core.models import BaseModel, TimestampedModel


class FuelType(models.TextChoices):
    """Fuel type enumeration."""
    GASOLINE = 'GASOLINE', 'Essence'
    DIESEL = 'DIESEL', 'Diesel'
    ELECTRIC = 'ELECTRIC', 'Électrique'
    HYBRID = 'HYBRID', 'Hybride'
    PLUGIN_HYBRID = 'PLUGIN_HYBRID', 'Hybride rechargeable'
    LPG = 'LPG', 'GPL'
    HYDROGEN = 'HYDROGEN', 'Hydrogène'


class Transmission(models.TextChoices):
    """Transmission type enumeration."""
    MANUAL = 'MANUAL', 'Manuelle'
    AUTOMATIC = 'AUTOMATIC', 'Automatique'
    SEMI_AUTO = 'SEMI_AUTO', 'Semi-automatique'


class VehicleCondition(models.TextChoices):
    """Vehicle condition enumeration."""
    NEW = 'NEW', 'Neuf'
    EXCELLENT = 'EXCELLENT', 'Excellent'
    GOOD = 'GOOD', 'Bon'
    FAIR = 'FAIR', 'Correct'
    POOR = 'POOR', 'À réviser'


class VehicleCategory(models.TextChoices):
    """Vehicle category enumeration."""
    CAR = 'CAR', 'Voiture'
    MOTORCYCLE = 'MOTORCYCLE', 'Moto'
    UTILITY = 'UTILITY', 'Utilitaire'
    TRUCK = 'TRUCK', 'Camion'
    CAMPER = 'CAMPER', 'Camping-car'


class Vehicle(BaseModel):
    """Main vehicle model representing a product in the catalog."""

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(
        max_length=20,
        choices=VehicleCategory.choices,
        default=VehicleCategory.CAR,
        db_index=True
    )
    brand = models.CharField(max_length=100, db_index=True)
    model = models.CharField(max_length=100, db_index=True)
    year = models.PositiveIntegerField(db_index=True)
    mileage = models.PositiveIntegerField(help_text="Kilométrage")
    fuel_type = models.CharField(
        max_length=20,
        choices=FuelType.choices,
        default=FuelType.GASOLINE
    )
    transmission = models.CharField(
        max_length=20,
        choices=Transmission.choices,
        default=Transmission.MANUAL
    )
    power_hp = models.PositiveIntegerField(null=True, blank=True, help_text="Puissance en chevaux")
    power_kw = models.PositiveIntegerField(null=True, blank=True, help_text="Puissance en kW")
    color = models.CharField(max_length=50, blank=True)
    interior_color = models.CharField(max_length=50, blank=True)
    doors = models.PositiveSmallIntegerField(null=True, blank=True)
    seats = models.PositiveSmallIntegerField(null=True, blank=True)
    condition = models.CharField(
        max_length=20,
        choices=VehicleCondition.choices,
        default=VehicleCondition.GOOD,
        db_index=True
    )
    vin = models.CharField(max_length=17, blank=True, help_text="Numéro d'identification du véhicule")
    registration_number = models.CharField(max_length=20, blank=True)
    first_registration_date = models.DateField(null=True, blank=True)

    # Pricing
    price = models.DecimalField(max_digits=12, decimal_places=2, db_index=True)
    currency = models.CharField(max_length=3, default='EUR')
    price_negotiable = models.BooleanField(default=False)

    # Status
    is_active = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)

    # SEO
    slug = models.SlugField(max_length=300, unique=True, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)

    class Meta:
        db_table = 'vehicles'
        verbose_name = 'Véhicule'
        verbose_name_plural = 'Véhicules'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['brand', 'model']),
            models.Index(fields=['price', 'is_active']),
            models.Index(fields=['year', 'mileage']),
            models.Index(fields=['category', 'condition']),
        ]

    def __str__(self):
        return f"{self.year} {self.brand} {self.model} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(f"{self.brand}-{self.model}-{self.year}-{self.title[:50]}")
            self.slug = base_slug
            # Ensure unique slug
            counter = 1
            while Vehicle.all_objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    @property
    def primary_image(self):
        """Get the primary image URL."""
        media = self.media.filter(media_type='IMAGE', is_primary=True).first()
        if not media:
            media = self.media.filter(media_type='IMAGE').first()
        return media.url if media else None


class MediaType(models.TextChoices):
    """Media type enumeration."""
    IMAGE = 'IMAGE', 'Image'
    VIDEO = 'VIDEO', 'Vidéo'
    DOCUMENT = 'DOCUMENT', 'Document'


class VehicleMedia(TimestampedModel):
    """Media files associated with a vehicle."""

    id = models.BigAutoField(primary_key=True)
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='media'
    )
    media_type = models.CharField(
        max_length=10,
        choices=MediaType.choices,
        default=MediaType.IMAGE
    )
    url = models.URLField(max_length=500)
    file = models.FileField(upload_to='vehicles/%Y/%m/', blank=True, null=True)
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'vehicle_media'
        verbose_name = 'Média véhicule'
        verbose_name_plural = 'Médias véhicule'
        ordering = ['sort_order', '-is_primary']

    def __str__(self):
        return f"{self.vehicle.title} - {self.media_type}"

    def save(self, *args, **kwargs):
        # Ensure only one primary media per type per vehicle
        if self.is_primary:
            VehicleMedia.objects.filter(
                vehicle=self.vehicle,
                media_type=self.media_type,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class VehicleSpecification(models.Model):
    """Custom specifications for a vehicle (key-value pairs)."""

    id = models.BigAutoField(primary_key=True)
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='specifications'
    )
    key = models.CharField(max_length=100)
    value = models.CharField(max_length=255)
    group = models.CharField(max_length=50, blank=True, help_text="Groupe de spécifications")

    class Meta:
        db_table = 'vehicle_specifications'
        verbose_name = 'Spécification véhicule'
        verbose_name_plural = 'Spécifications véhicule'
        unique_together = ['vehicle', 'key']

    def __str__(self):
        return f"{self.vehicle.title}: {self.key}={self.value}"


class VehicleHistory(TimestampedModel):
    """Historical information about a vehicle."""

    vehicle = models.OneToOneField(
        Vehicle,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='history'
    )
    accident_history = models.TextField(blank=True, help_text="Historique des accidents")
    maintenance_history = models.TextField(blank=True, help_text="Historique d'entretien")
    number_of_previous_owners = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Nombre de propriétaires précédents"
    )
    last_inspection_date = models.DateField(null=True, blank=True)
    inspection_valid_until = models.DateField(null=True, blank=True)
    is_imported = models.BooleanField(default=False)
    import_country = models.CharField(max_length=100, blank=True)
    warranty_until = models.DateField(null=True, blank=True)
    service_book_available = models.BooleanField(default=False)
    additional_notes = models.TextField(blank=True)

    class Meta:
        db_table = 'vehicle_history'
        verbose_name = 'Historique véhicule'
        verbose_name_plural = 'Historiques véhicule'

    def __str__(self):
        return f"Historique: {self.vehicle.title}"
