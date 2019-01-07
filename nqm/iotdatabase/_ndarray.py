"""Stores functions about storing ndarrays in dbs.
"""
import typing as ty
import numpy as np
import os
import tempfile
import time
import base64
import json

np_type_to_single_char: ty.Dict[ty.Text, np.dtype] = {
    v: c for c, v in np.sctypeDict.items() 
    if isinstance(c, str) and len(c) == 1
}
"""Dict of single-chars to numpy types, ie p is an int64, P uint64"""

varlength_types = {"O", "U", "V"}

def basictypestring(
    charBuiltinType: ty.Text,
    length: int = -1,
    byteorder: ty.Text = "="
) -> ty.Text:
    # only specify length if we have a variable width type
    l = str(length) if charBuiltinType in varlength_types else ""
    # only specify byte order if we need to
    b = byteorder if byteorder != "=" and byteorder != "|" else ""
    return f"{b}{charBuiltinType}{l}"

class NDArray(object):
    """The metadata of an NDArray

    Attributes:
        t: typestr, basic string format is endian, type, byte size.
            ie ``>i8`` is an 8-bit signed big-endian int
        See https://docs.scipy.org/doc/devdocs/reference/arrays.interface.html#typestr
        s: the shape of the array
        v: the version of this NDArray
        p: the pointer to the location of the data. Usually a filepath.
        c: True if using C-type column ordering
    """
    t: ty.Text
    s: ty.Iterable[int] = tuple()
    v: ty.Text
    p: ty.Text
    c: bool

    @classmethod
    def from_array(cls, array: np.ndarray, pointer: ty.Text, version: ty.Text):
        """Creates an NDArray fron a numpy array.

        Args:
            array: The numpy array with correct metadata.
            pointer: A pointer to the data.
            version:
                The version of the metadata.
                "f" means the pointer is a filepath to a raw binary blob.
        
        Returns:
            The created NDArray metadata object.
        """
        c_order = array.flags.c_contiguous
        dtype = array.dtype
        typestr = basictypestring(dtype.char, dtype.itemsize, dtype.byteorder)
        return cls(t=typestr, s=array.shape, v=version, p=pointer, c=c_order)

    def __init__(self,
        t: ty.Text = "V", # void data type
        s: ty.Iterable[int] = tuple(), # no dimensions
        v: ty.Text = "", # assume no version
        p: ty.Text = "", # assume no pointer
        c: bool = True, # column order, True for c-type column ordering
    ):
        """Constructs a new NDArray object
        
        Args:
            t: typestr, basic string format is endian, type, byte size.
                ie ``>i8`` is an 8-bit signed big-endian int
                See https://docs.scipy.org/doc/devdocs/reference/arrays.interface.html#typestr
            s: the shape of the array
            v: the version of this NDArray
            p: the pointer to the location of the data. Usually a filepath.
            c: True if using C-type column ordering
        """
        m = self
        m.t = t; m.s = s; m.v = v; m.p = p; m.c = c

    def todict(self) -> dict:
        return_dict = {"t": self.t, "s": self.s, "v": self.v, "p": self.p}
        if not self.c: return_dict["c"] = self.c
        return return_dict

    def tojson(self) -> ty.Text:
        return json.dumps(self.todict())

def makePrefix():
    unix_time_ms = int(time.time() * 1000)
    unix_bytes = unix_time_ms.to_bytes(8, byteorder="big")
    return base64.urlsafe_b64encode(unix_bytes).decode("ascii")

def saveNDArray(array: np.ndarray, filepath = "", relative_loc = ""):
    open_file = None
    if filepath:
        path = os.path.join(relative_loc, filepath)
        open_file = open(path, "wb")
    else: # make pseudo-random filename
        open_file = tempfile.NamedTemporaryFile(
            delete=False, # do not delete automatically
            dir=relative_loc,
            prefix=str(makePrefix()),
            suffix=".dat")

    with open_file as datafile:
        datafile.write(array.tobytes(None))
    return NDArray.from_array(array, pointer=open_file.name, version="f")

supportedVersions = {"f"}
"""Stores the supported versions for loading a file"""

def getNDArray(metadata: NDArray, relative_loc="") -> np.ndarray:
    """Opens an NDArray object as a numpy array

    Args:
        metadata: The object containing the array metadata.
        relative_loc: Relative location of any filepaths.
    
    Returns:
        A copy-on-write numpy array loaded for the metadata.
    """
    md = metadata
    if md.v not in supportedVersions:
        raise NotImplementedError(
            f"Loading NDArray with version {md.v} failed!"
            f"Only versions {supportedVersions} are supported.")
    dtype = np.dtype(md.t)
    order = "C" if md.c else "F"
    path = os.path.join(relative_loc, md.p)
    return np.memmap( # mode="c" is copy-on-write, changes are made in RAM copy
        filename = path, dtype=dtype, mode="c", shape=md.s, order=order)

def deleteNDArray(metadata: NDArray, relative_loc=""):
    """Deletes the given NDArray.

    Args:
        metadata: The object containing the array metadata.
        relative_loc: Relative location of any filepaths.
    """
    md = metadata
    if md.v not in supportedVersions:
        raise NotImplementedError(
            f"Deleting NDArray with version {md.v} failed!"
            f"Only versions {supportedVersions} are supported.")
    path = os.path.join(relative_loc, md.p)
    os.unlink(md.p)
