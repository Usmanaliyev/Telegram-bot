import time

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, Update

import services

BLOKLANGAN = "🚫 Siz bloklangansiz. Administrator bilan bog'laning."


class AuthMiddleware(BaseMiddleware):
    """Har bir update uchun foydalanuvchini bazadan oladi va data['user'] ga soladi."""

    async def __call__(self, handler, event: TelegramObject, data: dict):
        tg_user = data.get("event_from_user")
        if tg_user is None or tg_user.is_bot:
            return await handler(event, data)

        user = await services.user_olish(tg_user.id, tg_user.full_name)
        if user["bloklangan"]:
            await self._rad_etish(event)
            return None

        data["user"] = user
        return await handler(event, data)

    @staticmethod
    async def _rad_etish(event: TelegramObject) -> None:
        # Outer middleware Update oladi - ichidagi hodisani ochib olamiz
        target = event.event if isinstance(event, Update) else event
        if isinstance(target, Message):
            await target.answer(BLOKLANGAN)
        elif isinstance(target, CallbackQuery):
            await target.answer(BLOKLANGAN, show_alert=True)


class ThrottlingMiddleware(BaseMiddleware):
    """rate soniyadan tez kelgan hodisalarni tashlab yuboradi."""

    def __init__(self, rate: float = 0.35):
        self.rate = rate
        self._korilgan: dict[int, float] = {}

    async def __call__(self, handler, event: TelegramObject, data: dict):
        tg_user = data.get("event_from_user")
        if tg_user is None:
            return await handler(event, data)

        hozir = time.monotonic()
        if hozir - self._korilgan.get(tg_user.id, 0.0) < self.rate:
            target = event.event if isinstance(event, Update) else event
            if isinstance(target, CallbackQuery):
                await target.answer("⏳ Sekinroq…")
            return None

        self._korilgan[tg_user.id] = hozir
        return await handler(event, data)