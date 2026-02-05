"""Business logic services for reviews."""
from django.db import IntegrityError, transaction
from django.db.models import Avg, Count

from core.services import AuditService
from orders.models import Order, OrderItem, OrderStatus
from vehicles.models import Vehicle

from .models import Review, ReviewVote


class ReviewService:
    """Service for review operations."""

    @staticmethod
    def get_vehicle_reviews(vehicle_id, approved_only: bool = True):
        """Get all reviews for a vehicle."""
        queryset = Review.objects.filter(vehicle_id=vehicle_id)
        if approved_only:
            queryset = queryset.filter(is_approved=True)
        return queryset.select_related('user').order_by('-created_at')

    @staticmethod
    def get_vehicle_review_stats(vehicle_id):
        """Get review statistics for a vehicle."""
        reviews = Review.objects.filter(vehicle_id=vehicle_id, is_approved=True)

        stats = reviews.aggregate(
            total=Count('id'),
            average=Avg('rating')
        )

        # Calculate rating distribution
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for review in reviews.values('rating').annotate(count=Count('id')):
            distribution[review['rating']] = review['count']

        return {
            'total_reviews': stats['total'] or 0,
            'average_rating': round(stats['average'] or 0, 1),
            'rating_distribution': distribution,
        }

    @staticmethod
    def get_user_reviews(user):
        """Get all reviews by a user."""
        return Review.objects.filter(user=user).select_related('vehicle').order_by('-created_at')

    @staticmethod
    def check_verified_purchase(user, vehicle) -> bool:
        """Check if user has purchased this vehicle."""
        return OrderItem.objects.filter(
            order__user=user,
            order__status=OrderStatus.PAID,
            vehicle=vehicle
        ).exists()

    @staticmethod
    @transaction.atomic
    def create_review(
        user,
        vehicle_id,
        rating: int,
        title: str = "",
        comment: str = "",
        request=None
    ) -> tuple[Review | None, str]:
        """Create a new review."""
        try:
            vehicle = Vehicle.objects.get(id=vehicle_id, is_active=True)
        except Vehicle.DoesNotExist:
            return None, "Véhicule non trouvé"

        # Check if user already reviewed this vehicle
        if Review.objects.filter(user=user, vehicle=vehicle).exists():
            return None, "Vous avez déjà laissé un avis pour ce véhicule"

        # Check for verified purchase
        is_verified = ReviewService.check_verified_purchase(user, vehicle)

        try:
            review = Review.objects.create(
                user=user,
                vehicle=vehicle,
                rating=rating,
                title=title,
                comment=comment,
                is_verified_purchase=is_verified,
            )
            AuditService.log_create(review, actor=user, request=request)
            return review, "Avis créé avec succès"
        except IntegrityError:
            return None, "Vous avez déjà laissé un avis pour ce véhicule"

    @staticmethod
    def update_review(
        review: Review,
        rating: int | None = None,
        title: str | None = None,
        comment: str | None = None,
        actor=None,
        request=None
    ) -> Review:
        """Update an existing review."""
        update_fields = []

        if rating is not None:
            review.rating = rating
            update_fields.append('rating')
        if title is not None:
            review.title = title
            update_fields.append('title')
        if comment is not None:
            review.comment = comment
            update_fields.append('comment')

        if update_fields:
            review.save(update_fields=update_fields + ['updated_at'])
            AuditService.log_update(review, {}, actor=actor, request=request)

        return review

    @staticmethod
    def delete_review(review: Review, actor=None, request=None):
        """Soft delete a review."""
        AuditService.log_delete(review, actor=actor, request=request)
        review.delete()

    @staticmethod
    @transaction.atomic
    def vote_helpful(user, review: Review, is_helpful: bool) -> tuple[bool, str]:
        """Vote on whether a review was helpful."""
        if review.user == user:
            return False, "Vous ne pouvez pas voter pour votre propre avis"

        vote, created = ReviewVote.objects.update_or_create(
            review=review,
            user=user,
            defaults={'is_helpful': is_helpful}
        )

        # Recalculate helpful votes
        review.helpful_votes = ReviewVote.objects.filter(
            review=review,
            is_helpful=True
        ).count()
        review.save(update_fields=['helpful_votes'])

        action = "enregistré" if created else "mis à jour"
        return True, f"Vote {action}"

    @staticmethod
    def moderate_review(review: Review, is_approved: bool, actor=None, request=None):
        """Approve or reject a review (admin only)."""
        review.is_approved = is_approved
        review.save(update_fields=['is_approved', 'updated_at'])
        AuditService.log_update(
            review,
            {'is_approved': not is_approved},
            actor=actor,
            request=request,
            extra_data={'action': 'moderation', 'approved': is_approved}
        )
        return review
