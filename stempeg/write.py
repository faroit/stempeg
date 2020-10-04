import base64
import json
import logging
import re
import subprocess as sp
import tempfile as tmp
import warnings
from itertools import chain
from pathlib import Path

import ffmpeg
import numpy as np

import stempeg


def _to_ffmpeg_codec(codec):
    ffmpeg_codecs = {
        'm4a': 'aac',
        'ogg': 'libvorbis',
        'wma': 'wmav2',
    }
    return ffmpeg_codecs.get(codec) or codec


def check_available_aac_encoders():
    """Returns the available AAC encoders

    Returns
    ----------
    codecs : list(str)
        List of available encoder codecs
    """

    cmd = [
        'ffmpeg',
        '-v', 'error',
        '-codecs'
    ]

    output = sp.check_output(cmd)
    aac_codecs = [
        x for x in
        output.splitlines() if "AAC (Advanced Audio Coding)" in str(x)
    ][0]
    hay = aac_codecs.decode('ascii')
    match = re.findall(r'\(encoders: ([^\)]*) \)', hay)
    if match:
        return match[0].split(" ")
    else:
        return None


def write_audio(
    path,
    data,
    sample_rate=44100,
    output_sample_rate=None,
    codec=None,
    bitrate=None
):
    """Write stems from numpy Tensor

    Parameters
    ----------
    path : str
        Output file_name
    data : array_like
        The matrix of audio. The data shape is formatted as
        :code:`samples x channels` or `samples` for single-channel.
    sample_rate : int
        Data samplerate. Defaults to 44100 Hz.
    output_sample_rate : int
        Sample rate of output signal, defaults to `sample_rate`.
        If different to `sample_rate`, signal is resampled.
    bitrate : int
        Bitrate in Bits per second. Defaults to None
    codec : str
        Specifies the codec being used. Defaults to `None` which
        automatically selects default codec for each container
    """

    # check if path is available and creat it
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    if output_sample_rate is None:
        output_sample_rate = sample_rate

    if data.ndim == 1:
        nb_channels = 1
    elif data.ndim == 2:
        nb_channels = data.shape[-1]
    else:
        raise RuntimeError("Number of channels not supported")

    input_kwargs = {'ar': sample_rate, 'ac': nb_channels}
    output_kwargs = {'ar': output_sample_rate, 'strict': '-2'}
    if bitrate:
        output_kwargs['audio_bitrate'] = bitrate
    if codec is not None and codec != 'wav':
        output_kwargs['codec'] = _to_ffmpeg_codec(codec)
    process = (
        ffmpeg
        .input('pipe:', format='f32le', **input_kwargs)
        .output(path, **output_kwargs)
        .overwrite_output()
        .run_async(pipe_stdin=True, pipe_stderr=True, quiet=True))
    try:
        process.stdin.write(data.astype('<f4').tobytes())
        process.stdin.close()
        process.wait()
    except IOError:
        raise Warning(f'FFMPEG error: {process.stderr.read()}')


def build_channel_map(nb_stems, nb_channels, stem_names):
    if nb_channels == 1:
        return (
            [
                '-filter_complex',
                # set merging
                ';'.join(
                    "[a:0]pan=mono| c0=c%d[a%d]" % (
                        idx, idx
                    )
                    for idx in range(nb_stems)
                ),
            ]
        ) + list(
            chain.from_iterable(
                [
                    [
                        '-map',
                        "[a%d]" % idx,
                        # add title tag (e.g. displayed by VLC)
                        "-metadata:s:a:%d" % idx,
                        "title=%s_title" % stem_names[idx],
                        # add handler tag (e.g. read by ffmpeg < 4.1)
                        "-metadata:s:a:%d" % idx,
                        "handler=%s" % stem_names[idx],
                        # add handler tag for ffmpeg >= 4.1
                        "-metadata:s:a:%d" % idx,
                        "handler_name=%s" % stem_names[idx]
                    ]
                    for idx in range(nb_stems)
                ]
            )
        )
    elif nb_channels == 2:
        return (
            [
                '-filter_complex',
                # set merging
                ';'.join(
                    "[a:0]pan=stereo| c0=c%d | c1=c%d[a%d]" % (
                        idx * 2,
                        idx * 2 + 1,
                        idx
                    )
                    for idx in range(nb_stems)
                ),
            ]
        ) + list(
            chain.from_iterable(
                [
                    [
                        '-map',
                        "[a%d]" % idx,
                        # add title tag (e.g. displayed by VLC)
                        "-metadata:s:a:%d" % idx,
                        "title=%s_title" % stem_names[idx],
                        # add handler tag (e.g. read by ffmpeg -i)
                        "-metadata:s:a:%d" % idx,
                        "handler=%s" % stem_names[idx],
                        # add handler tag for ffmpeg >= 4.1
                        "-metadata:s:a:%d" % idx,
                        "handler_name=%s" % stem_names[idx]
                    ]
                    for idx in range(nb_stems)
                ]
            )
        )
    else:
        raise NotImplementedError("not works")


