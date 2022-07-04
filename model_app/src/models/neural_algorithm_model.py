"""Module provides custom models that are used to transfer a style from one image to another."""

from copy import deepcopy
from typing import Iterable, Tuple

import torch
import torch.nn as nn
import torchvision.transforms as tt

from src.losses import ContentLoss, StyleLoss


class NeuralAlgorithmModel(nn.Module):
    """Model that transfers a style from one image to another."""
    def __init__(
        self,
        backbone: nn.Module,
        content_img: torch.Tensor,
        style_img: torch.Tensor,
        content_ids: Iterable,
        style_ids: Iterable,
        mean: list | tuple = (0.485, 0.456, 0.406),
        std: list | tuple = (0.229, 0.224, 0.225),
        device: str = ("cpu" if not torch.cuda.is_available() else "cuda")
    ):
        """
        Initialize an instance.
        :param backbone: pretrained model to use its layers as a base.
        :param content_img: target image for the content.
        :param style_img: target image for the style.
        :param content_ids: indices of backbone model convolution layers to put a content loss instance after.
        :param style_ids: indices of backbone model convolution layers to put a style loss instance after.
        :param mean: means for each channel to normalize input image.
        :param std: standard deviations for each channel to normalize input image.
        :param device: device to use (e.g. "cpu", "cuda").
        """
        super(NeuralAlgorithmModel, self).__init__()

        self.content_img = content_img
        self.style_img = style_img
        self.content_ids = content_ids
        self.style_ids = style_ids
        self.device = device

        self.model, self.content_losses, self.style_losses = self._get_model(
            backbone,
            content_img, style_img,
            content_ids, style_ids,
            mean, std
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Define how the module is going to be run from input to output.
        :param x: input tensor.
        :return: output tensor.
        """
        return self.model(x)

    def _get_model(
        self,
        backbone: nn.Module,
        content_img: torch.Tensor,
        style_img: torch.Tensor,
        content_ids: Iterable,
        style_ids: Iterable,
        mean: list | tuple = None,
        std: list | tuple = None
    ) -> Tuple[nn.Module, list, list]:
        """
        Construct a style transfer model instance using backbone model layers.
        :param backbone: pretrained model to use its layers as a base.
        :param content_img: target image for content.
        :param style_img: target image for style.
        :param content_ids: indices of backbone model convolution layers to put a content loss instance after.
        :param style_ids: indices of backbone model convolution layers to put a style loss instance after.
        :param mean: means for each channel to normalize input image.
        :param std: standard deviations for each channel to normalize input image.
        :return: custom model that is used to transfer style from one image to another.
        """
        model = nn.Sequential()
        if mean and std:
            model.append(tt.Normalize(mean, std))

        content_losses, style_losses = [], []
        conv_cnt = 0

        for layer in backbone.to(self.device).children():
            model.append(deepcopy(layer) if not isinstance(layer, nn.ReLU) else nn.ReLU(False))

            if isinstance(layer, nn.Conv2d):
                conv_cnt += 1
                if conv_cnt in content_ids:
                    content_loss = ContentLoss(model(content_img.to(self.device)))
                    model.append(content_loss)
                    content_losses.append(content_loss)

                if conv_cnt in style_ids:
                    style_loss = StyleLoss(model(style_img.to(self.device)))
                    model.append(style_loss)
                    style_losses.append(style_loss)

            if conv_cnt == max(max(content_ids), max(style_ids)):
                break

        return model, content_losses, style_losses
