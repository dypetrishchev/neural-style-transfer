"""
Module provides custom trainers that are used to fit
an input image to desired style via a style transfer model.
"""

from datetime import datetime
from typing import Callable

import torch
import torch.nn as nn
import torch.optim as optim


class Trainer:
    """Trainer that uses a style transfer model to fit an input image to desired style."""
    def __init__(
        self,
        model: nn.Module,
        device: str = ("cpu" if not torch.cuda.is_available() else "cuda")
    ):
        """
        Initialize an instance.
        :param model: style transfer model.
        :param device: device to use (e.g. "cpu", "cuda")
        """
        self.model = model.eval().to(device).requires_grad_(False)
        self.device = device
        self._counter = None
        self._content_loss = None
        self._style_loss = None

    def fit(
        self,
        input_img: torch.Tensor,
        max_iter: int = 300,
        content_weight: float = 1,
        style_weight: float = 10**6,
        verbose: int = None,
        inplace: bool = False
    ) -> torch.Tensor:
        """
        Fit an input image to desired style.
        :param input_img: image to be fitted.
        :param max_iter: maximum number of iterations of the optimization algorithm.
        :param content_weight: content loss weight.
        :param style_weight: style loss weight.
        :param verbose: frequency (in iterations) to display performance metrics.
        :param inplace: whether to use an original input image or clone it before fitting.
        :return: fitted image.
        """
        self._init_params()

        if not inplace:
            input_img = input_img.clone()
        input_img = input_img.to(self.device).requires_grad_(True)

        optimizer = self._get_optimizer(input_img)
        closure_fn = self._get_closure_fn(input_img, optimizer, content_weight, style_weight, verbose)

        while self._counter < max_iter:
            optimizer.step(closure_fn)
        if verbose:
            self._print_metrics()

        with torch.no_grad():
            input_img.clamp_(0, 1)

        return input_img

    def _init_params(self) -> None:
        """
        Set initial state of internal parameters that are used to fit an input image to desired style.
        """
        self._counter = 0
        self._content_loss = float("inf")
        self._style_loss = float("inf")

    @staticmethod
    def _get_optimizer(input_img: torch.Tensor) -> optim.Optimizer:
        """
        Create an optimizer that is used to fit an input image to desired style.
        :param input_img: image to be fitted.
        :return: optimizer to use.
        """
        optimizer = optim.LBFGS([input_img])
        return optimizer

    def _get_closure_fn(
        self,
        input_img: torch.Tensor,
        optimizer: optim.Optimizer,
        content_weight: float,
        style_weight: float,
        verbose: int = None
    ) -> Callable:
        """
        Create a closure function that is needed by the optimizer.
        :param input_img: image to be fitted.
        :param optimizer: optimizer to use.
        :param content_weight: content loss weight.
        :param style_weight: style loss weight.
        :param verbose: frequency (in iterations) to display performance metrics.
        :return: closure function.
        """
        def closure_fn() -> torch.Tensor:
            with torch.no_grad():
                input_img.clamp_(0, 1)

            optimizer.zero_grad()
            self.model(input_img)

            self._content_loss = content_weight * sum(map(lambda x: x.loss, self.model.content_losses))
            self._style_loss = style_weight * sum(map(lambda x: x.loss, self.model.style_losses))

            loss = self._content_loss + self._style_loss
            loss.backward()

            if verbose and self._counter % verbose == 0:
                self._print_metrics()
            self._counter += 1

            return loss

        return closure_fn

    def _print_metrics(self) -> None:
        """
        Show current performance metrics.
        """
        print("Epoch: {}".format(self._counter))
        print("Content Loss: {:.2f}, Style Loss: {:.2f}".format(
            self._content_loss.item(), self._style_loss.item()
        ))
        print("Time: {}".format(datetime.now().strftime("%H:%M:%S")))
        print("*" * 100)
