import subprocess as sp
import os
import soundfile as sf
from itertools import chain

try:
    from contextlib import nested  # Python 2
except ImportError:
    from contextlib import ExitStack, contextmanager

    @contextmanager
    def nested(*contexts):
        """
        Reimplementation of nested in python 3.
        """
        with ExitStack() as stack:
            for ctx in contexts:
                stack.enter_context(ctx)
            yield contexts


class tempfile:
    """ Context for temporary file.
    Will find a free temporary filename upon entering
    and will try to delete the file on leaving

    """
    def __enter__(self):
        import tempfile as tmp

        tf = tmp.NamedTemporaryFile(delete=False)
        tf.file.close()
        self.name = tf.name
        return tf.name

    def __exit__(self, type, value, traceback):
        try:
            os.remove(self.name)
        except OSError as e:
            if e.errno == 2:
                pass
            else:
                raise e


def write_stems(
    audio,
    filename,
    rate=44100,
    codec='libfdk_aac',
    bitrate=256000,
    ffmpeg_params=None
):
    """Write STEMS format from numpy Tensor

    Parameters
    ----------
    audio : array_like
        The tensor of Matrix of stems. The data shape is formatted as
        :code:`stems x samples x channels`.
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

    with nested(*[tempfile()] * audio.shape[0]) as x:
        for k, i in enumerate(x):
            sf.write(i.name, audio[k], rate)

        cmd = (
            [
                'ffmpeg', '-y',
                "-f", 's%dle' % (16),
                "-acodec", 'pcm_s%dle' % (16),
                '-ar', "%d" % rate,
                '-ac', "%d" % 2
            ] +
            list(chain.from_iterable(
                [['-i', i.name] for i in x]
            )) +
            list(chain.from_iterable(
                [['-map', str(k)] for k, _ in enumerate(x)]
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
