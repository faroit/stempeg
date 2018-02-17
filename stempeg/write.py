import subprocess as sp
import soundfile as sf
import tempfile as tmp
from itertools import chain
import warnings
import re
import stempeg


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
    match = re.findall('\(encoders: ([^\)]*) \)', hay)
    if match:
        return match[0].split(" ")
    else:
        return None


def write_stems(
    audio,
    filename,
    rate=44100,
    bitrate=256000,
    codec=None,
    ffmpeg_params=None
):
    """Write stems from numpy Tensor

    Parameters
    ----------
    audio : array_like
        The tensor of Matrix of stems. The data shape is formatted as
        :code:`stems x channels x samples`.
    filename : str
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

    tmps = [
        tmp.NamedTemporaryFile(delete=False, suffix='.wav')
        for t in range(audio.shape[0])
    ]

    if audio.shape[1] % 1024 != 0:
        warnings.warn(
            "Number of samples does not divide by 1024, be aware that "
            "the AAC encoder add silence to the input signal"
        )

    for k in range(audio.shape[0]):
        sf.write(tmps[k].name, audio[k], rate)

    cmd = (
        [
            'ffmpeg', '-y',
            "-f", 's%dle' % (16),
            "-acodec", 'pcm_s%dle' % (16),
            '-ar', "%d" % rate,
            '-ac', "%d" % 2
        ] +
        list(chain.from_iterable(
            [['-i', i.name] for i in tmps]
        )) +
        list(chain.from_iterable(
            [['-map', str(k)] for k, _ in enumerate(tmps)]
        )) +
        [
            '-vn',
            '-acodec', codec,
            '-ar', "%d" % rate,
            '-strict', '-2',
            '-loglevel', 'error'
        ] +
        (['-ab', str(bitrate)] if (bitrate is not None) else []) +
        (ffmpeg_params if ffmpeg_params else []) +
        [filename]
    )
    sp.call(cmd)
