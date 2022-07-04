"""
In this example the algorithm takes three images (content, style, input)
and changes the input to resemble the content of the content-image and the artistic style of the style-image.
"""

from os.path import dirname, join

import torch
import torchvision.models as models

from src.models import NeuralAlgorithmModel
from src.trainers import Trainer
from src.utils.images import load_image_from_file, plot_examples

if __name__ == "__main__":
    img_size = [512, 512] if torch.cuda.is_available() else [256, 256]
    style_img = load_image_from_file(join(dirname(__file__), "images", "picasso.jpeg"), img_size)
    content_img = load_image_from_file(join(dirname(__file__), "images", "dancing.jpeg"), img_size)

    backbone_model = models.vgg19(pretrained=True).features.eval()
    model = NeuralAlgorithmModel(backbone_model, content_img, style_img, [4], [1, 2, 3, 4, 5])
    trainer = Trainer(model)

    input_img = content_img.clone()
    fitted_img = trainer.fit(input_img, max_iter=300, verbose=50)

    fig, axes = plot_examples([content_img, style_img, fitted_img[None]], ["Content", "Style", "Output"])
    fig.savefig(join(dirname(__file__), "images", "output.png"), dpi=120)
