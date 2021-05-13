from typing import List, Union, Optional, Dict
import attr
import numpy as np
import math

from . import util


def positive(self, attribute, value):
    if value <= 0:
        raise ValueError(f"{attribute.name} must be greater than zero")


def non_negative(self, attribute, value):
    if value < 0:
        raise ValueError(f"{attribute.name} must be non-negative")


def finite(self, attribute, value):
    if math.isinf(value):
        raise ValueError(f"{attribute.name} must be finite")


def optional(func):
    """
    Wraps one or more validator functions with an "if not None" clause.
    """
    if isinstance(func, (tuple, list)):
        func_list = func
    else:
        func_list = [func]

    def validator(self, attribute, value):
        if value is not None:
            for func in func_list:
                func(self, attribute, value)

    return validator


@attr.s(auto_attribs=True, repr=False)
class Spectrum:
    """
    The deletion spectrum.

    :param data:
    :type data: array-like, optional
    :param sample_size:
    :type sample_size: int, optional
    :param folded:
    :type folded: bool, optional
    """

    data: np.array = attr.ib(default=None)
    sample_size: int = attr.ib(
        default=None, validator=attr.validators.optional([positive, finite]),
    )
    folded: bool = attr.ib(default=False)

    def __attrs_post_init__(self):
        def _get_n_from_length(l):
            return (np.sqrt(1 + 8 * l) - 1) / 2 - 1

        if self.data is None and self.sample_size is None:
            raise ValueError("Either a data array or sample size must be provided")
        if self.data is None:
            self.data = np.zeros((self.sample_size + 1) * (self.sample_size + 2) // 2)

        # ensure data length and sample size match
        sample_size_from_data = _get_n_from_length(len(self.data))
        if not np.isclose(sample_size_from_data, np.rint(sample_size_from_data)):
            raise ValueError("Length of data is not valid")
        sample_size_from_data = np.rint(sample_size_from_data).astype(int)
        if self.sample_size is None:
            self.sample_size = sample_size_from_data
        else:
            if sample_size_from_data != self.sample_size:
                raise ValueError(
                    f"Data does not have valid length for sample size = {self.sample_size}"
                )

    def _as_masked_array(self):
        """
        Represent the deletion frequency spectrum as a masked numpy array.
        """
        data_square = np.zeros((self.sample_size + 1, self.sample_size + 1))
        mask_square = np.full(
            (self.sample_size + 1, self.sample_size + 1), True, dtype=bool
        )
        c = 0
        for i in range(self.sample_size + 1):
            data_square[i, : self.sample_size + 1 - i] = self.data[
                c : c + self.sample_size + 1 - i
            ]
            mask_square[i, : self.sample_size + 1 - i] = False
            c += self.sample_size + 1 - i
        T = np.ma.masked_array(data_square, mask_square, fill_value=0)
        return T

    def __repr__(self):
        T = self._as_masked_array()
        return "DelSpectrum(\n%s,\nsample_size=%s\nfolded=%s)" % (
            str(T),
            str(self.sample_size),
            str(False),
        )

    def __getitem__(self, key):
        return self._as_masked_array()[key]

    def project(self, n_proj):
        if not isinstance(n_proj, int):
            raise ValueError("Projection size must be a positive integer")
        if n_proj == self.sample_size:
            return self
        elif n_proj <= 0:
            raise ValueError("Projection size must be positive")
        elif n_proj > self.sample_size:
            raise ValueError("Projection size must be smaller than current sample size")

        data_proj = util.project(self.data, n_proj)
        return Spectrum(data_proj)
