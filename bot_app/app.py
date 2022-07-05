"""Run the telegram bot in the polling mode."""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from src.handlers import register_message_handlers, register_callback_query_handlers, register_error_handlers
from src.middlewares import register_middlewares
from src.utils.utils import load_config

logger = logging.getLogger(__name__)


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s"
    )
    logger.info("Starting bot")

    config = load_config("config.yaml")

    storage = MemoryStorage()
    bot = Bot(token=config["bot_app"]["api_token"])
    dp = Dispatcher(bot, storage=storage)

    bot["config"] = config

    register_middlewares(dp)
    register_message_handlers(dp)
    register_callback_query_handlers(dp)
    register_error_handlers(dp)

    try:
        await dp.skip_updates()
        await dp.start_polling()
    finally:
        await dp.storage.close()
        await dp.storage.wait_closed()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error("Bot stopped!")
