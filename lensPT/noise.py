# lensPT autodiff pipline
# Copyright 20221031 Xiangchong Li.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# python lib

import jax.numpy as jnp
from .observable import Observable

__all__ = ["noisePerturb2"]


class noisePerturb2(Observable):
    """A Functional Class to derive the second-order noise perturbation
    function."""

    def __init__(self, obs_obj, noise_cov):
        """Initializes noise bias function object using a obs_obj object and
        a noise covariance matrix
        """
        super(noisePerturb2, self).__init__()
        if not hasattr(obs_obj, "hessian"):
            raise ValueError("obs_fun does not has hessian")
        self.update_obs(obs_obj)
        self.update_noise_cov(noise_cov)
        return

    def update_noise_cov(self, noise_cov):
        """Updates the noise covariance"""
        self.noise_cov = noise_cov
        return

    def update_obs(self, obs_obj):
        """Updates the observable funciton and the noise covariance"""
        self.obs_obj = obs_obj
        self.mode_names = obs_obj.mode_names
        return

    def check_vector(self, x):
        """checks whether a data vector meets the requirements"""
        ndata = x.shape[-1]
        if self.noise_cov.shape != (ndata, ndata):
            raise ValueError(
                "input data should have length %d" % self.noise_cov.shape[0]
            )

    def _base_func(self, x):
        """Returns the second-order noise response"""
        indexes = [[-2, -1], [-2, -1]]
        res = (
            jnp.tensordot(
                self.obs_obj._obs_hessian_func(x),
                self.noise_cov,
                indexes,
            )
            / 2.0
        )
        return res
