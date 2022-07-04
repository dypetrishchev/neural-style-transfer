"""Module provides message handlers."""

from io import BytesIO
from typing import List

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext

from src.states import StartStyleTransferForm
from src.utils.requests import request_style_transfer, request_examples, get_api_url


async def help_cmd_handler(message: types.Message):
    """
    Set the "/help" command behavior.
    """
    msg = (
        "Here are my commands:\n"
        "/help - list of commands\n"
        "/examples - show examples of style transfer\n"
        "/start - let's get acquainted!\n"
        "/transfer - transfer a style from one image to another\n"
        "/cancel - cancel the current operation"
    )
    await message.reply(msg)


async def start_cmd_handler(message: types.Message):
    """
    Set the "/start" command behavior.
    """
    bot_info = await message.bot.get_me()
    msg = (
        "Hi, {user_name}!\n"
        "My name is \"{bot_name}\".\n"
        "Nice to meet you!\n"
        "I can transfer the style from one image to another.\n"
        "Here are some \"/examples\".\n"
        "Would you like to try?"
    )
    inline_keyboard = types.InlineKeyboardMarkup(row_width=2).add(
        types.InlineKeyboardButton(text="Yes!", callback_data="start_style_transfer"),
        types.InlineKeyboardButton(text="Maybe later...", callback_data="postpone_style_transfer")
    )
    await message.reply(
        msg.format(user_name=message.from_user.first_name, bot_name=bot_info.first_name),
        reply_markup=inline_keyboard
    )


async def start_style_transfer_cmd_handler(message: types.Message):
    """
    Ask the user to choose a style.
    """
    await StartStyleTransferForm.choose_style.set()
    inline_keyboard = types.InlineKeyboardMarkup(row_width=1).add(
        types.InlineKeyboardButton(text="Claude Monet", callback_data="style_monet"),
        types.InlineKeyboardButton(text="Vincent van Gogh", callback_data="style_vangogh"),
        types.InlineKeyboardButton(text="Paul Cézanne", callback_data="style_cezanne"),
        types.InlineKeyboardButton(text="Ukiyo-e", callback_data="style_ukiyoe"),
        types.InlineKeyboardButton(text="Custom", callback_data="style_custom")
    )
    await message.answer(
        "Which style would you like to use?\n"
        "You can choose one of the suggested styles or whichever you want (the \"Custom\" option)",
        reply_markup=inline_keyboard
    )


async def receive_style_image_handler(message: types.Message, state: FSMContext):
    """
    Receive a style-image from the user and ask them to send content-images.
    """
    async with state.proxy() as data:
        style_image = BytesIO()
        await message.photo[-1].download(destination_file=style_image)
        data["style_image"] = style_image
    await StartStyleTransferForm.next()
    await message.answer(
        "Thanks!\n"
        f"Now send me up to {StartStyleTransferForm.max_images} images that you would like to transform.\n"
        "Please make sure that it will be a single image or a gallery, "
        "otherwise only the first image will be processed.\n"
        "For better results use square images."
    )


async def receive_content_image_handler(message: types.Message, state: FSMContext):
    """
    Receive a content-image from the user.
    Then send style and content images to the model application.
    Then receive the result and send it back to the user.
    """
    async with state.proxy() as data:
        content_image = BytesIO()
        await message.photo[-1].download(destination_file=content_image)
        data["content_images"] = [content_image]

    await StartStyleTransferForm.next()
    await message.answer(
        "Ok, the magic has begun! It can take a while. I'll text you when it's done."
    )

    try:
        async with Dispatcher.get_current().current_state().proxy() as data:
            processed_images = await request_style_transfer(
                get_api_url(message.bot["config"]["model_app"]["model_url"], "transfer"),
                data["style"],
                data["style_image"],
                data["content_images"],
                message.bot["config"]["model_app"]["username"],
                message.bot["config"]["model_app"]["password"],
                message.bot["config"]["bot_app"]["verify_ssl"]
            )

        curr_state = await Dispatcher.get_current().current_state().get_state()
        if curr_state == StartStyleTransferForm.await_model_response.state:
            await message.answer("Here you are!")
            await message.answer_photo(types.InputFile(processed_images[0]))

    finally:
        await state.finish()


