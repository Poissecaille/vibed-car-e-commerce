"""Core services for audit logging and common operations."""
from typing import Any

from django.db import models

from .models import AuditAction, AuditLog


def get_client_ip(request) -> str | None:
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def model_to_dict(instance: models.Model, exclude: list[str] | None = None) -> dict[str, Any]:
    """Convert a model instance to a dictionary for audit logging."""
    exclude = exclude or []
    data = {}
    for field in instance._meta.fields:
        if field.name in exclude:
            continue
        value = getattr(instance, field.name)
        if hasattr(value, 'pk'):
            value = str(value.pk)
        elif hasattr(value, 'isoformat'):
            value = value.isoformat()
        else:
            value = str(value) if value is not None else None
        data[field.name] = value
    return data


class AuditService:
    """Service for creating audit log entries."""

    @staticmethod
    def log_create(
        instance: models.Model,
        actor=None,
        request=None,
        extra_data: dict | None = None
    ):
        """Log the creation of an entity."""
        ip_address = get_client_ip(request) if request else None
        user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''

        AuditLog.log(
            action=AuditAction.CREATE,
            entity_type=instance.__class__.__name__,
            entity_id=str(instance.pk),
            actor=actor,
            after_state=model_to_dict(instance),
            ip_address=ip_address,
            user_agent=user_agent,
            extra_data=extra_data,
        )

    @staticmethod
    def log_update(
        instance: models.Model,
        before_state: dict,
        actor=None,
        request=None,
        extra_data: dict | None = None
    ):
        """Log the update of an entity."""
        ip_address = get_client_ip(request) if request else None
        user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''

        AuditLog.log(
            action=AuditAction.UPDATE,
            entity_type=instance.__class__.__name__,
            entity_id=str(instance.pk),
            actor=actor,
            before_state=before_state,
            after_state=model_to_dict(instance),
            ip_address=ip_address,
            user_agent=user_agent,
            extra_data=extra_data,
        )

    @staticmethod
    def log_delete(
        instance: models.Model,
        actor=None,
        request=None,
        extra_data: dict | None = None
    ):
        """Log the deletion of an entity."""
        ip_address = get_client_ip(request) if request else None
        user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''

        AuditLog.log(
            action=AuditAction.DELETE,
            entity_type=instance.__class__.__name__,
            entity_id=str(instance.pk),
            actor=actor,
            before_state=model_to_dict(instance),
            ip_address=ip_address,
            user_agent=user_agent,
            extra_data=extra_data,
        )

    @staticmethod
    def log_status_change(
        instance: models.Model,
        old_status: str,
        new_status: str,
        actor=None,
        request=None,
        extra_data: dict | None = None
    ):
        """Log a status change on an entity."""
        ip_address = get_client_ip(request) if request else None
        user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''

        AuditLog.log(
            action=AuditAction.STATUS_CHANGE,
            entity_type=instance.__class__.__name__,
            entity_id=str(instance.pk),
            actor=actor,
            before_state={'status': old_status},
            after_state={'status': new_status},
            ip_address=ip_address,
            user_agent=user_agent,
            extra_data=extra_data,
        )

    @staticmethod
    def log_login(user, request=None, success: bool = True):
        """Log a user login attempt."""
        ip_address = get_client_ip(request) if request else None
        user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''

        AuditLog.log(
            action=AuditAction.LOGIN,
            entity_type='User',
            entity_id=str(user.pk),
            actor=user if success else None,
            ip_address=ip_address,
            user_agent=user_agent,
            extra_data={'success': success},
        )

    @staticmethod
    def log_payment(
        order,
        payment,
        actor=None,
        request=None,
        extra_data: dict | None = None
    ):
        """Log a payment event."""
        ip_address = get_client_ip(request) if request else None
        user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''

        AuditLog.log(
            action=AuditAction.PAYMENT,
            entity_type='Payment',
            entity_id=str(payment.pk),
            actor=actor,
            after_state={
                'order_id': str(order.pk),
                'amount': str(payment.amount),
                'status': payment.status,
            },
            ip_address=ip_address,
            user_agent=user_agent,
            extra_data=extra_data,
        )
