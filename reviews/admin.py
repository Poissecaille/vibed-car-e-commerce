"""Admin configuration for review models."""
from django.contrib import admin

from .models import Review, ReviewVote


class ReviewVoteInline(admin.TabularInline):
    """Inline admin for review votes."""
    model = ReviewVote
    extra = 0
    readonly_fields = ['user', 'is_helpful', 'created_at']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Admin interface for Review model."""

    list_display = [
        'user', 'vehicle', 'rating', 'title', 'is_verified_purchase',
        'is_approved', 'helpful_votes', 'created_at'
    ]
    list_filter = ['rating', 'is_verified_purchase', 'is_approved', 'created_at']
    search_fields = ['user__email', 'vehicle__title', 'title', 'comment']
    raw_id_fields = ['user', 'vehicle']
    readonly_fields = [
        'is_verified_purchase', 'helpful_votes',
        'created_at', 'updated_at', 'deleted_at'
    ]
    ordering = ['-created_at']

    fieldsets = (
        ('Avis', {
            'fields': ('user', 'vehicle', 'rating', 'title', 'comment')
        }),
        ('Statut', {
            'fields': ('is_verified_purchase', 'is_approved', 'helpful_votes')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Suppression', {
            'fields': ('is_deleted', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [ReviewVoteInline]
    actions = ['approve_reviews', 'reject_reviews']

    def get_queryset(self, request):
        """Include soft-deleted reviews in admin."""
        return Review.all_objects.all()

    @admin.action(description="Approuver les avis sélectionnés")
    def approve_reviews(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"{updated} avis approuvé(s).")

    @admin.action(description="Rejeter les avis sélectionnés")
    def reject_reviews(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f"{updated} avis rejeté(s).")


@admin.register(ReviewVote)
class ReviewVoteAdmin(admin.ModelAdmin):
    """Admin interface for ReviewVote model."""

    list_display = ['review', 'user', 'is_helpful', 'created_at']
    list_filter = ['is_helpful', 'created_at']
    search_fields = ['review__title', 'user__email']
    raw_id_fields = ['review', 'user']
    readonly_fields = ['created_at']
