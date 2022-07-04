"""Module provides middlewares to add extra logic to message processing layers."""

import asyncio
from typing import Union

from aiogram import Dispatcher
from aiogram import types as types
from aiogram.dispatcher import DEFAULT_RATE_LIMIT
from aiogram.dispatcher.handler import CancelHandler, current_handler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.utils.exceptions import Throttled


class ThrottlingMiddleware(BaseMiddleware):
    """
    This middleware prevents users from sending too many messages to a chat.
    """
    def __init__(self, limit: float = DEFAULT_RATE_LIMIT, key_prefix: str = "antiflood_"):
        """
        Initialize an instance.
        :param limit: minimum time (in seconds) between two consecutive messages.
        :param key_prefix: prefix to add to a called handler name.
        """
        self.rate_limit = limit
        self.prefix = key_prefix
        super(ThrottlingMiddleware, self).__init__()

    async def on_process_message(self, message: types.Message, data: dict):
        """
        Add extra logic to the "process_message" layer in order to prevent users
        from sending too many messages.
        :param message: message to be processed.
        :param data: message data.
        """
        if message.media_group_id:
            return None

        curr_handler = current_handler.get()
        dispatcher = Dispatcher.get_current()

        if curr_handler:
            limit = getattr(curr_handler, "throttling_rate_limit", self.rate_limit)
            key = getattr(curr_handler, "throttling_key", f"{self.prefix}_{curr_handler.__name__}")
        else:
            limit = self.rate_limit
            key = f"{self.prefix}_message"

        try:
            await dispatcher.throttle(key, rate=limit)
        except Throttled as throttled:
            await message.delete()
            await self.message_throttled(message, throttled)
            raise CancelHandler()

    async def message_throttled(self, message: types.Message, throttled: Throttled):
        """
        Notify a user that they're sending too many messages and need to slow down.
        Then prevent the user from sending messages during the ban.
        At the end of the ban notify the user about unlocking.
        :param message: message to be processed.
        :param throttled: throttling handler.
        """
        handler = current_handler.get()
        dispatcher = Dispatcher.get_current()

        if handler:
            key = getattr(handler, "throttling_key", f"{self.prefix}_{handler.__name__}")
        else:
            key = f"{self.prefix}_message"

        delta = throttled.rate - throttled.delta

        if throttled.exceeded_count <= 2:
            await message.answer(
                "You've been banned for sending too many messages.\nPlease slow down a bit."
            )

        await asyncio.sleep(delta)

        thr = await dispatcher.check_key(key)

        if thr.exceeded_count == throttled.exceeded_count:
            await message.answer("You've been unbanned.")


class GatherMediaGroupMiddleware(BaseMiddleware):
    """
    This middleware gathers all messages belonging to the same media group as one message.
    """
    media_group_data: dict = {}

    def __init__(self, latency: Union[int, float] = 0.01):
        """
        Initialize an instance.
        :param latency: maximum time to wait for the last message of media group.
        """
        self.latency = latency
        super(GatherMediaGroupMiddleware, self).__init__()

    async def on_process_message(self, message: types.Message, data: dict) -> None:
        """
        Add extra logic to the "process_message" layer in case a message belongs to a media group
        so that the first received message of the media group contains the other messages as an attached list.
        :param message: message to be processed.
        :param data: message data.
        """
        if not message.media_group_id:
            return None

        elif message.media_group_id not in self.media_group_data:
            self.media_group_data[message.media_group_id] = [message]
            await asyncio.sleep(self.latency)
            message.conf["is_last"] = True
            data["media_group"] = self.media_group_data[message.media_group_id]

        else:
            self.media_group_data[message.media_group_id].append(message)
            raise CancelHandler()

    async def on_post_process_message(self, message: types.Message, result: dict, data: dict) -> None:
        """
        Add extra logic to the "post_process_message" layer in case a message belongs to a media group
        in order to clean up the middleware buffer.
        :param message: message to be post-processed.
        :param result: result.
        :param data: message data.
        """
        if message.media_group_id and message.conf.get("is_last"):
            del self.media_group_data[message.media_group_id]


def register_middlewares(dp: Dispatcher) -> None:
    """
    Register middlewares to be used by the application.
    """
    dp.setup_middleware(ThrottlingMiddleware(0.5))
    dp.setup_middleware(GatherMediaGroupMiddleware())
