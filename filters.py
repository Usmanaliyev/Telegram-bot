from aiogram.filters import Filter
from aiogram.types import TelegramObject

from shop.models import Role


class RoleFilter(Filter):
    def __init__(self, *rollar: str):
        self.rollar = set(rollar)

    async def __call__(self, event: TelegramObject, user: dict | None = None) -> bool:
        return bool(user) and user["rol"] in self.rollar


class IsAdmin(RoleFilter):
    def __init__(self):
        super().__init__(Role.ADMIN)


class IsCourier(RoleFilter):
    """Adminlar kuryer bo'limidan ham foydalana oladi."""

    def __init__(self):
        super().__init__(Role.KURYER, Role.ADMIN)