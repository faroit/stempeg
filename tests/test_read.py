import stempeg
import numpy as np
import pytest


@pytest.fixture(params=[np.float16, np.float32, np.float64])
def dtype(request):
    return request.param


def test_stem_id():
    S, rate = stempeg.read_stems(
        "tests/data/The Easton Ellises - Falcon 69.stem.mp4"
    )
    for k in range(S.shape[0]):
        Sk, rate = stempeg.read_stems(
            "tests/data/The Easton Ellises - Falcon 69.stem.mp4",
            stem_id=k
        )
        assert Sk.ndim == 2


def test_shape():
    S, rate = stempeg.read_stems(
        "tests/data/The Easton Ellises - Falcon 69.stem.mp4"
    )
    assert S.shape[0] == 5
    assert ((S.shape[1] % 1024) == 0 and S.shape[1] > 200000)
    assert S.shape[2] == 2


def test_outtype(dtype):
    S, rate = stempeg.read_stems(
        "tests/data/The Easton Ellises - Falcon 69.stem.mp4",
        out_type=dtype
    )
    assert S.dtype == dtype
