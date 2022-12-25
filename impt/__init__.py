# impt autodiff pipline
# flake8: noqa
from .__version__ import __version__
from .perturb import *
from . import fpfs

# We need accuracy is below 1e-6
from jax import config

config.update("jax_enable_x64", True)

__all__ = ["fpfs"]
__all__ += perturb.__all__
