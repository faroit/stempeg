import stempeg
import numpy as np
import pytest


@pytest.fixture(params=[np.float16, np.float32, np.float64])
def dtype(request):
    return request.param


@pytest.fixture(params=[None, 0, 0.0000001, 1, 100])
def start(request):
    return request.param


@pytest.fixture(params=[None, 0.00000001, 0.5, 1, 2.00000000000001])
def duration(request):
    return request.param

def test_stem_id():
    S, _ = stempeg.read_stems(stempeg.example_stem_path())
    for k in range(S.shape[0]):
        Sk, _ = stempeg.read_stems(
            stempeg.example_stem_path(),
            stem_id=k
        )
        # test number of channels
        assert Sk.shape[-1] == 2
        # test dim
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
            S, rate = stempeg.read_stems(
                fp,
                start=start,
                duration=duration
            )
            if duration is not None:
                assert S.shape[1] == int(duration * rate)
    else:
        S, rate = stempeg.read_stems(
            fp,
            start=start,
            duration=duration
        )
        if duration is not None:
            assert S.shape[1] == int(duration * rate)


def test_outtype(dtype):
    S, rate = stempeg.read_stems(
        stempeg.example_stem_path(),
        dtype=dtype
    )
    assert S.dtype == dtype


@pytest.mark.parametrize(
    ("format", "path"),
    [
        ("WAV", "http://samples.ffmpeg.org/A-codecs/wavpcm/madbear.wav"),
        pytest.param(
            "MP3", "http://samples.ffmpeg.org/A-codecs/MP3/Enrique.mp3",
            marks=pytest.mark.xfail
        ),
        pytest.param(
            "AAC", "http://samples.ffmpeg.org/A-codecs/AAC/ct_nero-heaac.mp4",
            marks=pytest.mark.xfail
        ),
        pytest.param(
            "OGG", "http://samples.ffmpeg.org/A-codecs/vorbis/ffvorbis_crash.ogm",
            marks=pytest.mark.xfail
        ),
    ],
)
def test_ffmpeg_format(format, path):
    Sint, _ = stempeg.read_stems(
        path,
        dtype=np.float32,
        ffmpeg_format="s16le"
    )

    Sfloat, _ = stempeg.read_stems(
        path,
        dtype=np.float32,
        ffmpeg_format="f32le"
    )
    assert np.allclose(Sint, Sfloat)


def test_info():
    fp = stempeg.example_stem_path()
    info = stempeg.Info(fp)
    S, rate = stempeg.read_stems(fp, info=info)
