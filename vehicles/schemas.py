"""Schemas for vehicle-related API endpoints."""
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from ninja import FilterSchema, Schema
from pydantic import Field


class VehicleMediaSchema(Schema):
    """Schema for vehicle media."""
    id: int
    media_type: str
    url: str
    alt_text: str
    is_primary: bool
    sort_order: int


class VehicleMediaCreateSchema(Schema):
    """Schema for creating vehicle media."""
    media_type: str = "IMAGE"
    url: str
    alt_text: str = ""
    is_primary: bool = False
    sort_order: int = 0


class VehicleSpecificationSchema(Schema):
    """Schema for vehicle specification."""
    id: int
    key: str
    value: str
    group: str


class VehicleSpecificationCreateSchema(Schema):
    """Schema for creating vehicle specification."""
    key: str
    value: str
    group: str = ""


class VehicleHistorySchema(Schema):
    """Schema for vehicle history."""
    accident_history: str
    maintenance_history: str
    number_of_previous_owners: int | None
    last_inspection_date: date | None
    inspection_valid_until: date | None
    is_imported: bool
    import_country: str
    warranty_until: date | None
    service_book_available: bool
    additional_notes: str


class VehicleHistoryCreateSchema(Schema):
    """Schema for creating/updating vehicle history."""
    accident_history: str = ""
    maintenance_history: str = ""
    number_of_previous_owners: int | None = None
    last_inspection_date: date | None = None
    inspection_valid_until: date | None = None
    is_imported: bool = False
    import_country: str = ""
    warranty_until: date | None = None
    service_book_available: bool = False
    additional_notes: str = ""


class VehicleSchema(Schema):
    """Schema for vehicle data."""
    id: UUID
    title: str
    slug: str
    description: str
    category: str
    brand: str
    model: str
    year: int
    mileage: int
    fuel_type: str
    transmission: str
    power_hp: int | None
    color: str
    condition: str
    price: Decimal
    currency: str
    price_negotiable: bool
    is_active: bool
    is_featured: bool
    view_count: int
    created_at: datetime
    updated_at: datetime
    primary_image: str | None = None


class VehicleDetailSchema(VehicleSchema):
    """Detailed vehicle schema including relations."""
    power_kw: int | None
    interior_color: str
    doors: int | None
    seats: int | None
    vin: str
    registration_number: str
    first_registration_date: date | None
    meta_description: str
    media: list[VehicleMediaSchema] = []
    specifications: list[VehicleSpecificationSchema] = []
    history: VehicleHistorySchema | None = None


class VehicleCreateSchema(Schema):
    """Schema for creating a vehicle."""
    title: str
    description: str = ""
    category: str = "CAR"
    brand: str
    model: str
    year: int = Field(ge=1900, le=2100)
    mileage: int = Field(ge=0)
    fuel_type: str = "GASOLINE"
    transmission: str = "MANUAL"
    power_hp: int | None = None
    power_kw: int | None = None
    color: str = ""
    interior_color: str = ""
    doors: int | None = None
    seats: int | None = None
    condition: str = "GOOD"
    vin: str = ""
    registration_number: str = ""
    first_registration_date: date | None = None
    price: Decimal = Field(ge=0)
    currency: str = "EUR"
    price_negotiable: bool = False
    is_active: bool = True
    is_featured: bool = False
    meta_description: str = ""


class VehicleUpdateSchema(Schema):
    """Schema for updating a vehicle."""
    title: str | None = None
    description: str | None = None
    category: str | None = None
    brand: str | None = None
    model: str | None = None
    year: int | None = None
    mileage: int | None = None
    fuel_type: str | None = None
    transmission: str | None = None
    power_hp: int | None = None
    power_kw: int | None = None
    color: str | None = None
    interior_color: str | None = None
    doors: int | None = None
    seats: int | None = None
    condition: str | None = None
    vin: str | None = None
    registration_number: str | None = None
    first_registration_date: date | None = None
    price: Decimal | None = None
    currency: str | None = None
    price_negotiable: bool | None = None
    is_active: bool | None = None
    is_featured: bool | None = None
    meta_description: str | None = None


class VehicleFilterSchema(FilterSchema):
    """Filter schema for vehicle search."""
    category: str | None = None
    brand: str | None = None
    model: str | None = None
    year_min: int | None = Field(None, q='year__gte')
    year_max: int | None = Field(None, q='year__lte')
    price_min: Decimal | None = Field(None, q='price__gte')
    price_max: Decimal | None = Field(None, q='price__lte')
    mileage_max: int | None = Field(None, q='mileage__lte')
    fuel_type: str | None = None
    transmission: str | None = None
    condition: str | None = None
    is_active: bool | None = None


class VehicleListSchema(Schema):
    """Schema for paginated vehicle list response."""
    items: list[VehicleSchema]
    total: int
    page: int
    page_size: int
    pages: int
