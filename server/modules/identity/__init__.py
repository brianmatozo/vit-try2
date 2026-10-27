"""Identity domain module: users, profiles, and authentication."""

from server.modules.identity.models import User
from server.modules.identity.router import router

__all__ = ["User", "router"]
