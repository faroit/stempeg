from .read import read_stems
from .read import read_info
from .read import Info
from .write import write_stems
from .write import check_available_aac_encoders

import re
import os
import subprocess as sp
from os import path as op
import soundfile as sf
import argparse

__version__ = "0.2.0"


def ffmpeg_version():
    """Returns the available ffmpeg version

    Returns
    ----------
    version : str
        version number as string
    """

    cmd = [
        'ffmpeg',
        '-version'
    ]

    output = sp.check_output(cmd)
    aac_codecs = [
        x for x in
        output.splitlines() if "ffmpeg version " in str(x)
    ][0]
    hay = aac_codecs.decode('ascii')
    match = re.findall(r'ffmpeg version (\d+\.)?(\d+\.)?(\*|\d+)', hay)
    if match:
        return "".join(match[0])
    else:
        return None


def cli(inargs=None):
    """
    Commandline interface for receiving stem files
    """

    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--version', '-V',
        action='version',
        version='%%(prog)s %s' % __version__
    )

    parser.add_argument(
        'filename',
        metavar="filename",
        help="Input STEM file"
    )

    parser.add_argument(
        '--id',
        metavar='id',
        type=int,
        nargs='+',
        help="A list of stem_ids"
    )

    parser.add_argument(
        '-s',
        type=float,
        nargs='?',
        help="start offset in seconds"
    )

    parser.add_argument(
        '-t',
        type=float,
        nargs='?',
        help="read duration"
    )

    parser.add_argument(
        'outdir',
        metavar='outdir',
        nargs='?',
        help="Output folder"
    )

    args = parser.parse_args(inargs)
    stem2wav(args.filename, args.outdir, args.id, args.s, args.t)


def stem2wav(
    stems_file,
    outdir=None,
    idx=None,
    start=None,
    duration=None,
):
    S, sr = read_stems(stems_file, stem_id=idx, start=start, duration=duration)

    rootpath, filename = op.split(stems_file)

    basename = op.splitext(filename)[0]
    if ".stem" in basename:
        basename = basename.split(".stem")[0]

    if outdir is not None:
        if not op.exists(outdir):
            os.makedirs(outdir)

        rootpath = outdir

    for i in range(S.shape[0]):
        outfile = op.join(rootpath, "%s_%s.wav" % (basename, i))
        sf.write(outfile, S[i], sr)
