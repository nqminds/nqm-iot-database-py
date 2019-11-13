"""Stores functions about storing ndarrays in dbs.
"""
import typing as ty
from os import PathLike
import numpy as np # only for typing

from .ndarray import NDArray
from .storageformats import STORAGE_TYPES

Path = ty.Union[PathLike, ty.Text]

#TODO: Rename to match PEP8?
#pylint: disable=locally-disabled, invalid-name

def saveNDArray(
        array: np.ndarray,
        relative_loc: Path = "",
        storage_method: ty.Text = "",
) -> NDArray:
    """Saves an array.

    Args:
        array: The numpy ndarray to save.
        relative_loc: Relative location of any filepaths.
        storage_method: Pick the storage version to use.
            default is pick automatically.

    Returns:
        The metadata of the saved numpy array.
    """
    storage_class = None
    if not storage_method:
        storage_method = "f"
    try:
        storage_class = STORAGE_TYPES[storage_method]
    except:
        raise NotImplementedError(
            f"Loading NDArray with version {storage_method} failed!"
            f"Only versions {STORAGE_TYPES.keys()} are supported.")
    return storage_class.save(array, relative_loc)

def getNDArray(
        metadata: NDArray,
        relative_loc: Path = ""
) -> np.ndarray:
    """Opens an NDArray object as a numpy array

    Args:
        metadata: The object containing the array metadata.
        relative_loc: Relative location of any filepaths.

    Returns:
        A numpy array.
    """
    storage_class = None
    try:
        storage_class = STORAGE_TYPES[metadata.v]
    except:
        raise NotImplementedError(
            f"Loading NDArray with version {metadata.v} failed!"
            f"Only versions {STORAGE_TYPES.keys()} are supported.")
    return storage_class.get(metadata, relative_loc)

def deleteNDArray(metadata: NDArray, relative_loc: Path = "") -> None:
    """Deletes the given NDArray.

    Args:
        metadata: The object containing the array metadata.
        relative_loc: Relative location of any filepaths.
    """
    storage_class = None
    try:
        storage_class = STORAGE_TYPES[metadata.v]
    except:
        raise NotImplementedError(
            f"Deleting NDArray with version {metadata.v} failed!"
            f"Only versions {STORAGE_TYPES.keys()} are supported.")
    storage_class.delete(metadata, relative_loc)
