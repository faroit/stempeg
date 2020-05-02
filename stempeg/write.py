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
        The tensor of Matrix of streams. The data shape is formatted as
        :code:`streams x samples x channels`.
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

    input_kwargs = {'ar': sample_rate, 'ac': data.shape[-1]}
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


def write_stems(
    path,
    data,
    sample_rate=44100,
    stream_names=None
):
    write_streams(
        path,
        data,
        sample_rate=sample_rate,
        output_sample_rate=44100,
        codec="aac",
        bitrate=256000,
        ffmpeg_params=None,
        streams_as_multichannel=False,
        stream_names=stream_names
    )


def write_streams(
    path,
    data,
    sample_rate=44100,
    output_sample_rate=None,
    codec=None,
    bitrate=None,
    ffmpeg_params=None,
    streams_as_multichannel=False,
    streams_as_files=False,
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
    streams_as_multichannel : bool
        streams will be saved as multiple channels
        (if multichannel is supported).
    streams_as_files : bool
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
         when `streams_as_multichannel=False` (default)
    1b.) streams will be aggregated into channels and saved as
         multichannel file.
         Here the `audio` tensor of `shape=(streams, samples, 2)`
         will be converted to a single-stream multichannel audio
         `(samples, streams*2)`. This option is activated using
         `streams_as_multichannel=True`
    1c.) streams will be saved as multiple files when `streams_as_files` is active

    For 2.), when the container does not support multiple streams there
    are also two options:

    2a) `streams_as_multichannel` has to be set to True (See 1b) otherwise an
        error will be raised. Note that this only works for `wav` and `flac`).
        * file ending of `path` determines the container (but not the codec!).
    2b) `streams_as_files` so that multiple files will be created when `streams_as_files` is active


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
        keys = data.keys()
        values = data.values()
        data = np.array(list(values))
        stream_names = list(keys)
    else:
        if stream_names is None:
            stream_names = [str(k) for k in range(data.shape[0])]

    if data.shape[1] % 1024 != 0:
        logging.warning(
            "Number of samples does not divide by 1024, be aware that "
            "the AAC encoder add silence to the input signal"
        )

    if data.ndim == 3:
        nb_streams = data.shape[0]
    else:
        nb_streams = 1

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
        if nb_channels % 2 != 0:
            warnings.warning("Only stereo streams are supported", UserWarning)

        # For more than one stream, streams will be reshaped
        # into the channel dimension, always assuming we have stereo channels
        # (streams, samples, 2)->(samples, streams*2)
        # this multichannel file will be temporarily
        # saved as wav file

        if not streams_as_files:
            # swap stream axis
            data = data.transpose(1, 0, 2)
            # aggregate stream and channels
            data = data.reshape(data.shape[0], -1)

    if streams_as_multichannel:
        data = np.squeeze(data)
        write_audio(
            path=path,
            data=data,
            sample_rate=sample_rate,
            output_sample_rate=output_sample_rate,
            codec=codec,
            bitrate=bitrate
        )
    elif streams_as_files:
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

            # convert tempfile to multistream file assuming
            # each stream occupies a pair of channels
            cmd = (
                [
                    'ffmpeg',
                    '-y',
                    '-acodec', 'pcm_s%dle' % (16),
                    '-i', tempfile.name
                ] +
                (
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
                                "-metadata:s:a:%d" % idx,
                                "handler_name=%s" % stream_names[idx],
                                "-metadata:s:a:%d" % idx,
                                "title=%s" % stream_names[idx]
                            ]
                            for idx in range(nb_streams)
                        ]
                    )
                ) +
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
