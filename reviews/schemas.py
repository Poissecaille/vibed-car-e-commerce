"""Schemas for review API endpoints."""
from datetime import datetime
from uuid import UUID

from ninja import Schema
from pydantic import Field


class ReviewSchema(Schema):
    """Schema for review."""
    id: UUID
    user_id: UUID
    user_name: str
    vehicle_id: UUID
    rating: int
    title: str
    comment: str
    is_verified_purchase: bool
    helpful_votes: int
    created_at: datetime


class ReviewCreateSchema(Schema):
    """Schema for creating a review."""
    vehicle_id: UUID
    rating: int = Field(ge=1, le=5)
    title: str = ""
    comment: str = ""


class ReviewUpdateSchema(Schema):
    """Schema for updating a review."""
    rating: int | None = Field(None, ge=1, le=5)
    title: str | None = None
    comment: str | None = None


class VehicleReviewsSchema(Schema):
    """Schema for vehicle reviews with statistics."""
    reviews: list[ReviewSchema]
    total_reviews: int
    average_rating: float
    rating_distribution: dict[int, int]


class MessageSchema(Schema):
    """Generic message response."""
    message: str
