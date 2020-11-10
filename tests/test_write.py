from stempeg.write import ChannelsWriter
import stempeg
import numpy as np
import pytest
import tempfile as tmp
import subprocess as sp
import json
import os
import codecs


@pytest.fixture(params=[1, 4])
def nb_stems(request):
    return request.param


@pytest.fixture(params=[1, 2])
def nb_channels(request):
    return request.param


@pytest.fixture(params=[4096, 4096*10])
def nb_samples(request):
    return request.param


@pytest.fixture
def audio(request, nb_stems, nb_samples, nb_channels):
    return np.random.random((nb_stems, nb_samples, nb_channels))


@pytest.fixture(params=["m4a"])
def multistream_format(request):
    return request.param


@pytest.fixture(params=["m4a", "wav", "flac"])
def multichannel_format(request):
    return request.param


@pytest.fixture(params=["mp3", "m4a", "wav", "flac"])
def multifile_format(request):
    return request.param


def test_multistream_containers(audio, multistream_format, nb_stems):
    if nb_stems > 1:
        with tmp.NamedTemporaryFile(
            delete=False,
            suffix='.' + multistream_format
        ) as tempfile:
            stem_names = [str(k) for k in range(nb_stems)]
            stempeg.write_stems(
                tempfile.name,
                audio,
                sample_rate=44100,
                writer=stempeg.StreamsWriter(
                    codec='aac',
                    stem_names=stem_names
                )
            )
            loaded_audio, rate = stempeg.read_stems(
                tempfile.name,
                always_3d=True
            )
            assert audio.shape == loaded_audio.shape
            if multistream_format == "m4a":
                info = stempeg.Info(tempfile.name)
                loaded_stem_names = info.title_streams
                # check if titles could be extracted
                assert all(
                    [a == b for a, b in zip(stem_names, loaded_stem_names)]
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
            writer=ChannelsWriter()
        )
        loaded_audio, rate = stempeg.read_stems(
            tempfile.name,
            always_3d=True,
            reader=stempeg.ChannelsReader(nb_channels=nb_channels)
        )
        assert audio.shape == loaded_audio.shape


def test_multifileformats(audio, multifile_format, nb_stems):
    with tmp.NamedTemporaryFile(
        delete=False,
        suffix='.' + multifile_format
    ) as tempfile:
        stem_names = [str(k) for k in range(nb_stems)]
        stempeg.write_stems(
            tempfile.name,
            audio,
            sample_rate=44100,
            writer=stempeg.FilesWriter(stem_names=stem_names)
        )


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


# write multistream as wav, which doesn't support it
@pytest.mark.xfail
def test_ffmpeg_errors(audio):
    if audio.ndim == 3:
        with pytest.raises(RuntimeError):
            with tmp.NamedTemporaryFile(
                delete=False,
                suffix='.wav'
            ) as tempfile:
                stempeg.write_stems(
                    tempfile.name,
                    audio,
                    sample_rate=44100,
                    writer=stempeg.StreamsWriter()
                )


def ordered(obj):
    if isinstance(obj, dict):
        return sorted((k, ordered(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return sorted(ordered(x) for x in obj)
    else:
        return obj


def test_nistems():
    mp4exc = stempeg.cmds.find_cmd("MP4Box")

    stems, rate = stempeg.read_stems(stempeg.example_stem_path())
    with tmp.NamedTemporaryFile(
        delete=False,
        suffix='.m4a'
    ) as tempfile:

        stempeg.write_stems(
            tempfile.name,
            stems,
            sample_rate=rate,
            writer=stempeg.NIStemsWriter()
        )
        callArgs = [mp4exc]
        callArgs.extend(["-dump-udta", "0:stem", tempfile.name])
        sp.check_call(callArgs)

        root, ext = os.path.splitext(tempfile.name)
        udtaFile = root + "_stem.udta"
        with open(stempeg.default_metadata()) as f:
            d_metadata = json.load(f)

        try:
            fileObj = codecs.open(udtaFile, encoding="utf-8")
            fileObj.seek(8)
            l_metadata = json.load(fileObj)
        except json.decoder.JSONDecodeError:
            with open(udtaFile) as json_file:
                l_metadata = json.load(json_file)

        assert ordered(l_metadata) == ordered(d_metadata)
