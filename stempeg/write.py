import subprocess as sp
import soundfile as sf
import tempfile as tmp
from itertools import chain
import warnings
import re
import stempeg
import ffmpeg


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


def write_stems(
    audio,
    path,
    rate=44100,
    bitrate=256000,
    codec="m4a",
    ffmpeg_params=None
):
    """Write stems from numpy Tensor

    Parameters
    ----------
    audio : array_like
        The tensor of Matrix of stems. The data shape is formatted as
        :code:`stems x samples x channels`.
    path : str
        Output file_name of the stems file
    rate : int
        Output samplerate. Defaults to 44100 Hz.
    bitrate : int
        AAC Bitrate in Bits per second. Defaults to 256 Kbit/s
    codec : str
        AAC codec used. Defaults to `None` which automatically selects
        either `libfdk_aac` or `aac` in that order, determined by availability.
    ffmpeg_params : list(str)
        List of additional ffmpeg parameters

    Notes
    -----

    Output is written as 16bit/44.1 kHz

    """
    if int(stempeg.ffmpeg_version()[0]) < 3:
        warnings.warn(
            "Writing STEMS with FFMPEG version < 3 is unsupported", UserWarning
        )

    if codec is None:
        avail = check_available_aac_encoders()

        if avail is not None:
            if 'libfdk_aac' in avail:
                codec = 'libfdk_aac'
            else:
                codec = 'aac'
                warnings.warn("For better quality, please install libfdc_aac")
        else:
            codec = 'aac'
            warnings.warn("For better quality, please install libfdc_aac")

    if audio.shape[1] % 1024 != 0:
        warnings.warn(
            "Number of samples does not divide by 1024, be aware that "
            "the AAC encoder add silence to the input signal"
        )

    input_kwargs = {'ar': rate, 'ac': audio.shape[-1]}
    output_kwargs = {'ar': rate, 'strict': '-2'}

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
        process.stdin.write(audio.astype('<f4').tobytes())
        process.stdin.close()
        process.wait()
    except IOError:
        raise Warning(f'FFMPEG error: {process.stderr.read()}')
    # list(chain.from_iterable(
    #     [['-i', i.name] for i in tmps]
    # )) +
    # list(chain.from_iterable(
    #     [['-map', str(k)] for k, _ in enumerate(tmps)]
    # )) +
