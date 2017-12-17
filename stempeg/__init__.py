from .read import read_stems
from .read import read_info
from .write import write_stems


import os
from os import path as op
import soundfile as sf
import argparse

__version__ = "0.1.1"


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
        'outdir',
        metavar='outdir',
        nargs='?',
        help="Output folder"
    )

    args = parser.parse_args(inargs)
    stem2wav(args.filename, args.outdir, args.id)


def stem2wav(
    stems_file,
    outdir=None,
    idx=None
):
    S, sr = read_stems(stems_file, stem_id=idx)

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
