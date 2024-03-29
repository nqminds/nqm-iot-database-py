"""Stores the NDArray array class, that contains NDArray metadata.

This can be used to store an NDArray as a JSON object.
"""
import typing as ty
import json
import numpy as np # only used for typing

np_type_to_single_char: ty.Dict[ty.Text, np.dtype] = {
    v: c for c, v in np.sctypeDict.items()
    if isinstance(c, str) and len(c) == 1
}
"""Dict of single-chars to numpy types, ie p is an int64, P uint64"""

VARLENGTH_TYPE_CHARS = {"O", "U", "V"}
"""Set of Numpy types that require a length to be specified"""

def basictypestring(
        dtype_char: ty.Text,
        length: int = -1,
        byteorder: ty.Text = "="
    ) -> ty.Text:
    """Creates a compressed typestring from a given Numpy type details.

    Arguments:
        dtype_char: A single char from Numpy. See `numpy.dtype.char`.
        length: The length of the dtype in bytes. See `numpy.dtype.itemsize`
        byteorder:
            The byte order, ie little/big-endian. See `numpy.dtype.byteorder`

    Returns:
        A numpy typestring that is as compressed as possible.
    """
    # only specify length if we have a variable width type
    lengthstr = str(length) if dtype_char in VARLENGTH_TYPE_CHARS else ""
    # only specify byte order if we need to
    byteorderchar = byteorder if byteorder not in ("=", "|") else ""
    return f"{byteorderchar}{dtype_char}{lengthstr}"

# Create a generic variable that can be 'NDArray', or any subclass.
T = ty.TypeVar('T', bound="NDArray")
class NDArray():
    """The metadata of an NDArray.

    Example:
        >>> from nqm.iotdatabase.ndarray import NDArray
        >>> arr = NDArray(
        ...     # numpy typestring, h means signed 16-bit int and = means native align
        ...     t = "=h",
        ...     s = (766, 480), # shape of array, means 766 x 480 (2d)
        ...     # metadata version, f means p is a pointer to uncompressed binary file
        ...     v = "f",
        ...     # True if in C-order (row-major), else in F-order (column-major)
        ...     c = True,
        ...     # filename can be anything, but currently it is being generated by
        ...     #    vvvvvvvvvvvv - base64 unix timestamp in ms
        ...     #                  this means files are in alphabet chronological order
        ...     #                vvvvvvvv - pseudorandom prefix to avoid clashes
        ...     #                           if there is the same timestamp
        ...     #                        vvvv - static suffux
        ...     p = "AAABaBQNuQI=s8ffou_6.dat",
        ... )

    """
    t: ty.Text
    """typestr, basic string format is endian, type, byte size.
        ie ``>i8`` is an 8-bit signed big-endian int. See
        https://docs.scipy.org/doc/devdocs/reference/arrays.interface.html#typestr"""
    s: ty.Tuple[int, ...] = tuple()
    """the shape of the array, a :any:`list` of dimensions,
    ie ``[10, 10]`` for a 10 by 10 array."""
    v: ty.Text
    "the version of this NDArray, ``f`` means that :attr:`p` is a filepath."
    p: ty.Text
    """the pointer to the data.
    This changes depending on the value of the version, :attr:`v`."""
    c: bool
    """``True`` if using C-type column ordering (row-major),
        ``False`` if using Fortran ordering"""

    @classmethod
    def from_array(
        cls: ty.Type[T], array: np.ndarray, pointer: ty.Text, version: ty.Text,
    ) -> T:
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

    #pylint: disable=locally-disabled, too-many-arguments
    def __init__(
            self,
            t: ty.Text = "V", # void data type
            s: ty.Tuple[int, ...] = tuple(), # no dimensions
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
        #pylint: disable=locally-disabled, multiple-statements, invalid-name
        m = self
        m.t = t; m.s = s; m.v = v; m.p = p; m.c = c

    def todict(self) -> dict:
        """Returns this object as a dict"""
        return_dict = {"t": self.t, "s": self.s, "v": self.v, "p": self.p}
        if not self.c:
            return_dict["c"] = self.c
        return return_dict

    def tojson(self) -> ty.Text:
        """Returns this object as a json"""
        return json.dumps(self.todict())

    @classmethod
    def fromjson(cls, jsonstr: ty.Text) -> "NDArray":
        """Creates an NDArray object from a json."""
        return cls(**json.loads(jsonstr))
