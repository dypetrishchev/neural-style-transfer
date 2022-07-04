"""Module provides custom loss functions that are used to transfer a style from one image to another."""

import torch
import torch.nn as nn
import torch.nn.functional as F


class ContentLoss(nn.Module):
    """Loss function that measures how different the content is between two images"""
    def __init__(self, target: torch.Tensor):
        """
        Initialize an instance.
        :param target: reference image to measure content difference with.
        """
        super(ContentLoss, self).__init__()
        self.target = nn.Parameter(target.detach())
        self.loss = None

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Define how the module is going to be run from input to output.
        :param x: input tensor.
        :return: output tensor.
        """
        self.loss = F.mse_loss(x, self.target)
        return x


class StyleLoss(nn.Module):
    """Loss function that measures how different the style is between two images"""
    def __init__(self, target: torch.Tensor):
        """
        Initialize an instance.
        :param target: reference image to measure style difference with.
        """
        super(StyleLoss, self).__init__()
        self.target = nn.Parameter(self._to_gram_matrix(target.detach()))
        self.loss = None

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Define how the module is going to be run from input to output.
        :param x: input tensor.
        :return: output tensor.
        """
        self.loss = F.mse_loss(self._to_gram_matrix(x), self.target)
        return x

    @staticmethod
    def _to_gram_matrix(x: torch.Tensor) -> torch.Tensor:
        """
        Compute the gram matrix for a given tensor.
        :param x: tensor to compute the gram matrix for.
        :return: gram matrix.
        """
        d1, d2, d3, d4 = x.shape
        x = x.view(d1 * d2, d3 * d4)
        return x.mm(x.T) / x.numel()
