"""Stores functions about storing ndarrays in dbs.
"""
import typing as ty
import numpy as np # only for typing

from nqm.iotdatabase._ndarray import NDArray
from nqm.iotdatabase._ndarray.storageformats import storage_types

def saveNDArray(
    array: np.ndarray,
    relative_loc="",
    storage_method="",
):
    """Saves an array.

    Args:
        array: The numpy ndarray to save.
        relative_loc: Relative location of any filepaths.
        storage_method: Pick the storage version to use.
            default is pick automatically.
    """
    storage_class = None
    if not storage_method:
        storage_method = "f"
    try:
        storage_class = storage_types[storage_method]
    except:
        raise NotImplementedError(
            f"Loading NDArray with version {storage_method} failed!"
            f"Only versions {storage_types.keys()} are supported.")
    return storage_class.save(array,relative_loc)

def getNDArray(metadata: NDArray, relative_loc="") -> np.ndarray:
    """Opens an NDArray object as a numpy array

    Args:
        metadata: The object containing the array metadata.
        relative_loc: Relative location of any filepaths.
    
    Returns:
        A numpy array.
    """
    storage_class = None
    try:
        storage_class = storage_types[metadata.v]
    except:
        raise NotImplementedError(
            f"Loading NDArray with version {metadata.v} failed!"
            f"Only versions {storage_types.keys()} are supported.")
    return storage_class.get(metadata,relative_loc)

def deleteNDArray(metadata: NDArray, relative_loc=""):
    """Deletes the given NDArray.

    Args:
        metadata: The object containing the array metadata.
        relative_loc: Relative location of any filepaths.
    """
    storage_class = None
    try:
        storage_class = storage_types[metadata.v]
    except:
        raise NotImplementedError(
            f"Deleting NDArray with version {metadata.v} failed!"
            f"Only versions {storage_types.keys()} are supported.")
    return storage_class.delete(metadata, relative_loc)
