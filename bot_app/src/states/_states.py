"""Module provides state classes to guide the user through the script."""

from aiogram.dispatcher.filters.state import StatesGroup, State


class StartStyleTransferForm(StatesGroup):
    """
    This script consists of two stages.
    The first stage is for choosing a style to use.
    The second stage is for receiving a single style-image from the user.
    The third stage is for receiving up to `max_images` content-images from the user.
    """
    max_images = 3
    choose_style = State()
    send_style_image = State()
    send_content_images = State()
    await_model_response = State()
