from .root import router as root_router
from .products import router as products_router
from .categories import router as categories_router
from .product_details import router as product_details_router
from .simple_category import router as simple_category_router
from .sync import router as sync_router
from .async_sync import router as async_sync_router

__all__ = [
    "root_router",
    "products_router",
    "categories_router",
    "product_details_router",
    "simple_category_router",
    "sync_router",
    "async_sync_router",
]
