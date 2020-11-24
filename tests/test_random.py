import stempeg
import numpy as np
import pytest


@pytest.fixture(params=[1024, 2048, 12313, 100000])
def nb_samples(request):
    return request.param


def test_shape(nb_samples):
    R = np.random.random((5, nb_samples, 2))
    stempeg.write_stems("./random.stem.m4a", R, writer=stempeg.StreamsWriter())
    S, rate = stempeg.read_stems(
        "./random.stem.m4a"
    )

    assert S.shape[0] == R.shape[0]
    assert S.shape[2] == R.shape[2]
    assert S.shape[1] % 1024 == 0
