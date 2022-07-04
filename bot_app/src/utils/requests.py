"""Module provides useful functions to make requests."""

from io import BytesIO
from typing import List, Union

import aiohttp

from src.utils.images import image_to_base64, base64_to_image


async def request_style_transfer(
    url: str,
    style: str,
    style_image: BytesIO,
    content_images: List[BytesIO],
    username: str,
    password: str,
    verify_ssl: bool = True,
    timeout: Union[int, float] = 600
) -> List[BytesIO]:
    """
    Send style and content images as a json file to the model application
    and receive processed images from the latter.
    :param url: API url path of the model to send a request to.
    :param style: style name (e.g. "style_monet", "style_custom").
    :param style_image: style-image.
    :param content_images: content-images.
    :param username: username to sign in.
    :param password: password to sign in.
    :param verify_ssl: whether to accept self-signed ssl certificates.
    :param timeout: maximum time (in seconds) to wait for a response.
    :return: processed images.
    """
    async with aiohttp.ClientSession() as session:
        data = {
            "style": style,
            "style_image": image_to_base64(style_image) if style_image else "",
            "content_images": [image_to_base64(content_image) for content_image in content_images],
            "username": username,
            "password": password
        }
        async with session.post(
            url,
            json=data,
            verify_ssl=verify_ssl,
            timeout=timeout*len(content_images)
        ) as response:
            processed_images = await response.json()
    processed_images = [base64_to_image(image) for image in processed_images["fitted_images"]]
    return processed_images


async def request_examples(
    url: str,
    username: str,
    password: str,
    verify_ssl: bool = True,
    timeout: Union[int, float] = 60
) -> List[BytesIO]:
    """
    Request examples of style transfer.
    :param url: API url path of the model to send a request to.
    :param username: username to sign in.
    :param password: password to sign in.
    :param verify_ssl: whether to accept self-signed ssl certificates.
    :param timeout: maximum time (in seconds) to wait for a response.
    :return: processed images.
    """
    async with aiohttp.ClientSession() as session:
        data = {"username": username, "password": password}
        async with session.post(url, json=data, verify_ssl=verify_ssl, timeout=timeout) as response:
            examples = await response.json()
    examples = [base64_to_image(image) for image in examples["example_images"]]
    return examples


def get_api_url(model_url: str, action: str) -> str:
    """
    Create an api url path.
    :param model_url: api url path of the style transfer model.
    :param action: action to be done.
    :return: api url path.
    """
    url = "/".join([model_url.rstrip("/"), action])
    return url
