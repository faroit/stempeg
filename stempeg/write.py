import subprocess as sp
import tempfile as tmp
import numpy as np
from itertools import chain
import warnings
import logging
import re
import stempeg
import ffmpeg
import os
from pathlib import Path


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


# TODO: test single estimates
def write_audio(
    path,
    data,
    sample_rate=44100,
    output_sample_rate=None,
    codec=None,
    bitrate=None
):
    """Write streams from numpy Tensor

    Parameters
    ----------
    path : str
        Output file_name of the streams file
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


def build_channel_map(nb_streams, nb_channels, stream_names):
    if nb_channels == 1:
        return (
            [
                '-filter_complex',
                # set merging
                ';'.join(
                    "[a:0]pan=mono| c0=c%d[a%d]" % (
                        idx, idx
                    )
                    for idx in range(nb_streams)
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
                        "title=%s_title" % stream_names[idx],
                        # add handler tag (e.g. read by ffmpeg < 4.1)
                        "-metadata:s:a:%d" % idx,
                        "handler=%s" % stream_names[idx],
                        # add handler tag for ffmpeg >= 4.1
                        "-metadata:s:a:%d" % idx,
                        "handler_name=%s" % stream_names[idx]
                    ]
                    for idx in range(nb_streams)
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
                    for idx in range(nb_streams)
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
                        "title=%s_title" % stream_names[idx],
                        # add handler tag (e.g. read by ffmpeg -i)
                        "-metadata:s:a:%d" % idx,
                        "handler=%s" % stream_names[idx],
                        # add handler tag for ffmpeg >= 4.1
                        "-metadata:s:a:%d" % idx,
                        "handler_name=%s" % stream_names[idx]
                    ]
                    for idx in range(nb_streams)
                ]
            )
        )
    else:
        raise NotImplementedError("not works")


def write_ni_stems(
    path,
    data,
    sample_rate=44100,
    stream_names=None
):
    """Shortcut for Native Instruments stems format"""
    # TODO: Check for stereo
    if data.ndim != 3:
        warnings.warning("Please pass multiple streams", UserWarning)

    if data.shape[2] % 2 != 0:
        warnings.warning("Only stereo streams are supported", UserWarning)

    if data.shape[1] % 1024 != 0:
        logging.warning(
            "Number of samples does not divide by 1024, be aware that "
            "the AAC encoder add silence to the input signal"
        )

    # TODO: check samplerate
    # raise error if checks not passed
    write_stems(
        path,
        data,
        sample_rate=sample_rate,
        output_sample_rate=44100,
        codec="aac",
        bitrate=256000,
        ffmpeg_params=None,
        stems_as_channels=False,
        stream_names=stream_names
    )


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
    stream_names=None
):
    """Write streams from numpy Tensor

    Parameters
    ----------
    path : str
        Output file_name of the streams file
    data : array_like or dict
        The tensor of Matrix of streams. The data shape is formatted as
            :code:`(streams, samples, channels)`.
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
        streams will be saved as multiple channels
        (if multichannel is supported).
    stems_as_files : bool
        streams will be saved as multiple files. Here, the basename(path),
        is ignored and just the parent path + extension is used.
    stream_names : list(str)
        provide a name of each streams, if `data` is array_like
        defaults to enumerated

    Notes
    -----

    The procedure for writing stream files varies depending of the
    specified output container format. There are two possible
    stream saving is done:

    1.) container supports multiple streams (`mp4/m4a`, `opus`, `mka`)
    2.) container does not support multiple streams (`wav`, `mp3`, `flac`)

    For 1.) we provide two options:

    1a.) streams will be saved as substreams aka
            when `stems_as_channels=False` (default)
    1b.) streams will be aggregated into channels and saved as
        multichannel file.
        Here the `audio` tensor of `shape=(streams, samples, 2)`
        will be converted to a single-stream multichannel audio
        `(samples, streams*2)`. This option is activated using
        `stems_as_channels=True`
    1c.) streams will be saved as multiple files when `stems_as_files` is
         active

    For 2.), when the container does not support multiple streams there
    are also two options:

    2a) `stems_as_channels` has to be set to True (See 1b) otherwise an
        error will be raised. Note that this only works for `wav` and `flac`).
        * file ending of `path` determines the container (but not the codec!).
    2b) `stems_as_files` so that multiple files will be created when
        stems_as_files` is active


    """
    if int(stempeg.ffmpeg_version()[0]) < 3:
        warnings.warning(
            "Writing streams with FFMPEG version < 3 is unsupported",
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
        stream_names = list(keys)
    else:
        if stream_names is None:
            stream_names = [str(k) for k in range(data.shape[0])]

    if data.ndim != 3:
        raise RuntimeError("Input tensor dimension should be 3d")

    nb_streams = data.shape[0]
    nb_channels = data.shape[-1]

    if nb_streams == 1:
        # for single stream audio remove stream dimension (if 1)
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
        # For more than one stream, streams will be reshaped
        # into the channel dimension, always assuming we have stereo channels
        # (streams, samples, 2)->(samples, streams*2)
        # this multichannel file will be temporarily
        # saved as wav file
        if not stems_as_files:
            # swap stream axis
            data = data.transpose(1, 0, 2)
            # aggregate stream and channels
            data = data.reshape(data.shape[0], -1)

        if stems_as_channels:
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
            for idx in range(nb_streams):
                p = Path(path)
                stream_filepath = str(Path(
                    p.parent, stream_names[idx] + p.suffix
                ))
                write_audio(
                    path=stream_filepath,
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
                    nb_streams=nb_streams,
                    nb_channels=nb_channels,
                    stream_names=stream_names
                )

                # convert tempfile to multistream file assuming
                # each stream occupies a pair of channels
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
