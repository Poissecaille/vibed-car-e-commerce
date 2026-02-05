"""Main API configuration with Django Ninja."""
from ninja import NinjaAPI, Router
from ninja_jwt.authentication import JWTAuth
from ninja_jwt.routers.obtain import obtain_pair_router
from ninja_jwt.routers.verify import verify_router

from users.api import router as users_router
from vehicles.api import router as vehicles_router
from inventory.api import router as inventory_router
from wishlist.api import router as wishlist_router
from cart.api import router as cart_router
from orders.api import router as orders_router
from billing.api import router as billing_router
from reviews.api import router as reviews_router

api = NinjaAPI(
    title="Véhicules d'Occasion API",
    version="1.0.0",
    description="API e-commerce pour la vente de véhicules d'occasion",
)

# JWT Authentication endpoints
api.add_router("/token", tags=["Auth"], router=obtain_pair_router)
api.add_router("/token", tags=["Auth"], router=verify_router)

# Register routers
api.add_router("/users", users_router, tags=["Users"])
api.add_router("/vehicles", vehicles_router, tags=["Vehicles"])
api.add_router("/inventory", inventory_router, tags=["Inventory"])
api.add_router("/wishlist", wishlist_router, tags=["Wishlist"])
api.add_router("/cart", cart_router, tags=["Cart"])
api.add_router("/orders", orders_router, tags=["Orders"])
api.add_router("/billing", billing_router, tags=["Billing"])
api.add_router("/reviews", reviews_router, tags=["Reviews"])
