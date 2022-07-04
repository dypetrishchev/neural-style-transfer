"""Module provides useful functions to make requests."""

import functools
from io import BytesIO
from typing import Tuple, List, Callable, Any

import torch
from flask import request
from torchvision.transforms.functional import to_pil_image
from werkzeug.security import check_password_hash
from yaml import safe_load

from src.utils.images import load_image_from_buffer, base64_to_image, image_to_base64


def extract_original_images(json: dict, with_style: bool = True) -> Tuple[torch.Tensor, List[torch.Tensor]]:
    """
    Parse a received request in order to extract style and content images
    and convert them to torch tensors.
    :param json: request as a python dict.
    :param with_style: whether to extract the style image.
    :return: style and content images as torch tensors.
    """
    if with_style:
        size = [512, 512] if torch.cuda.is_available() else [256, 256]
        style_image = load_image_from_buffer(base64_to_image(json["style_image"]), size)
    else:
        size = None
        style_image = None

    content_images = [
        load_image_from_buffer(base64_to_image(image), size)
        for image in json["content_images"]
    ]

    return style_image, content_images


def pack_processed_images(fitted_images: List[torch.Tensor]) -> dict:
    """
    Convert each fitted image to a string encoded with base64 algorithm.
    :param fitted_images: fitted images.
    :return: encoded images.
    """
    response = {"fitted_images": []}
    for image in fitted_images:
        buffer = BytesIO()
        to_pil_image(image, mode="RGB").save(buffer, format="PNG")
        response["fitted_images"].append(image_to_base64(buffer))
    return response


def load_users(path: str) -> dict:
    """
    Load the white list of users.
    :param path: path to file.
    :return: application users.
    """
    with open(path) as f:
        users = safe_load(f)
    return users


def login(users: dict) -> Callable:
    """
    Check whether a user can make requests to the application.
    :param users: white list of users.
    """
    def outer_wrapper(func: Callable) -> Callable:
        @functools.wraps(func)
        def inner_wrapper(*args, **kwargs) -> Any:
            user = request.json.get("username")
            pwd = request.json.get("password")
            if user and pwd:
                if user in users and check_password_hash(users[user], pwd):
                    return func(*args, **kwargs)
                return "Authentication is failed.\nWrong username or password."
            return "Request must contain the following keys: [\"username\", \"password\"]."
        return inner_wrapper
    return outer_wrapper