def write_ni_stems(
    path,
    data,
    sample_rate=44100,
    bitrate=256000,
    default_metadata=None,
    stems_metadata=None
):
    """Write stems using native instruments stems format
    
    this is essentially a shortcut to `write_stems` using specific
    defaults and adding additional metadata using mp4box.

    Process is originally created by Native Instrument as shown here:
    https://github.com/axeldelafosse/stemgen/blob/909d9422af0738457303962262f99072a808d0c1/ni-stem/_internal.py#L38

    """
    if data.ndim != 3:
        warnings.warning("Please pass multiple stems", UserWarning)

    if data.shape[2] % 2 != 0:
        warnings.warning("Only stereo stems are supported", UserWarning)

    if data.shape[1] % 1024 != 0:
        logging.warning(
            "Number of samples does not divide by 1024, be aware that "
            "the AAC encoder add silence to the input signal"
        )

    # raise error if checks not passed
    write_stems(
        path,
        data,
        sample_rate=sample_rate,
        output_sample_rate=44100,
        codec="aac",
        bitrate=bitrate,
        ffmpeg_params=None,
        stems_as_channels=False,
        stem_names=stems_metadata.keys()
    )

    # add metadata for traktor
    if default_metadata is not None:
        with open(stempeg.example_stem_path()) as f:
            metadata = json.load(f)
    else:
        metadata = default_metadata

    if stems_metadata is not None:
        metadata['stems'] = stems_metadata
    else:
        nb_stems_metadata = len(metadata["stems"])
        nb_stems = data.shape[0]

        # enumerate tracks and use default colors
        if nb_stems != nb_stems_metadata:
            print("missing stem metadata, using defaults")
            metadata['stems'] = [
                {
                    "name": "".join(
                        [
                            "Stem_", str(i + nb_stems_metadata)
                        ]
                    ),
                    "color": "#000000"
                } for i in range(nb_stems)
            ]

    cmd = (
        [
            'mp4box',
            path,
            "-udta",
            "0:type=stem:src=base64," + str(
                base64.b64encode(json.dumps(metadata).encode())
            )
        ]
    )
    try:
        sp.check_call(cmd)
    except sp.CalledProcessError as err:
        raise RuntimeError(err) from None


