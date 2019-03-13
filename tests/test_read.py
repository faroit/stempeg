import stempeg
import numpy as np
import pytest


@pytest.fixture(params=[np.float16, np.float32, np.float64])
def dtype(request):
    return request.param


@pytest.fixture(params=[None, 0, 1, 2, 100])
def start(request):
    return request.param


@pytest.fixture(params=[None, 0.5, 1, 2])
def duration(request):
    return request.param


def test_stem_id():
    S, _ = stempeg.read_stems(stempeg.example_stem_path())
    for k in range(S.shape[0]):
        Sk, _ = stempeg.read_stems(
            stempeg.example_stem_path(),
            stem_id=k
        )
        assert Sk.ndim == 2


def test_shape():
    S, _ = stempeg.read_stems(stempeg.example_stem_path())
    assert S.shape[0] == 5
    assert ((S.shape[1] % 1024) == 0 and S.shape[1] > 200000)
    assert S.shape[2] == 2


def test_duration(start, duration):
    fp = stempeg.example_stem_path()
    info = stempeg.Info(fp)
    if start:
        if start < min(info.duration_streams):
            S, _ = stempeg.read_stems(
                fp,
                start=start,
                duration=duration
            )
    else:
        S, rate = stempeg.read_stems(fp,
            start=start,
            duration=duration
        )
        if duration is not None:
            assert S.shape[1] == duration * rate


def test_outtype(dtype):
    S, rate = stempeg.read_stems(
        stempeg.example_stem_path(),
        out_type=dtype
    )
    assert S.dtype == dtype


def test_info():
    fp = stempeg.example_stem_path()
    info = stempeg.Info(fp)
    S, rate = stempeg.read_stems(fp, info=info)
