import stempeg
import pytest
import numpy as np


@pytest.fixture(params=[1024, 2048, 12313, 100000])
def nb_samples(request):
    return request.param


@pytest.fixture(params=[1, 2, 3])
def nb_channels(request):
    return request.param


@pytest.fixture(params=[2, 3, 4])
def nb_stems(request):
    return request.param


@pytest.fixture
def S(nb_stems, nb_samples, nb_channels):
    return np.random.random((nb_stems, nb_samples, nb_channels))


def test_random_write(S, nb_channels, nb_stems, nb_samples):
    stempeg.write_stems(S, "./stems.m4a")
    info = stempeg.Info("./stems.m4a")
    assert info.nb_audio_streams == nb_stems
    assert info.channels(0) == nb_channels


def test_write():
    S, rate = stempeg.read_stems(stempeg.example_stem_path())
    stempeg.write_stems(S, "./stems.mp4")
