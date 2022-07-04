"""Module provides useful functions to fit models."""

import sys
from copy import deepcopy
from typing import List

import torch
from torchvision.models import vgg19

from src.models import NeuralAlgorithmModel, create_model
from src.models.test_model import TestModel
from src.options.test_options import TestOptions
from src.trainers import Trainer


def init_trainer(style_img: torch.Tensor, content_img: torch.Tensor) -> Trainer:
    """
    Construct a model instance using backbone model layers and put it into a trainer.
    :param style_img: style-image.
    :param content_img: content-image.
    :return: model trainer.
    """
    backbone_model = vgg19(pretrained=True).features.eval()
    model = NeuralAlgorithmModel(backbone_model, content_img, style_img, [4], [1, 2, 3, 4, 5])
    trainer = Trainer(model)
    return trainer


def fit_image(
    trainer: Trainer,
    input_img: torch.Tensor,
    max_iter: int = 300,
    verbose: int = None
) -> torch.Tensor:
    """
    Change an input image to resemble content of a content-image and artistic style of a style-image.
    :param trainer: model trainer.
    :param input_img: image to be fitted.
    :param max_iter: maximum number of iterations of the optimization algorithm.
    :param verbose: frequency (in iterations) to display performance metrics.
    :return: fitted image.
    """
    fitted_img = trainer.fit(input_img, max_iter=max_iter, verbose=verbose)
    return fitted_img[0]


def get_fitted_image(style_img: torch.Tensor, content_img: torch.Tensor) -> torch.Tensor:
    """
    Change a copy of content-image to resemble artistic style of a style-image
    via the neural transfer algorithm.
    :param style_img: style-image.
    :param content_img: content-image.
    :return: fitted image.
    """
    trainer = init_trainer(style_img, content_img)
    fitted_img = fit_image(trainer, content_img.clone())
    return fitted_img.detach().cpu()


def get_pretrained_gan_model(
    name: str,
    gpu_ids: str = ("0" if torch.cuda.is_available() else "-1"),
    verbose: bool = False
) -> TestModel:
    """
    Initialize a pretrained GAN model.
    :param name: model name.
    :param gpu_ids: GPU indices to use (e.g. "0", "0,1,2,", "0,2"). Use "-1" for CPU.
    :param verbose: whether to print parsed options.
    :return: pretrained GAN model.
    """
    args = deepcopy(sys.argv)

    sys.argv = [
        sys.argv[0],
        # "--checkpoints_dir", join(dirname(dirname(dirname(__file__))), "checkpoints"),
        "--model", "test",
        "--name", name,
        "--preprocess", "none",
        "--gpu_ids", gpu_ids,
        "--num_threads", "0",
        "--batch_size", "1",
        "--no_dropout",
    ]

    opt = TestOptions().parse(verbose)
    opt.display_id = -1

    model = create_model(opt)
    model.setup(opt)
    model.eval()

    sys.argv = args

    return model


def get_pretrained_gan_models(
    names: List[str] = None,
    gpu_ids: str = ("0" if torch.cuda.is_available() else "-1"),
    verbose: bool = False
) -> dict:
    """
    Initialize pretrained GAN models.
    :param names: model names.
    :param gpu_ids: GPU indices to use (e.g. "0", "0,1,2,", "0,2"). Use "-1" for CPU.
    :param verbose: whether to print parsed options.
    :return: pretrained GAN models.
    """
    if not names:
        names = ["style_monet", "style_cezanne", "style_ukiyoe", "style_vangogh"]
    models = {name: get_pretrained_gan_model("{}_pretrained".format(name), gpu_ids, verbose) for name in names}
    return models


def get_inferred_image(model: TestModel, content_image: torch.Tensor) -> torch.Tensor:
    """
    Change a copy of content-image to resemble a predefined artistic style
    via the given GAN model.
    :param model: GAN model to use.
    :param content_image: content-images.
    :return: inferred image.
    """
    data = {"A": ((content_image - 0.5) / 0.5).to(model.device), "A_paths": None}
    model.set_input(data)
    model.test()
    inferred_image = model.get_current_visuals()["fake"].detach().cpu() * 0.5 + 0.5
    return inferred_image[0]