async def receive_content_images_handler(message: types.Message, media_group: List[types.Message], state: FSMContext):
    """
    Receive content-images from the user.
    Then send style and content images to the model application.
    Then receive the result and send it back to the user.
    """
    async with state.proxy() as data:
        data["content_images"] = []
        for msg in media_group:
            if msg.photo and len(data["content_images"]) < StartStyleTransferForm.max_images:
                content_image = BytesIO()
                await msg.photo[-1].download(destination_file=content_image)
                data["content_images"].append(content_image)

    await StartStyleTransferForm.next()
    await message.answer(
        "Ok, the magic has begun! It can take a while. I'll text you when it's done."
    )

    try:
        async with Dispatcher.get_current().current_state().proxy() as data:
            processed_images = await request_style_transfer(
                get_api_url(message.bot["config"]["model_app"]["model_url"], "transfer"),
                data["style"],
                data["style_image"],
                data["content_images"],
                message.bot["config"]["model_app"]["username"],
                message.bot["config"]["model_app"]["password"],
                message.bot["config"]["bot_app"]["verify_ssl"]
            )

        media = types.MediaGroup()
        for image in processed_images:
            media.attach_photo(types.InputMediaPhoto(image))

        curr_state = await Dispatcher.get_current().current_state().get_state()
        if curr_state == StartStyleTransferForm.await_model_response.state:
            await message.answer("Here you are!")
            await message.answer_media_group(media)

    finally:
        await state.finish()


async def other_message_handler(message: types.Message, state: FSMContext):
    """
    Handle user messages which are out of the script.
    """
    curr_state = await state.get_state()
    if not curr_state:
        await message.reply("Sorry, I only understand commands. Feel free to use \"/help\".")

    elif curr_state == StartStyleTransferForm.choose_style.state:
        await message.reply(
            "Just a little reminder.\n"
            "For now I expect you to choose a style from the list.\n"
            "If you want to cancel the current operation, just send \"/cancel\" to the chat."
        )

    elif curr_state == StartStyleTransferForm.send_style_image.state:
        await message.reply(
            "Just a little reminder.\n"
            "For now I expect you to send me a single style-image.\n"
            "If you want to cancel the current operation, just send \"/cancel\" to the chat."
        )

    elif curr_state == StartStyleTransferForm.send_content_images.state:
        await message.reply(
            "Just a little reminder.\n"
            f"For now I expect you to send me up to {StartStyleTransferForm.max_images} images to be transformed.\n"
            "If you want to cancel the current operation, just send \"/cancel\" to the chat"
        )

    elif curr_state == StartStyleTransferForm.await_model_response.state:
        await message.reply(
            "I'm working on your request. Please wait a moment.\n"
            "If you want to cancel the current operation, just send \"/cancel\" to the chat"
        )


async def cancel_cmd_handler(message: types.Message, state: FSMContext):
    """
    Set "/cancel" command behavior.
    """
    curr_state = await state.get_state()
    if not curr_state:
        await message.reply("Nothing to cancel")
        return None
    await state.finish()
    await message.reply("Operation is cancelled.\nSee you next time!")


async def examples_cmd_handler(message: types.Message):
    """
    Set "/examples" command behavior.
    """
    await message.answer("Here are examples of style transfer:")
    examples = await request_examples(
        get_api_url(message.bot["config"]["model_app"]["model_url"], "examples"),
        message.bot["config"]["model_app"]["username"],
        message.bot["config"]["model_app"]["password"],
        message.bot["config"]["bot_app"]["verify_ssl"]
    )
    media = types.MediaGroup()
    for example in examples:
        media.attach_photo(types.InputMediaPhoto(example))
    await message.answer_media_group(media)


def register_message_handlers(dp: Dispatcher) -> None:
    """
    Register message handlers to be used by the application.
    """
    dp.register_message_handler(cancel_cmd_handler, state="*", commands=["cancel"])
    dp.register_message_handler(help_cmd_handler, commands=["help"])
    dp.register_message_handler(start_cmd_handler, commands=["start"])
    dp.register_message_handler(start_style_transfer_cmd_handler, commands=["transfer"])
    dp.register_message_handler(examples_cmd_handler, commands=["examples"])
    dp.register_message_handler(
        receive_style_image_handler,
        content_types=["photo"],
        state=StartStyleTransferForm.send_style_image,
        is_media_group=False
    )
    dp.register_message_handler(
        receive_content_images_handler,
        content_types=["photo"],
        state=StartStyleTransferForm.send_content_images,
        is_media_group=True
    )
    dp.register_message_handler(
        receive_content_image_handler,
        content_types=["photo"],
        state=StartStyleTransferForm.send_content_images
    )
    dp.register_message_handler(other_message_handler, state="*", content_types=["any"])
