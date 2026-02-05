"""API endpoints for users."""
from uuid import UUID

from django.shortcuts import get_object_or_404
from ninja import Router
from ninja_jwt.authentication import JWTAuth

from .models import Address, User
from .schemas import (
    AddressCreateSchema,
    AddressSchema,
    AddressUpdateSchema,
    MessageSchema,
    PasswordChangeSchema,
    ProfileUpdateSchema,
    UserCreateSchema,
    UserDetailSchema,
    UserSchema,
    UserUpdateSchema,
)
from .services import AddressService, ProfileService, UserService

router = Router()


# User Registration (public)
@router.post("/register", response={201: UserSchema}, auth=None)
def register(request, data: UserCreateSchema):
    """Register a new user account."""
    user = UserService.create_user(data, request=request)
    return 201, user


# Current User endpoints (authenticated)
@router.get("/me", response=UserDetailSchema, auth=JWTAuth())
def get_current_user(request):
    """Get current authenticated user details."""
    user = request.auth
    return UserDetailSchema(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        phone_number=user.phone_number,
        role=user.role,
        is_active=user.is_active,
        date_joined=user.date_joined,
        profile=user.profile if hasattr(user, 'profile') else None,
        addresses=list(user.addresses.all()),
    )


@router.patch("/me", response=UserSchema, auth=JWTAuth())
def update_current_user(request, data: UserUpdateSchema):
    """Update current user information."""
    user = UserService.update_user(request.auth, data, request=request)
    return user


@router.post("/me/change-password", response=MessageSchema, auth=JWTAuth())
def change_password(request, data: PasswordChangeSchema):
    """Change current user's password."""
    success = UserService.change_password(
        request.auth,
        data.current_password,
        data.new_password
    )
    if not success:
        return {"message": "Mot de passe actuel incorrect"}
    return {"message": "Mot de passe modifié avec succès"}


@router.patch("/me/profile", response=MessageSchema, auth=JWTAuth())
def update_profile(request, data: ProfileUpdateSchema):
    """Update current user's profile."""
    ProfileService.update_profile(
        request.auth.profile,
        data.dict(exclude_unset=True),
        actor=request.auth,
        request=request
    )
    return {"message": "Profil mis à jour avec succès"}


# Address endpoints
@router.get("/me/addresses", response=list[AddressSchema], auth=JWTAuth())
def list_addresses(request):
    """List all addresses for current user."""
    return AddressService.get_user_addresses(request.auth)


@router.post("/me/addresses", response={201: AddressSchema}, auth=JWTAuth())
def create_address(request, data: AddressCreateSchema):
    """Create a new address for current user."""
    address = AddressService.create_address(request.auth, data, request=request)
    return 201, address


@router.get("/me/addresses/{address_id}", response=AddressSchema, auth=JWTAuth())
def get_address(request, address_id: UUID):
    """Get a specific address."""
    address = get_object_or_404(Address, id=address_id, user=request.auth)
    return address


@router.patch("/me/addresses/{address_id}", response=AddressSchema, auth=JWTAuth())
def update_address(request, address_id: UUID, data: AddressUpdateSchema):
    """Update an address."""
    address = get_object_or_404(Address, id=address_id, user=request.auth)
    address = AddressService.update_address(address, data, actor=request.auth, request=request)
    return address


@router.delete("/me/addresses/{address_id}", response={204: None}, auth=JWTAuth())
def delete_address(request, address_id: UUID):
    """Delete an address."""
    address = get_object_or_404(Address, id=address_id, user=request.auth)
    AddressService.delete_address(address, actor=request.auth, request=request)
    return 204, None


# Admin endpoints
@router.get("/", response=list[UserSchema], auth=JWTAuth())
def list_users(request, role: str | None = None, is_active: bool | None = None):
    """List all users (admin only)."""
    if not request.auth.is_admin():
        return []

    queryset = User.objects.all()
    if role:
        queryset = queryset.filter(role=role)
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)

    return queryset


@router.get("/{user_id}", response=UserDetailSchema, auth=JWTAuth())
def get_user(request, user_id: UUID):
    """Get a specific user (admin only)."""
    if not request.auth.is_admin():
        return get_object_or_404(User, id=user_id)

    user = get_object_or_404(User, id=user_id)
    return UserDetailSchema(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        phone_number=user.phone_number,
        role=user.role,
        is_active=user.is_active,
        date_joined=user.date_joined,
        profile=user.profile if hasattr(user, 'profile') else None,
        addresses=list(user.addresses.all()),
    )
