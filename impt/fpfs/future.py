# impt autodiff pipline
# Copyright 20221222 Xiangchong Li.
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

# This file contains modules for nonlinear observables measured from images
# from jax import jit
# from functools import partial

import numpy as np
from flax import struct
from .default import npeak

from .default import indexes as did
from ..base import NlBase
from .linobs import FpfsLinResponse
from .utils import tsfunc2, smfunc, ssfunc2, ssfunc3
from ..perturb import BiasNoise, RespG1, RespG2

__all__ = [
    "FpfsExtParams",
    "FpfsExtE1",
    "FpfsExtE2",
]

"""
The following Classes are for FPFS. Feel free to extend the following system
or take it as an example to develop new system
"""
# TODO: Contact me if you are interested in developing a new system of
# Observables


class FpfsExtParams(struct.PyTreeNode):
    """FPFS parameter tree, these parameters are fixed in the tree"""

    # Exting parameter
    C0: float = struct.field(pytree_node=True, default=5.0)
    C2: float = struct.field(pytree_node=True, default=5.0)
    alpha: float = struct.field(pytree_node=True, default=1.3)
    beta: float = struct.field(pytree_node=True, default=1.2)

    # flux selection
    # cut on magntidue
    lower_m00: float = struct.field(pytree_node=False, default=0.2)
    # softening paramter for cut on flux
    sigma_m00: float = struct.field(pytree_node=False, default=0.2)

    # size selection
    # cut on size
    lower_r2: float = struct.field(pytree_node=False, default=0.03)
    upper_r2: float = struct.field(pytree_node=False, default=2.0)
    # softening paramter for cut on size
    sigma_r2: float = struct.field(pytree_node=False, default=0.2)

    # peak selection
    # cut on peak
    lower_v: float = struct.field(pytree_node=False, default=0.005)
    # softening parameter for cut on peak
    sigma_v: float = struct.field(pytree_node=False, default=0.2)


class FpfsObsBase(NlBase):
    def __init__(self, params, parent=None, func_name="ts2"):
        if not isinstance(params, FpfsExtParams):
            raise TypeError("params is not FPFS parameters")
        lin_resp = FpfsLinResponse()
        if func_name == "sm":
            self.ufunc = smfunc
        elif func_name == "ts2":
            self.ufunc = tsfunc2
        elif func_name == "ss2":
            self.ufunc = ssfunc2
        elif func_name == "ss3":
            self.ufunc = ssfunc3
        else:
            raise ValueError("func_name: %s is not supported" % func_name)
        super().__init__(
            params=params,
            parent=parent,
            lin_resp=lin_resp,
        )


class FpfsExtE1(FpfsObsBase):
    """FPFS selection weight"""

    def __init__(self, params, parent=None, skip=1, func_name="ts2"):
        self.nmodes = 31
        self.skip = skip
        super().__init__(
            params=params,
            parent=parent,
            func_name=func_name,
        )

    # @partial(jit, static_argnums=(0,))
    def _base_func(self, cat):
        # selection on flux
        w0 = self.ufunc(cat[did["m00"]], self.params.lower_m00, self.params.sigma_m00)

        # selection on size (lower limit)
        # (M00 + M20) / M00 > lower_r2_lower
        r2l = cat[did["m00"]] * (1.0 - self.params.lower_r2) + cat[did["m20"]]
        w2l = self.ufunc(r2l, self.params.sigma_r2, self.params.sigma_r2)

        # selection on size (upper limit)
        # (M00 + M20) / M00 < upper_r2
        # M00 ( 1 - lower_r2_lower) + M20 > 0
        # r2u = cat[did["m00"]] * (self.params.upper_r2 - 1.0) - cat[did["m20"]]
        # w2u = self.ufunc(r2u, 0.0, self.params.sigma_r2)
        w2u = 1.0
        wsel = w0 * w2l * w2u

        # detection
        wdet = 1.0
        for i in range(0, npeak, self.skip):
            # v_i > lower_v
            wdet = wdet * self.ufunc(
                cat[did["v%d" % i]],
                self.params.lower_v,
                self.params.sigma_v,
            )

        # ellipticity
        denom = (cat[did["m00"]] + self.params.C0) ** self.params.alpha * (
            cat[did["m00"]] + cat[did["m20"]] + self.params.C2
        ) ** self.params.beta
        e1 = cat[did["m22c"]] / denom
        return wdet * wsel * e1


