"""Module provides flask views."""

from multiprocessing import Pool

from flask import request, Flask
from flask.views import MethodView

from src.utils.images import get_examples
from src.utils.requests import login, extract_original_images, pack_processed_images
from src.utils.training import get_fitted_image, get_pretrained_gan_models, get_inferred_image


class StyleTransferAPI(MethodView):
    gan_models: dict = get_pretrained_gan_models()
    pool_size: int = 3

    def post(self):
        """
        Receive style and content images, process them and send the result back.
        """
        if request.json:
            if request.json["style"] == "style_custom":
                return self.use_neural_algorithm()
            else:
                return self.use_gan_model()
        return "Request content type must be json."

    def use_neural_algorithm(self) -> dict:
        """
        Transfer a style via the neural style algorithm.
        :return: processed images.
        """
        style_image, content_images = extract_original_images(request.json)
        if len(content_images) == 1:
            fitted_images = [get_fitted_image(style_image, content_images[0])]
        else:
            with Pool(min(len(content_images), self.pool_size)) as p:
                fitted_images = p.starmap(
                    get_fitted_image,
                    ((style_image, content_image) for content_image in content_images)
                )
        return pack_processed_images(fitted_images)

    def use_gan_model(self) -> dict:
        """
        Transfer a style via a GAN model.
        :return: processed images.
        """
        _, content_images = extract_original_images(request.json, with_style=False)
        inferred_images = [
            get_inferred_image(self.gan_models[request.json["style"]], content_image)
            for content_image in content_images
        ]
        return pack_processed_images(inferred_images)


class ExamplesAPI(MethodView):
    examples: dict = get_examples()

    def post(self):
        """
        Send examples of style transfer.
        """
        if request.json:
            return self.examples
        return "Request content type must be json."


def register_views(app: Flask, users: dict) -> None:
    """
    Register flask views.
    :param app: application instance.
    :param users: white list of users.
    """
    app.add_url_rule("/transfer", view_func=login(users)(StyleTransferAPI.as_view("transfer")))
    app.add_url_rule("/examples", view_func=login(users)(ExamplesAPI.as_view("examples")))
