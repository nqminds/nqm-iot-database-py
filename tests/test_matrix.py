import pytest
import nqm.iotdatabase._matrix as _matrix
import numpy as np

types = ["int8", "int64", "uint32", "float", "double"]
@pytest.fixture(params=types)
def dtype(request):
    return request.param

shapes = [[i] * j for i in range(1,3) for j in range(6)]
@pytest.fixture(params=shapes)
def shape(request):
    return request.param

@pytest.fixture(params=(True, False))
def c_order(request):
    return request.param

def test_saving_loading(dtype, shape, c_order, tmp_path):
    a = np.random.random_sample(shape)
    if c_order: a = np.ascontiguousarray(a, np.dtype(dtype))
    else: a = np.asfortranarray(a, np.dtype(dtype))

    filepath = "./test"
    metadata = _matrix.saveNDArray(a, filepath, tmp_path)

    assert np.array_equal(a, _matrix.getNDArray(metadata, tmp_path))
