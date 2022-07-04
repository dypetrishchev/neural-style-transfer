"""Module provides error handlers."""

from asyncio.exceptions import TimeoutError

from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiohttp import ClientOSError


async def timeout_error_handler(update: types.Update, exception: TimeoutError) -> bool:
    """
    Handle the timeout error.
    :param update: update.
    :param exception: timeout exception.
    """
    await update.message.answer(
        "Sorry!\n"
        "It seems like the model service or the telegram server is too busy right now.\n"
        "Please try it later."
    )
    return True


async def client_os_error_handler(update: types.Update, exception: ClientOSError) -> bool:
    """
    Handle the client os error.
    :param update: update.
    :param exception: client os exception.
    """
    await update.message.answer(
        "Sorry!\n"
        "It seems like the model service is unavailable right now.\n"
        "Please try it later."
    )
    return True


async def other_errors_handler(update: types.Update, exception: Exception) -> bool:
    """
    Handle any other exception.
    :param update: update.
    :param exception: any exception.
    """
    excluded_exceptions = [TimeoutError, ClientOSError]
    if all(map(lambda x: not isinstance(exception, x), excluded_exceptions)):
        await update.message.answer("Sorry! Something went wrong. Please try it later.")
    return True


def register_error_handlers(dp: Dispatcher) -> None:
    """
    Register error handlers to be used by the application.
    """
    dp.register_errors_handler(timeout_error_handler, exception=TimeoutError)
    dp.register_errors_handler(client_os_error_handler, exception=ClientOSError)
    dp.register_errors_handler(other_errors_handler)
