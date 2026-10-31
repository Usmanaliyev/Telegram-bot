import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter

logger = logging.getLogger(__name__)


async def safe_send(bot: Bot, chat_id: int, text: str, reply_markup=None, **kwargs) -> bool:
    try:
        await bot.send_message(chat_id, text, reply_markup=reply_markup, **kwargs)
        return True
    except TelegramRetryAfter as exc:
        await asyncio.sleep(exc.retry_after)
        return await safe_send(bot, chat_id, text, reply_markup, **kwargs)
    except TelegramForbiddenError:
        logger.info("User %s blocked the bot", chat_id)
        return False
    except Exception as exc:  # noqa: BLE001
        logger.warning("send_message to %s failed: %s", chat_id, exc)
        return False


async def fan_out(bot: Bot, chat_ids, text: str, reply_markup=None,
                  delay: float = 0.05) -> tuple[int, int]:
    """Telegram limiti: sekundiga ~30 xabar. delay bilan ~20 ta yuboramiz."""
    sent = failed = 0
    for chat_id in chat_ids:
        if await safe_send(bot, chat_id, text, reply_markup):
            sent += 1
        else:
            failed += 1
        await asyncio.sleep(delay)
    return sent, failed