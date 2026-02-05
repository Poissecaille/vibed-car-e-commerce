"""Review models for vehicle ratings and comments."""
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.models import BaseModel


class Review(BaseModel):
    """Review for a vehicle."""

    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Note de 1 à 5"
    )
    title = models.CharField(max_length=100, blank=True)
    comment = models.TextField(blank=True)
    is_verified_purchase = models.BooleanField(
        default=False,
        help_text="L'utilisateur a-t-il acheté ce véhicule?"
    )
    is_approved = models.BooleanField(default=True)
    helpful_votes = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'reviews'
        verbose_name = 'Avis'
        verbose_name_plural = 'Avis'
        unique_together = ['user', 'vehicle']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['vehicle', 'is_approved']),
            models.Index(fields=['rating']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.vehicle.title} ({self.rating}/5)"


class ReviewVote(models.Model):
    """Vote on whether a review was helpful."""

    id = models.BigAutoField(primary_key=True)
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='votes'
    )
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='review_votes'
    )
    is_helpful = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'review_votes'
        verbose_name = 'Vote avis'
        verbose_name_plural = 'Votes avis'
        unique_together = ['review', 'user']

    def __str__(self):
        vote_type = "utile" if self.is_helpful else "pas utile"
        return f"{self.user.email} a trouvé l'avis {vote_type}"
