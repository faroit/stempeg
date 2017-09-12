import subprocess as sp
import os
import scipy.io.wavfile
import contextlib
from itertools import chain


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
    audio, filename, sr,
    codec='libfdk_aac', bitrate=256000,
    ffmpeg_params=None
):

    audio = (2**(15)*audio).astype('int16')

    with contextlib.nested(*[tempfile()] * audio.shape[0]) as x:
        for k, i in enumerate(x):
            scipy.io.wavfile.write(i, sr, audio[k].T)

        cmd = (
            [
                'ffmpeg', '-y',
                "-f", 's%dle' % (16),
                "-acodec", 'pcm_s%dle' % (16),
                '-ar', "%d" % sr,
                '-ac', "%d" % 2
            ] +
            list(chain.from_iterable(
                [['-i', i] for i in x]
            )) +
            list(chain.from_iterable(
                [['-map', str(k)] for k, _ in enumerate(x)]
            )) +
            [
                '-vn',
                '-acodec', codec,
                '-ar', "%d" % sr,
                '-strict', '-2',
                '-loglevel', 'panic',
            ] +
            (['-ab', str(bitrate)] if (bitrate is not None) else []) +
            (ffmpeg_params if ffmpeg_params else []) +
            [filename]
        )
        sp.call(cmd)
