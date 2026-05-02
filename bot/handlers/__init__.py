from .user import router as user_router
from .admin import router as admin_router
from .faq import router as faq_router
from .security import router as security_router

__all__ = ["user_router", "admin_router", "faq_router", "security_router"]
