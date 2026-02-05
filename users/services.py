"""Business logic services for users."""
from django.contrib.auth import authenticate
from django.db import transaction

from core.services import AuditService

from .models import Address, Profile, User
from .schemas import AddressCreateSchema, AddressUpdateSchema, UserCreateSchema, UserUpdateSchema


class UserService:
    """Service for user-related operations."""

    @staticmethod
    @transaction.atomic
    def create_user(data: UserCreateSchema, request=None) -> User:
        """Create a new user with profile."""
        user = User.objects.create_user(
            email=data.email,
            password=data.password,
            first_name=data.first_name,
            last_name=data.last_name,
            phone_number=data.phone_number,
        )
        AuditService.log_create(user, actor=user, request=request)
        return user

    @staticmethod
    def update_user(user: User, data: UserUpdateSchema, request=None) -> User:
        """Update user information."""
        update_fields = []
        for field, value in data.dict(exclude_unset=True).items():
            if value is not None:
                setattr(user, field, value)
                update_fields.append(field)

        if update_fields:
            user.save(update_fields=update_fields + ['updated_at'] if hasattr(user, 'updated_at') else update_fields)
            AuditService.log_update(user, {}, actor=user, request=request)

        return user

    @staticmethod
    def change_password(user: User, current_password: str, new_password: str) -> bool:
        """Change user password."""
        if not user.check_password(current_password):
            return False
        user.set_password(new_password)
        user.save(update_fields=['password'])
        return True

    @staticmethod
    def authenticate_user(email: str, password: str) -> User | None:
        """Authenticate a user with email and password."""
        return authenticate(email=email, password=password)

    @staticmethod
    def deactivate_user(user: User, actor=None, request=None):
        """Deactivate a user account."""
        user.is_active = False
        user.save(update_fields=['is_active'])
        AuditService.log_update(
            user,
            {'is_active': True},
            actor=actor or user,
            request=request,
            extra_data={'action': 'deactivate'}
        )


class AddressService:
    """Service for address-related operations."""

    @staticmethod
    def create_address(user: User, data: AddressCreateSchema, request=None) -> Address:
        """Create a new address for a user."""
        address = Address.objects.create(
            user=user,
            **data.dict()
        )
        AuditService.log_create(address, actor=user, request=request)
        return address

    @staticmethod
    def update_address(address: Address, data: AddressUpdateSchema, actor=None, request=None) -> Address:
        """Update an existing address."""
        update_fields = []
        for field, value in data.dict(exclude_unset=True).items():
            if value is not None:
                setattr(address, field, value)
                update_fields.append(field)

        if update_fields:
            address.save(update_fields=update_fields)
            AuditService.log_update(address, {}, actor=actor, request=request)

        return address

    @staticmethod
    def delete_address(address: Address, actor=None, request=None):
        """Soft delete an address."""
        AuditService.log_delete(address, actor=actor, request=request)
        address.delete()

    @staticmethod
    def get_user_addresses(user: User):
        """Get all addresses for a user."""
        return Address.objects.filter(user=user)


class ProfileService:
    """Service for profile-related operations."""

    @staticmethod
    def update_profile(profile: Profile, data: dict, actor=None, request=None) -> Profile:
        """Update user profile."""
        update_fields = []

        if 'shipping_address_id' in data and data['shipping_address_id']:
            profile.shipping_address_id = data['shipping_address_id']
            update_fields.append('shipping_address')

        if 'billing_address_id' in data and data['billing_address_id']:
            profile.billing_address_id = data['billing_address_id']
            update_fields.append('billing_address')

        if 'preferences' in data and data['preferences']:
            profile.preferences = data['preferences']
            update_fields.append('preferences')

        if 'avatar_url' in data and data['avatar_url'] is not None:
            profile.avatar_url = data['avatar_url']
            update_fields.append('avatar_url')

        if update_fields:
            profile.save(update_fields=update_fields)
            AuditService.log_update(profile, {}, actor=actor, request=request)

        return profile
