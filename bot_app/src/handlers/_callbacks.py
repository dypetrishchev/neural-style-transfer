"""Module provides callback query handlers."""

from aiogram import types
from aiogram.dispatcher import Dispatcher

from src.handlers._messages import start_style_transfer_cmd_handler
from src.states import StartStyleTransferForm


async def start_style_transfer_callback_handler(callback: types.CallbackQuery):
    """
    Branch of the "/start" command dialogue that leads to sending style and content images by the user.
    """
    await callback.message.answer("Great! We're starting!")
    await start_style_transfer_cmd_handler(callback.message)


async def postpone_style_transfer_callback_handler(callback: types.CallbackQuery):
    """
    Branch of the "/start" command dialogue that ends the conversation with the user.
    """
    msg = (
        "Ok, maybe next time... Anyway I'll be here.\n"
        "In case you change your mind, just send me this \"/transfer\"."
    )
    await callback.message.answer(msg)


async def receive_chosen_style_callback_handler(callback: types.CallbackQuery):
    """
    Receive a chosen style from the user.
    """
    if callback.data != "style_custom":
        await StartStyleTransferForm.send_content_images.set()
        async with Dispatcher.get_current().current_state().proxy() as data:
            data["style"] = callback.data
            data["style_image"] = None

        await callback.message.answer(
            f"Please send me up to {StartStyleTransferForm.max_images} images that you would like to transform.\n"
            "Please make sure that it will be a single image or a gallery, "
            "otherwise only the first image will be processed."
        )

    else:
        await StartStyleTransferForm.next()
        async with Dispatcher.get_current().current_state().proxy() as data:
            data["style"] = callback.data

        await callback.message.answer(
            "Please send me a single image with the style you would like to transfer. "
            "For better results use a square image."
        )


def register_callback_query_handlers(dp: Dispatcher) -> None:
    """
    Register callback query handlers to be used by the application.
    """
    dp.register_callback_query_handler(
        start_style_transfer_callback_handler,
        text="start_style_transfer"
    )
    dp.register_callback_query_handler(
        postpone_style_transfer_callback_handler,
        text="postpone_style_transfer"
    )
    dp.register_callback_query_handler(
        receive_chosen_style_callback_handler,
        state=StartStyleTransferForm.choose_style
    )
