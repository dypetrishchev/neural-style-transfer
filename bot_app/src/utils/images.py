"""Module provides useful functions to process images."""


import base64
from io import BytesIO


def image_to_base64(image: BytesIO) -> str:
    """
    Encode an image with base64 algorithm and convert it to a string.
    :param image: image to be converted.
    :return: string representation of encoded image.
    """
    image.seek(0)
    return base64.encodebytes(image.read()).decode()


def base64_to_image(image: str) -> BytesIO:
    """
    Convert a string representation of image to bytes and decode them with base64 algorithm.
    :param image: string representation of encoded image.
    :return: decoded image.
    """
    return BytesIO(base64.decodebytes(image.encode()))
