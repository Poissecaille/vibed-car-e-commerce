"""Schemas for user-related API endpoints."""
from datetime import datetime
from uuid import UUID

from ninja import Schema
from pydantic import EmailStr, Field


class AddressSchema(Schema):
    """Schema for address data."""
    id: UUID
    label: str
    street: str
    street_complement: str
    city: str
    postal_code: str
    country: str
    is_default_shipping: bool
    is_default_billing: bool


class AddressCreateSchema(Schema):
    """Schema for creating an address."""
    label: str = ""
    street: str
    street_complement: str = ""
    city: str
    postal_code: str
    country: str = "France"
    is_default_shipping: bool = False
    is_default_billing: bool = False


class AddressUpdateSchema(Schema):
    """Schema for updating an address."""
    label: str | None = None
    street: str | None = None
    street_complement: str | None = None
    city: str | None = None
    postal_code: str | None = None
    country: str | None = None
    is_default_shipping: bool | None = None
    is_default_billing: bool | None = None


class ProfileSchema(Schema):
    """Schema for user profile data."""
    shipping_address: AddressSchema | None = None
    billing_address: AddressSchema | None = None
    preferences: dict
    avatar_url: str


class ProfileUpdateSchema(Schema):
    """Schema for updating a profile."""
    shipping_address_id: UUID | None = None
    billing_address_id: UUID | None = None
    preferences: dict | None = None
    avatar_url: str | None = None


class UserSchema(Schema):
    """Schema for user data."""
    id: UUID
    email: str
    first_name: str
    last_name: str
    phone_number: str
    role: str
    is_active: bool
    date_joined: datetime


class UserDetailSchema(UserSchema):
    """Detailed user schema including profile."""
    profile: ProfileSchema | None = None
    addresses: list[AddressSchema] = []


class UserCreateSchema(Schema):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(min_length=8)
    first_name: str = ""
    last_name: str = ""
    phone_number: str = ""


class UserUpdateSchema(Schema):
    """Schema for updating user information."""
    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None


class PasswordChangeSchema(Schema):
    """Schema for password change."""
    current_password: str
    new_password: str = Field(min_length=8)


class MessageSchema(Schema):
    """Generic message response schema."""
    message: str
