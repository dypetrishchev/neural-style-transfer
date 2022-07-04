"""Module provides helper functions."""

import yaml


def load_config(path: str) -> dict:
    """
    Load a config from a yaml file.
    :param path: path to a config file.
    :return: loaded config.
    """
    with open(path) as f:
        config = yaml.safe_load(f)
    return config
