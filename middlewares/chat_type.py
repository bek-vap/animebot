from typing import Callable, Awaitable, Any
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery


class PrivateChatOnlyMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict], Awaitable[Any]],
        event: TelegramObject,
        data: dict,
    ) -> Any:
        if isinstance(event, Message):
            if event.chat.type != "private":
                return
        elif isinstance(event, CallbackQuery):
            if event.message and event.message.chat.type != "private":
                return
        return await handler(event, data)
