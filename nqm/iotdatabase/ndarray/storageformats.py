"""Contains different methods of storing an ndarray in a NDArray.

For example:

- "f" means that "p" is a pointer to a uncompressed binary matrix.
- "B" means that "p" is a base64 string of an uncompressed binary matrix.
- "G" means that "G" is a base64 string of a gzipped binary matrix.
"""

import tempfile
import time
import abc
import base64
import gzip
import os

import numpy as np

from nqm.iotdatabase.ndarray import NDArray

def makePrefix():
    unix_time_ms = int(time.time() * 1000)
    unix_bytes = unix_time_ms.to_bytes(8, byteorder="big")
    return base64.urlsafe_b64encode(unix_bytes).decode("ascii")

storage_types = {}
class NDArrayStorage(abc.ABC):
    """Abstract Base Class for classes that save/load NDArrays.
    """
    @classmethod
    @property
    def storage_types(cls):
        return storage_types

    @classmethod
    @abc.abstractmethod
    def get(cls, metadata: NDArray, relative_loc="", **kwargs) -> np.ndarray:
        """Loads the numpy array from the given NDArray.

        Args:
            metadata: The NDArray telling you here the np.ndarray is stored.
            relative_loc: If NDArray contains a relative filepath,
                it is relative to this absolute path.
            **kwargs: Other arguments.

        Returns:
            The loaded numpy array.
        """
        pass

    @classmethod
    @abc.abstractmethod
    def save(cls, array: np.ndarray, relative_loc="", **kwargs) -> NDArray:
        """Saves the numpy array and returns an NDArray.

        Args:
            array: The array to store.
            relative_loc: If NDArray contains a relative filepath,
                it is relative to this absolute path.
            **kwargs: Other arguments.

        Returns:
            The metadata explaining where the ndarray is stored.
        """
        pass

    @classmethod
    @abc.abstractmethod
    def delete(cls, metadata: NDArray, relative_loc="", **kwargs):
        """Deletes the numpy array from the given NDArray.

        Args:
            metadata: The NDArray telling you here the np.ndarray is stored.
            relative_loc: If NDArray contains a relative filepath,
                it is relative to this absolute path.
            **kwargs: Other arguments.
        """
        pass

class FileStorage(NDArrayStorage):
    """Stores the ndarray as a raw binary file"""
    code = "f"
    @classmethod
    def get(cls, metadata: NDArray, relative_loc="") -> np.ndarray:
        md = metadata
        dtype = np.dtype(md.t)
        order = "C" if md.c else "F"
        # relative_loc is the data folder
        # md.p is either the name of the data, or an absolute path
        path = os.path.join(relative_loc, md.p)
        return np.memmap(
            filename=path,
            dtype=dtype,
            mode="c", #  mode="c" is copy-on-write, changes are made in RAM
            shape=tuple(md.s), # we have to make shape a tuple for numpy
            order=order)
    @classmethod
    def save(cls, array: np.ndarray, relative_loc="") -> NDArray:
        # make pseudo-random filename
        open_file = tempfile.NamedTemporaryFile(
            delete=False, # do not delete automatically
            dir=relative_loc,
            prefix=makePrefix(),
            suffix=".dat")

        # pointer is a relative filepath to the binary matrix file
        pointer = os.path.basename(open_file.name)
        with open_file as datafile:
            datafile.write(
                array.tobytes(
                    "C" if array.flags.c_contiguous else "F"))
        return NDArray.from_array(
            array, pointer=open_file.name, version=cls.code)

    @classmethod
    def delete(cls, metadata: NDArray, relative_loc=""):
        md = metadata
        path = os.path.join(relative_loc, md.p)
        os.unlink(md.p)

class Base64Storage(NDArrayStorage):
    """Stores the ndarray as a raw base64 string"""
    code = "B"
    @classmethod
    def get(cls, metadata: NDArray, relative_loc="") -> np.ndarray:
        bin_data = base64.b64decode(metadata.p) # load binary data from b64 str
        array = np.frombuffer(bin_data, dtype=np.dtype(metadata.t))
        if metadata.c:
            array.shape = metadata.s
        else: # binary data is in fortran order
            array.shape = tuple(reversed(metadata.s))
            array = np.transpose(array)
        return array

    @classmethod
    def save(cls, array: np.ndarray, relative_loc="") -> NDArray:
        arrb64 = base64.b64encode( # convert array into a b64 string
            array.tobytes("C" if array.flags.c_contiguous else "F")).decode()
        return NDArray.from_array(array, pointer=arrb64, version=cls.code)

    @classmethod
    def delete(cls, metadata: NDArray, relative_loc=""):
        pass # no need to delete anything since data is stored in the metadata

class GzippedBase64Storage(Base64Storage):
    """Stores the ndarray as a gzipped base64 string"""
    code = "G"
    @classmethod
    def get(cls, metadata: NDArray, relative_loc="") -> np.ndarray:
        # load compressed b64 bytes and uncompress them
        bin_data = gzip.decompress(base64.b64decode(metadata.p))
        array = np.frombuffer(bin_data, dtype=np.dtype(metadata.t))
        if metadata.c:
            array.shape = metadata.s
        else: # binary data is in fortran order
            array.shape = tuple(reversed(metadata.s))
            array = np.transpose(array)
        return array

    @classmethod
    def save(cls, array: np.ndarray, relative_loc="") -> NDArray:
        arrb64 = base64.b64encode( # convert compressed array into a b64 string
            gzip.compress(
                array.tobytes("C" if array.flags.c_contiguous else "F"))
        ).decode()
        return NDArray.from_array(array, pointer=arrb64, version=cls.code)

storage_types[FileStorage.code] = FileStorage
storage_types[Base64Storage.code] = Base64Storage
storage_types[GzippedBase64Storage.code] = GzippedBase64Storage
