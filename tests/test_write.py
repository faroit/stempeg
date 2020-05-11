import stempeg
import numpy as np
import pytest
import tempfile as tmp
import subprocess as sp


@pytest.fixture(params=[1, 2, 4])
def nb_streams(request):
    return request.param


@pytest.fixture(params=[1, 2])
def nb_channels(request):
    return request.param


@pytest.fixture(params=[4096, 4096*10])
def nb_samples(request):
    return request.param


@pytest.fixture
def audio(request, nb_streams, nb_samples, nb_channels):
    return np.random.random((nb_streams, nb_samples, nb_channels))


@pytest.fixture(params=["mp4", "mka"])
def multistream_format(request):
    return request.param


@pytest.fixture(params=["mp4", "mka", "wav", "flac"])
def multichannel_format(request):
    return request.param


@pytest.fixture(params=["mp3", "mp4", "mka", "wav", "flac"])
def multifile_format(request):
    return request.param


def test_multistream_containers(audio, multistream_format, nb_streams):
    if nb_streams > 1:
        with tmp.NamedTemporaryFile(
            delete=False,
            suffix='.' + multistream_format
        ) as tempfile:
            stream_names = [str(k) for k in range(nb_streams)]
            stempeg.write_stems(
                tempfile.name,
                audio,
                sample_rate=44100,
                stream_names=stream_names
            )
            loaded_audio, rate = stempeg.read_stems(tempfile.name, always_3d=True)
            assert audio.shape == loaded_audio.shape
            if multistream_format == "mp4":
                info = stempeg.Info(tempfile.name)
                loaded_stream_names = info.title_streams
                # check if titles could be extracted
                assert all(
                    [a == b for a, b in zip(stream_names, loaded_stream_names)]
                )


def test_multichannel_containers(audio, nb_channels, multichannel_format):
    with tmp.NamedTemporaryFile(
        delete=False,
        suffix='.' + multichannel_format
    ) as tempfile:
        stempeg.write_stems(
            tempfile.name,
            audio,
            sample_rate=44100,
            stems_as_channels=nb_channels
        )
        loaded_audio, rate = stempeg.read_stems(
            tempfile.name,
            always_3d=True,
            stems_from_channels=nb_channels
        )
        assert audio.shape == loaded_audio.shape


def test_multifileformats(audio, multifile_format):
    with tmp.NamedTemporaryFile(
        delete=False,
        suffix='.' + multifile_format
    ) as tempfile:
        stempeg.write_stems(
            tempfile.name,
            audio,
            sample_rate=44100,
            stems_as_files=True
        )
        # TODO: implement multiple reads


def test_channels(audio, multichannel_format):
    if audio.ndim == 1:
        with tmp.NamedTemporaryFile(
            delete=False,
            suffix='.' + multichannel_format
        ) as tempfile:
            stempeg.write_audio(tempfile.name, audio, sample_rate=44100)
            loaded_audio, rate = stempeg.read_stems(
                tempfile.name,
            )
            assert audio.shape == loaded_audio.shape


def test_stereo(audio, multifile_format):
    if audio.ndim == 2:
        with tmp.NamedTemporaryFile(
            delete=False,
            suffix='.' + multifile_format
        ) as tempfile:
            stempeg.write_audio(tempfile.name, audio, sample_rate=44100)
            loaded_audio, rate = stempeg.read_stems(
                tempfile.name,
                always_3d=True,
            )
            assert audio.shape == loaded_audio.shape


# def test_ffmpeg_errors(audio):
#     if audio.ndim == 3:
#         # write multistream as wav
#         with pytest.raises(RuntimeError):
#             with tmp.NamedTemporaryFile(
#                 delete=False,
#                 suffix='.wav'
#             ) as tempfile:
#                 stempeg.write_audio(tempfile.name, audio, sample_rate=44100)
