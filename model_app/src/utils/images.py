"""Module provides useful functions to process images."""

import base64
import random
from io import BytesIO
from os.path import dirname, join
from typing import Union, List

import matplotlib.pyplot as plt
import torch
from PIL import Image
from torchvision.io import read_image
from torchvision.transforms.functional import convert_image_dtype, resize, to_tensor


def load_image_from_file(path: str, size: Union[int, List[int]] = None) -> torch.Tensor:
    """
    Load and process an image from a file.
    :param path: image path.
    :param size: desired output size.
    :return: processed image.
    """
    image = read_image(path)
    image = convert_image_dtype(image)
    if size:
        image = resize(image, size, antialias=True)
    return image[None]


def load_image_from_buffer(buffer: BytesIO, size: Union[int, List[int]] = None) -> torch.Tensor:
    """
    Load and process an image from a byte buffer.
    :param buffer: byte buffer.
    :param size: desired output size.
    :return: processed image.
    """
    buffer.seek(0)
    image = Image.open(buffer)
    image = to_tensor(image)
    if size:
        image = resize(image, size, antialias=True)
    return image[None]


def plot_examples(images: List[torch.Tensor], titles: list = None, size: int = 5, fontsize: int = None) -> tuple:
    """
    Plot images in a row.
    :param images: images to be plotted.
    :param titles: titles.
    :param size: size of figure.
    :param fontsize: size of title font.
    :return: figure and axes.
    """
    ncols = len(images)
    fig, axes = plt.subplots(1, ncols, figsize=(ncols * size, size))
    for (idx, ax) in enumerate(axes.flatten()):
        ax.imshow(images[idx][0].detach().cpu().numpy().transpose((1, 2, 0)))
        ax.axis("off")
        if titles:
            ax.set_title(titles[idx], fontsize=fontsize)
    return fig, axes


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


class ImagePool:
    """This class implements an image buffer that stores previously generated images.

    This buffer enables us to update discriminators using a history of generated images
    rather than the ones produced by the latest generators.
    """

    def __init__(self, pool_size):
        """Initialize the ImagePool class

        Parameters:
            pool_size (int) -- the size of image buffer, if pool_size=0, no buffer will be created
        """
        self.pool_size = pool_size
        if self.pool_size > 0:  # create an empty pool
            self.num_imgs = 0
            self.images = []

    def query(self, images):
        """Return an image from the pool.

        Parameters:
            images: the latest generated images from the generator

        Returns images from the buffer.

        By 50/100, the buffer will return input images.
        By 50/100, the buffer will return images previously stored in the buffer,
        and insert the current images to the buffer.
        """
        if self.pool_size == 0:  # if the buffer size is 0, do nothing
            return images
        return_images = []
        for image in images:
            image = torch.unsqueeze(image.data, 0)
            if self.num_imgs < self.pool_size:   # if the buffer is not full; keep inserting current images to the buffer
                self.num_imgs = self.num_imgs + 1
                self.images.append(image)
                return_images.append(image)
            else:
                p = random.uniform(0, 1)
                if p > 0.5:  # by 50% chance, the buffer will return a previously stored image, and insert the current image into the buffer
                    random_id = random.randint(0, self.pool_size - 1)  # randint is inclusive
                    tmp = self.images[random_id].clone()
                    self.images[random_id] = image
                    return_images.append(tmp)
                else:       # by another 50% chance, the buffer will return the current image
                    return_images.append(image)
        return_images = torch.cat(return_images, 0)   # collect all the images and return
        return return_images


def get_examples() -> dict:
    """
    Prepare examples of style transfer.
    :return: examples of style transfer.
    """
    examples = {"example_images": []}
    styles = ["style_monet", "style_vangogh", "style_cezanne", "style_ukiyoe", "style_custom"]

    root = join(dirname(dirname(dirname(__file__))), "examples")
    for style in styles:
        buffer = BytesIO()
        image = Image.open(join(root, style, "transformed.png"))
        image.save(buffer, format="PNG")
        examples["example_images"].append(image_to_base64(buffer))

    return examples
