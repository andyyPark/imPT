# imPT
[![Python package](https://github.com/mr-superonion/lensPT/actions/workflows/python-package.yml/badge.svg)](https://github.com/mr-superonion/lensPT/actions/workflows/python-package.yml)
[![Documentation Status](https://readthedocs.org/projects/impt/badge/?version=latest)](https://impt.readthedocs.io/en/latest/?badge=latest)

Fast estimator for Lensing Perturbation (`imPT`) from astronomical images
using the auto differentiating function of jax.

A simple code to compute the response to lensing perturbations and remove the
bias due to the perturbation from image noise.


## Installation

For developers:
```shell
git clone https://github.com/mr-superonion/imPT.git
pip install -e . --user
```
before running code, users need to setup the environment by
```shell
source impt_config
```

## Summary
For the first version of `imPT`, we implement `FPFS` and use `imPT` to auto
differentiate `FPFS`.
