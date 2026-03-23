from .products import router as products_router
from .missions import router as missions_router
from .users import router as users_router
from .issues import router as issues_router
from .maintainers import router as maintainers_router

__all__ = [
    "products_router",
    "missions_router",
    "users_router",
    "issues_router",
    "maintainers_router",
]
