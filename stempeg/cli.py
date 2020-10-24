import argparse
from . import __version__

from .read import Info, read_stems
from .write import write_stems
from .write import FilesWriter

from os import path as op
import os


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
        '--extension',
        metavar='extension',
        type=str,
        default='.wav',
        help="Output extension"
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
    stem2files(
        args.filename,
        args.outdir,
        args.extension,
        args.id,
        args.s,
        args.t
    )


def stem2files(
    stems_file,
    outdir=None,
    extension="wav",
    idx=None,
    start=None,
    duration=None,
):
    info = Info(stems_file)
    S, sr = read_stems(stems_file, stem_id=idx, start=start, duration=duration)

    rootpath, filename = op.split(stems_file)

    basename = op.splitext(filename)[0]
    if ".stem" in basename:
        basename = basename.split(".stem")[0]

    if outdir is not None:
        if not op.exists(outdir):
            os.makedirs(outdir)

        rootpath = outdir

    if len(set(info.title_streams)) == len(info.title_streams):
        # titles contain duplicates
        # lets not use the metadata
        stem_names = info.title_streams
    else:
        stem_names = None

    write_stems(
        (op.join(rootpath, basename), extension),
        S,
        sample_rate=sr,
        writer=FilesWriter(
            multiprocess=True,
            output_sample_rate=sr,
            stem_names=stem_names
        )
    )
