"""User models for authentication and profiles."""
import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

from core.models import SoftDeleteManager, SoftDeleteModel, TimestampedModel


class UserRole(models.TextChoices):
    """User role enumeration."""
    CLIENT = 'CLIENT', 'Client'
    ADMIN = 'ADMIN', 'Administrateur'
    STAFF = 'STAFF', 'Staff'
    SELLER = 'SELLER', 'Vendeur'


class UserManager(BaseUserManager, SoftDeleteManager):
    """Custom user manager with soft delete support."""

    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user."""
        if not email:
            raise ValueError("L'adresse email est obligatoire")
        email = self.normalize_email(email)
        extra_fields.setdefault('role', UserRole.CLIENT)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', UserRole.ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Un superuser doit avoir is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Un superuser doit avoir is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, SoftDeleteModel):
    """
    Custom user model with email as the unique identifier.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    role = models.CharField(
        max_length=10,
        choices=UserRole.choices,
        default=UserRole.CLIENT,
        db_index=True
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'users'
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role', 'is_active']),
        ]

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        """Return the full name of the user."""
        return f"{self.first_name} {self.last_name}".strip() or self.email

    def is_admin(self):
        """Check if user has admin role."""
        return self.role == UserRole.ADMIN

    def is_seller(self):
        """Check if user has seller role."""
        return self.role == UserRole.SELLER


class Address(TimestampedModel, SoftDeleteModel):
    """User address model for shipping and billing."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='addresses'
    )
    label = models.CharField(max_length=50, blank=True, help_text="Ex: Domicile, Bureau")
    street = models.CharField(max_length=255)
    street_complement = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='France')
    is_default_shipping = models.BooleanField(default=False)
    is_default_billing = models.BooleanField(default=False)

    class Meta:
        db_table = 'addresses'
        verbose_name = 'Adresse'
        verbose_name_plural = 'Adresses'
        ordering = ['-is_default_shipping', '-created_at']

    def __str__(self):
        return f"{self.street}, {self.postal_code} {self.city}"

    def save(self, *args, **kwargs):
        # Ensure only one default shipping address per user
        if self.is_default_shipping:
            Address.objects.filter(
                user=self.user, is_default_shipping=True
            ).exclude(pk=self.pk).update(is_default_shipping=False)
        # Ensure only one default billing address per user
        if self.is_default_billing:
            Address.objects.filter(
                user=self.user, is_default_billing=True
            ).exclude(pk=self.pk).update(is_default_billing=False)
        super().save(*args, **kwargs)


class Profile(TimestampedModel):
    """User profile for additional user information."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='profile'
    )
    shipping_address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='profiles_shipping'
    )
    billing_address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='profiles_billing'
    )
    preferences = models.JSONField(default=dict, blank=True)
    avatar_url = models.URLField(blank=True)

    class Meta:
        db_table = 'profiles'
        verbose_name = 'Profil'
        verbose_name_plural = 'Profils'

    def __str__(self):
        return f"Profil de {self.user.email}"
