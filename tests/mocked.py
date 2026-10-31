"""Soxta Telegram transporti — chaqiruvlarni yozib boradi, tarmoqqa chiqmaydi."""
from __future__ import annotations

import datetime as dt
from collections.abc import AsyncGenerator
from typing import Any

from aiogram import Bot
from aiogram.client.session.base import BaseSession
from aiogram.methods import TelegramMethod
from aiogram.types import CallbackQuery, Chat, Message, Update, User

TEST_BOT = User(id=42, is_bot=True, first_name="TestBot", username="test_bot")


class MockedSession(BaseSession):
    def __init__(self):
        super().__init__()
        self.requests: list[TelegramMethod[Any]] = []
        self._message_id = 1000

    def calls(self, method_name: str) -> list[TelegramMethod[Any]]:
        return [r for r in self.requests if type(r).__name__ == method_name]

    @property
    def texts(self) -> list[str]:
        out = []
        for req in self.requests:
            for field in ("text", "caption"):
                value = getattr(req, field, None)
                if isinstance(value, str):
                    out.append(value)
        return out

    def contains(self, needle: str) -> bool:
        return any(needle in t for t in self.texts)

    def clear(self) -> None:
        self.requests.clear()

    async def close(self) -> None:
        return None

    async def stream_content(self, *args, **kwargs) -> AsyncGenerator[bytes, None]:
        yield b""

    async def make_request(self, bot: Bot, method: TelegramMethod[Any], timeout: int | None = None):
        self.requests.append(method)
        name = type(method).__name__
        if name == "GetMe":
            return TEST_BOT
        if name.startswith(("Send", "Edit", "Copy")):
            self._message_id += 1
            return Message(
                message_id=self._message_id,
                date=dt.datetime.now(dt.UTC),
                chat=Chat(id=int(getattr(method, "chat_id", None) or 1), type="private"),
                from_user=TEST_BOT,
                text=getattr(method, "text", None) or getattr(method, "caption", None) or "",
            )
        return True


class Conversation:
    """Update'larni Dispatcher'ga xuddi real odam bosayotgandek uzatadi."""

    def __init__(self, dp, bot: Bot, session: MockedSession, user_id: int, ism: str):
        self.dp, self.bot, self.session = dp, bot, session
        self.user = User(id=user_id, is_bot=False, first_name=ism)
        self.chat = Chat(id=user_id, type="private")
        self._n = 0

    def _next(self) -> int:
        self._n += 1
        return self._n

    async def send(self, text: str | None = None, **extra) -> MockedSession:
        self.session.clear()
        n = self._next()
        message = Message(message_id=n, date=dt.datetime.now(dt.UTC), chat=self.chat,
                          from_user=self.user, text=text, **extra)
        await self.dp.feed_update(self.bot, Update(update_id=n, message=message))
        return self.session

    async def click(self, data: str) -> MockedSession:
        self.session.clear()
        n = self._next()
        source = Message(message_id=1, date=dt.datetime.now(dt.UTC), chat=self.chat,
                         from_user=TEST_BOT, text="…")
        call = CallbackQuery(id=f"cb{n}", from_user=self.user, chat_instance="test",
                             data=data, message=source)
        await self.dp.feed_update(self.bot, Update(update_id=n, callback_query=call))
        return self.session

    def buttons(self) -> list[tuple[str, str]]:
        pairs: list[tuple[str, str]] = []
        for req in reversed(self.session.requests):
            markup = getattr(req, "reply_markup", None)
            rows = getattr(markup, "inline_keyboard", None)
            if not rows:
                continue
            for row in rows:
                for btn in row:
                    if btn.callback_data:
                        pairs.append((btn.text, btn.callback_data))
            if pairs:
                break
        return pairs

    def find(self, needle: str) -> str | None:
        return next((d for t, d in self.buttons() if needle in t), None)