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

# This is only a simple example of shear estimator
# You can define your own observable function


import jax.numpy as jnp
from .observable import Observable
from .utils import tsfunc2


class FPFSDistort(Observable):
    """A class for FPFS observables, which implements perturbation response of
    polar shapelet modes introduced in
    https://arxiv.org/abs/astro-ph/0408445
    [see eq. (37) to eq. (42)],
    and FPFS peak modes intriduced in
    https://arxiv.org/abs/1805.08514
    These shear responses are to construct shear estimator.
    """

    def __init__(self, meta2):
        super(FPFSDistort, self).__init__()
        self.meta2 = meta2
        return

    def _dm_dg1(self, x, basis_name):
        if basis_name == "fpfs_M00":
            out = -jnp.sqrt(2.0) * x[self.aind("fpfs_M22c")]
        elif basis_name == "fpfs_M20":
            out = -jnp.sqrt(6.0) * x[self.aind("fpfs_M42c")]
        elif basis_name == "fpfs_M22c":
            out = (x[self.aind("fpfs_M00")] - x[self.aind("fpfs_M40")]) / jnp.sqrt(2.0)
        elif basis_name == "fpfs_M22s":
            # TODO: Neglect spin-4 term. Need to add it when we have M44
            out = 0.0
        elif basis_name == "fpfs_M40":
            # NOTE: Incldue the shear response of M40 in the future. This is not
            # required in the FPFS shear estimation (v1~v3), so I set it to zero
            # here (But if you are interested in playing with shear response of
            # this term, please contact me.)
            out = 0.0
        else:
            out = 0.0
        return out

    def _dm_dg2(self, x, basis_name):
        if basis_name == "fpfs_M00":
            out = -jnp.sqrt(2.0) * x[self.aind("fpfs_M22s")]
        elif basis_name == "fpfs_M20":
            out = -jnp.sqrt(6.0) * x[self.aind("fpfs_M42s")]
        elif basis_name == "fpfs_M22c":
            # TODO: Neglect spin-4 term. Need to add it when we have M44
            out = 0.0
        elif basis_name == "fpfs_M22s":
            out = (x[self.aind("fpfs_M00")] - x[self.aind("fpfs_M40")]) / jnp.sqrt(2.0)
        elif basis_name == "fpfs_M40":
            # NOTE: Incldue the shear response of M40 in the future. This is not
            # required in the FPFS shear estimation (v1~v3), so I set it to zero
            # here (But if you are interested in playing with shear response of
            # this term, please contact me.)
            out = 0.0
        else:
            out = 0.0
        return out

    def dm_dg(self, data, g_comp):
        """Returns shear response of shapelet basis

        Args:
            data (ndarray):     multi-row array
            g_comp (int):       the component of shear [1 or 2]
        Returns:
            out (ndarray):      shear responses for the shapelet bases
        """
        if g_comp == 1:

            def _func_(x, basis_name):
                return jnp.apply_along_axis(
                    func1d=self._dm_dg1,
                    axis=-1,
                    arr=x,
                    basis_name=basis_name,
                )

        elif g_comp == 2:

            def _func_(x, basis_name):
                return jnp.apply_along_axis(
                    func1d=self._dm_dg2,
                    axis=-1,
                    arr=x,
                    basis_name=basis_name,
                )

        else:
            raise ValueError("g_comp can only be 1 or 2")
        out = jnp.array(
            [_func_(x=data, basis_name=nm) for nm in self.meta2["modes_tmp"]]
        ).T
        return out

    def make_child(self):
        # TODO: This need to be improved
        return self


class WeightedE1(Observable):
    """A class for FPFS ellipticity [the first component] introduced by
    https://arxiv.org/abs/1805.08514
    We take the form of eq. (36) in
    https://arxiv.org/abs/2208.10522
    """

    def __init__(self, wconst):
        """Initializer of FPFS weighted e1

        Args:
            wconst (float):  FPFS weighting parameter
        """
        super(WeightedE1, self).__init__(wconst=wconst)
        self.umode_names = None
        self.meta["modes"] = [
            "fpfs_M22c",
            "fpfs_M00",
        ]
        # NOTE: XL: I manually put dmode_names, which I know is not clever;
        # Will make a dictionary for that
        self.meta["modes_child"] = [
            "fpfs_M22c",
            "fpfs_M00",
            "fpfs_M40",
        ]
        self.distort = FPFSDistort(self.meta2)
        return

    def _base_func(self, x):
        out = x[self.aind("fpfs_M22c")] / (
            x[self.aind("fpfs_M00")] + self.meta["wconst"]
        )
        return out


class WeightedE2(Observable):
    """A class for FPFS ellipticity [the second component] introduced by
    https://arxiv.org/abs/1805.08514
    We take the form of eq. (36) in
    https://arxiv.org/abs/2208.10522
    """

    def __init__(self, wconst):
        """Initializer of FPFS weighted e1

        Args:
            wconst (float):  FPFS weighting parameter
        """
        super(WeightedE2, self).__init__(wconst=wconst)
        self.meta["modes"] = [
            "fpfs_M22s",
            "fpfs_M00",
        ]
        # NOTE: XL: I manually put dmode_names, which I know is not clever;
        # Will make a dictionary for that
        self.meta["modes_child"] = [
            "fpfs_M22s",
            "fpfs_M00",
            "fpfs_M40",
        ]
        self.distort = FPFSDistort(self.meta2)
        return

    def _base_func(self, x):
        out = x[self.aind("fpfs_M22s")] / (
            x[self.aind("fpfs_M00")] + self.meta["wconst"]
        )
        return out


class SelectWeight(Observable):
    """A class for FPFS selection weight introduced by
    https://arxiv.org/abs/2208.10522
    """

    def __init__(self, mu0, sigma0, mu2, sigma2):
        """Initializer of FPFS selection weight [flux=0, size=2]

        Args:
            mu (float):     Center of the cut
            sigma (float):  Smoothness parameter of the cut
        """
        super(SelectWeight, self).__init__(
            mu0=mu0,
            sigma0=sigma0,
            mu2=mu2,
            sigma2=sigma2,
        )
        self.meta["modes"] = [
            "fpfs_M00",
            "fpfs_M20",
        ]
        # NOTE: XL: I manually put dmode_names, which I know is not clever;
        # Will make a dictionary for that
        self.meta["modes_child"] = [
            "fpfs_M22c",
            "fpfs_M22s",
            "fpfs_M42c",
            "fpfs_M42s",
        ]
        self.distort = FPFSDistort(self.meta2)
        return

    def _base_func(self, x):
        w0 = tsfunc2(
            x[self.aind("fpfs_M00")],
            mu=self.meta["mu0"],
            sigma=self.meta["sigma0"],
        )
        w2 = tsfunc2(
            x[self.aind("fpfs_M20")],
            mu=self.meta["mu2"],
            sigma=self.meta["sigma2"],
        )
        return w0 * w2


# class PeakWeight(Observable):
#     def __init__(self, **kwargs):
#         super(peak_weight, self).__init__()
#         return

#     def _base_func(self, x):
#         pass
