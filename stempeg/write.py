import subprocess as sp
import soundfile as sf
from itertools import chain


def write_stems(
    audio,
    filename,
    rate=44100,
    codec='libfdk_aac',
    bitrate=256000,
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
    ffmpeg_params : list(str)
        List of additional ffmpeg parameters

    Notes
    -----

    Output is written as 16bit/44.1 kHz

    """
    import tempfile as tmp
    tmps = [
        tmp.NamedTemporaryFile(delete=False, suffix='.wav')
        for t in range(audio.shape[0])
    ]

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
            '-loglevel', 'panic'
        ] +
        (['-ab', str(bitrate)] if (bitrate is not None) else []) +
        (ffmpeg_params if ffmpeg_params else []) +
        [filename]
    )
    sp.call(cmd)