class FpfsExtE2(FpfsObsBase):
    """FPFS selection weight"""

    def __init__(self, params, parent=None, skip=1, func_name="ts2"):
        self.nmodes = 31
        self.skip = skip
        super().__init__(
            params=params,
            parent=parent,
            func_name=func_name,
        )

    # @partial(jit, static_argnums=(0,))
    def _base_func(self, cat):
        # selection on flux
        w0 = self.ufunc(cat[did["m00"]], self.params.lower_m00, self.params.sigma_m00)

        # selection on size (lower limit)
        # (M00 + M20) / M00 > lower_r2_lower
        # M00 ( 1 - lower_r2_lower) + M20 > 0
        r2l = cat[did["m00"]] * (1.0 - self.params.lower_r2) + cat[did["m20"]]
        w2l = self.ufunc(r2l, self.params.sigma_r2, self.params.sigma_r2)

        # selection on size (upper limit)
        # (M00 + M20) / M00 < upper_r2
        # r2u = cat[did["m00"]] * (self.params.upper_r2 - 1.0) - cat[did["m20"]]
        # w2u = self.ufunc(r2u, 0.0, self.params.sigma_r2)
        w2u = 1.0
        wsel = w0 * w2l * w2u

        # detection
        wdet = 1.0
        for i in range(0, npeak, self.skip):
            # v_i > lower_v
            wdet = wdet * self.ufunc(
                cat[did["v%d" % i]],
                self.params.lower_v,
                self.params.sigma_v,
            )

        # ellipticity
        denom = (cat[did["m00"]] + self.params.C0) ** self.params.alpha * (
            cat[did["m00"]] + cat[did["m20"]] + self.params.C2
        ) ** self.params.beta
        e2 = cat[did["m22s"]] / denom
        return wdet * wsel * e2


def prepare_func_e1(
    cov_mat,
    ratio=1.3,
    c0=4.0,
    c2=4.0,
    alpha=0.2,
    beta=0.8,
    snr_min=12,
    r2_min=0.03,
    r2_max=2.0,
):
    std_modes = np.sqrt(np.diagonal(cov_mat))
    std_m00 = std_modes[did["m00"]]
    std_m20 = np.sqrt(
        cov_mat[did["m00"], did["m00"]]
        + cov_mat[did["m20"], did["m20"]]
        + cov_mat[did["m00"], did["m20"]]
        + cov_mat[did["m20"], did["m00"]]
    )
    std_v0 = std_modes[did["v0"]]
    params = FpfsExtParams(
        C0=c0 * std_m00,
        C2=c2 * std_m20,
        alpha=alpha,
        beta=beta,
        lower_m00=snr_min * std_m00,
        lower_r2=r2_min,
        upper_r2=r2_max,
        lower_v=ratio * std_v0 * 0.4,
        sigma_m00=ratio * std_m00,
        sigma_r2=ratio * std_m20,
        sigma_v=ratio * std_v0,
    )
    funcnm = "ss2"
    e1 = FpfsExtE1(params, func_name=funcnm)
    enoise = BiasNoise(e1, cov_mat)
    res1 = RespG1(e1)
    rnoise = BiasNoise(res1, cov_mat)
    return e1, enoise, res1, rnoise


def prepare_func_e2(
    cov_mat,
    ratio=1.3,
    c0=4.0,
    c2=4.0,
    alpha=0.2,
    beta=0.8,
    snr_min=12,
    r2_min=0.03,
    r2_max=2.0,
):
    std_modes = np.sqrt(np.diagonal(cov_mat))
    std_m00 = std_modes[did["m00"]]
    std_m20 = np.sqrt(
        cov_mat[did["m00"], did["m00"]]
        + cov_mat[did["m20"], did["m20"]]
        + cov_mat[did["m00"], did["m20"]]
        + cov_mat[did["m20"], did["m00"]]
    )
    std_v0 = std_modes[did["v0"]]
    params = FpfsExtParams(
        C0=c0 * std_m00,
        C2=c2 * std_m20,
        alpha=alpha,
        beta=beta,
        lower_m00=snr_min * std_m00,
        lower_r2=r2_min,
        upper_r2=r2_max,
        lower_v=ratio * std_v0 * 0.4,
        sigma_m00=ratio * std_m00,
        sigma_r2=ratio * std_m20,
        sigma_v=ratio * std_v0,
    )
    funcnm = "ss2"
    e2 = FpfsExtE2(params, func_name=funcnm)
    enoise = BiasNoise(e2, cov_mat)
    res2 = RespG2(e2)
    rnoise = BiasNoise(res2, cov_mat)
    return e2, enoise, res2, rnoise
