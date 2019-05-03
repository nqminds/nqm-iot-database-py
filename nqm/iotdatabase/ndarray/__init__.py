"""Module for loading/storing n-dimensional arrays."""
import typing
import json

import numpy as np # used for typing only

from .ndarray import NDArray
from .fileio import (
    saveNDArray, getNDArray, deleteNDArray
)

#TODO: Rename to match PEP8?
#pylint: disable=locally-disabled, invalid-name

def saveToPureJSON(array: np.array) -> typing.Text:
    """Saves a numpy ndarray as a pure JSON string.

    Args:
        array: The numpy array that should be a compressed JSON.

    Returns:
        A JSON string that can be loaded with `loadFromPureJSON`.
    """
    return saveNDArray(array, storage_method="G").tojson()

def loadFromPureJSON(jsonstr: typing.Text) -> np.array:
    """Loads a numpy ndarray from a pure JSON string.

    Args:
        jsonstr: The JSON string returned by `saveToPureJSON`.

    Returns:
        The loaded numpy array.
    """
    return getNDArray(NDArray(**json.loads(jsonstr)))
