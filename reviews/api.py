"""API endpoints for reviews."""
from uuid import UUID

from django.shortcuts import get_object_or_404
from ninja import Router
from ninja_jwt.authentication import JWTAuth

from .models import Review
from .schemas import (
    MessageSchema,
    ReviewCreateSchema,
    ReviewSchema,
    ReviewUpdateSchema,
    VehicleReviewsSchema,
)
from .services import ReviewService

router = Router()


# Public endpoints
@router.get("/vehicles/{vehicle_id}", response=VehicleReviewsSchema, auth=None)
def get_vehicle_reviews(request, vehicle_id: UUID):
    """Get all reviews for a vehicle with statistics."""
    reviews = ReviewService.get_vehicle_reviews(vehicle_id)
    stats = ReviewService.get_vehicle_review_stats(vehicle_id)

    return VehicleReviewsSchema(
        reviews=[_build_review_response(r) for r in reviews],
        **stats
    )


# Authenticated endpoints
@router.get("/me", response=list[ReviewSchema], auth=JWTAuth())
def get_my_reviews(request):
    """Get current user's reviews."""
    reviews = ReviewService.get_user_reviews(request.auth)
    return [_build_review_response(r) for r in reviews]


@router.post("/", response={201: ReviewSchema, 400: MessageSchema}, auth=JWTAuth())
def create_review(request, data: ReviewCreateSchema):
    """Create a new review."""
    review, message = ReviewService.create_review(
        request.auth,
        data.vehicle_id,
        data.rating,
        data.title,
        data.comment,
        request=request
    )
    if review is None:
        return 400, MessageSchema(message=message)
    return 201, _build_review_response(review)


@router.patch("/{review_id}", response={200: ReviewSchema, 403: MessageSchema}, auth=JWTAuth())
def update_review(request, review_id: UUID, data: ReviewUpdateSchema):
    """Update own review."""
    review = get_object_or_404(Review, id=review_id)

    # Check permission
    if review.user != request.auth:
        return 403, MessageSchema(message="Vous ne pouvez modifier que vos propres avis")

    review = ReviewService.update_review(
        review,
        rating=data.rating,
        title=data.title,
        comment=data.comment,
        actor=request.auth,
        request=request
    )
    return _build_review_response(review)


@router.delete("/{review_id}", response={200: MessageSchema, 403: MessageSchema}, auth=JWTAuth())
def delete_review(request, review_id: UUID):
    """Delete own review."""
    review = get_object_or_404(Review, id=review_id)

    # Check permission (owner or admin)
    if review.user != request.auth and not request.auth.is_admin():
        return 403, MessageSchema(message="Vous ne pouvez supprimer que vos propres avis")

    ReviewService.delete_review(review, actor=request.auth, request=request)
    return MessageSchema(message="Avis supprimé")


@router.post("/{review_id}/vote", response={200: MessageSchema, 400: MessageSchema}, auth=JWTAuth())
def vote_review(request, review_id: UUID, is_helpful: bool = True):
    """Vote on whether a review was helpful."""
    review = get_object_or_404(Review, id=review_id)

    success, message = ReviewService.vote_helpful(
        request.auth,
        review,
        is_helpful
    )
    if not success:
        return 400, MessageSchema(message=message)
    return MessageSchema(message=message)


# Admin endpoints
@router.post("/admin/{review_id}/moderate", response=ReviewSchema, auth=JWTAuth())
def moderate_review(request, review_id: UUID, is_approved: bool = True):
    """Approve or reject a review (admin only)."""
    if not request.auth.is_admin():
        return router.create_response(request, {"detail": "Non autorisé"}, status=403)

    review = get_object_or_404(Review.all_objects, id=review_id)
    review = ReviewService.moderate_review(
        review,
        is_approved,
        actor=request.auth,
        request=request
    )
    return _build_review_response(review)


@router.get("/admin/pending", response=list[ReviewSchema], auth=JWTAuth())
def get_pending_reviews(request):
    """Get reviews pending moderation (admin only)."""
    if not request.auth.is_admin():
        return router.create_response(request, {"detail": "Non autorisé"}, status=403)

    reviews = Review.objects.filter(is_approved=False).select_related('user', 'vehicle')
    return [_build_review_response(r) for r in reviews]


def _build_review_response(review: Review) -> ReviewSchema:
    """Build review response schema."""
    return ReviewSchema(
        id=review.id,
        user_id=review.user_id,
        user_name=review.user.first_name or review.user.email.split('@')[0],
        vehicle_id=review.vehicle_id,
        rating=review.rating,
        title=review.title,
        comment=review.comment,
        is_verified_purchase=review.is_verified_purchase,
        helpful_votes=review.helpful_votes,
        created_at=review.created_at,
    )