def write_stems(
    path,
    data,
    sample_rate=44100,
    output_sample_rate=None,
    codec=None,
    bitrate=None,
    ffmpeg_params=None,
    stems_as_channels=False,
    stems_as_files=False,
    stem_names=None
):
    """Write stems from numpy Tensor

    Parameters
    ----------
    path : str
        Output file_name of the stems file
    data : array_like or dict
        The tensor of Matrix of stems. The data shape is formatted as
            :code:`(stems, samples, channels)`.
        If a dict is provided, we assume:
            :code: `{ "name": array_like of shape (samples, channels), ...}`
    sample_rate : int
        Output samplerate. Defaults to 44100 Hz.
    codec : str
        codec used. Defaults to `None` which automatically selects
        either `libfdk_aac` or `aac` in that order, determined by availability.
        For the best quality, use `libfdk_aac`.
    bitrate : int
        Bitrate in Bits per second. Defaults to `None`
    ffmpeg_params : list(str)
        List of additional ffmpeg parameters
    stems_as_channels : bool
        stems will be saved as multiple channels
        (if multichannel is supported).
    stems_as_files : bool
        stems will be saved as multiple files. Here, the basename(path),
        is ignored and just the parent path + extension is used.
    stem_names : list(str)
        provide a name of each stem, if `data` is array_like
        defaults to enumerated

    Notes
    -----

    The procedure for writing stem files varies depending of the
    specified output container format. There are two basic ways to write
    stems:

    1.) the container supports multiple stems (`mp4/m4a`, `opus`, `mka`)
    2.) the container does not support multiple stems (`wav`, `mp3`, `flac`)

    For 1.) we provide two options:

    1a.) stems will be saved as substreams when
         `stems_as_channels=False` (default)
    1b.) stems will be multiplexed into channels and saved as
        multichannel file.
        E.g. an `audio` tensor of `shape=(stems, samples, 2)`
        will be converted to a single-stem multichannel audio
        `(samples, stems*2)`. This option is activated using
        `stems_as_channels=True`
    1c.) stems will be saved as multiple files when `stems_as_files` is
         active

    For 2.), when the container does not support multiple stems there
    are two options:

    2a) `stems_as_channels` has to be set to `True` (See 1b) otherwise an
        error will be raised. Note that this only works for `wav` and `flac`).
        note that file ending of `path` determines the container (but not the codec!).
    2b) `stems_as_files` so that multiple files will be created when
        stems_as_files` is active.

    """
    if int(stempeg.ffmpeg_version()[0]) < 3:
        warnings.warning(
            "Writing stems with FFMPEG version < 3 is unsupported",
            UserWarning
        )

    if codec == "aac":
        avail = check_available_aac_encoders()
        if avail is not None:
            if 'libfdk_aac' in avail:
                codec = 'libfdk_aac'
            else:
                logging.warning(
                    "For the best quality, use `libfdk_aac` instead of `aac`."
                )
                codec = 'aac'
        else:
            codec = 'aac'

    if output_sample_rate is None:
        output_sample_rate = sample_rate

    if isinstance(data, dict):
        # TODO: what about ordered dicts?
        # alternatively, pass an sort order
        keys = data.keys()
        values = data.values()
        data = np.array(list(values))
        stem_names = list(keys)
    else:
        if stem_names is None:
            stem_names = [str(k) for k in range(data.shape[0])]

    if data.ndim != 3:
        raise RuntimeError("Input tensor dimension should be 3d")

    nb_stems = data.shape[0]
    nb_channels = data.shape[-1]

    # for single stems use `write_audio`
    if nb_stems == 1:
        # remove stem dimension
        data = np.squeeze(data)
        write_audio(
            path=path,
            data=data,
            sample_rate=sample_rate,
            output_sample_rate=output_sample_rate,
            codec=codec,
            bitrate=bitrate
        )
    else:
        if not stems_as_files:
            # swap stem axis
            data = data.transpose(1, 0, 2)
            # aggregate stem and channels
            data = data.reshape(data.shape[0], -1)

        if stems_as_channels:
            # For more than one stem, stems will be reshaped
            # into the channel dimension, always assuming we have
            # stereo channels:
            #     (stems, samples, 2)->(samples, stems*2)
            # this multichannel file will be temporarily
            # saved as wav file
            data = np.squeeze(data)
            write_audio(
                path=path,
                data=data,
                sample_rate=sample_rate,
                output_sample_rate=output_sample_rate,
                codec=codec,
                bitrate=bitrate
            )
        elif stems_as_files:
            # TODO: add multiprocessing
            for idx in range(nb_stems):
                p = Path(path)
                stem_filepath = str(Path(
                    p.parent, stem_names[idx] + p.suffix
                ))
                write_audio(
                    path=stem_filepath,
                    data=data[idx],
                    sample_rate=sample_rate,
                    output_sample_rate=output_sample_rate,
                    codec=codec,
                    bitrate=bitrate
                )
        else:
            # create temporary file and merge afterwards
            with tmp.NamedTemporaryFile(suffix='.wav') as tempfile:
                # write audio to temporary file
                write_audio(
                    path=tempfile.name,
                    data=data,
                    sample_rate=sample_rate,
                    output_sample_rate=output_sample_rate,
                    codec='wav'
                )

                # check if path is available and creat it
                Path(path).parent.mkdir(parents=True, exist_ok=True)

                channel_map = build_channel_map(
                    nb_stems=nb_stems,
                    nb_channels=nb_channels,
                    stem_names=stem_names
                )

                # convert tempfile to multistem file assuming
                # each stem occupies a pair of channels
                cmd = (
                    [
                        'ffmpeg',
                        '-y',
                        '-acodec', 'pcm_s%dle' % (16),
                        '-i', tempfile.name
                    ] + channel_map +
                    [
                        '-vn'
                    ] +
                    (
                        ['-c:a', _to_ffmpeg_codec(codec)]
                        if (codec is not None) else []
                    ) +
                    [
                        '-ar', "%d" % output_sample_rate,
                        '-strict', '-2',
                        '-loglevel', 'error'
                    ] +
                    (['-ab', str(bitrate)] if (bitrate is not None) else []) +
                    (ffmpeg_params if ffmpeg_params else []) +
                    [path]
                )
                try:
                    sp.check_call(cmd)
                except sp.CalledProcessError as err:
                    raise RuntimeError(err) from None
                finally:
                    tempfile.close()
