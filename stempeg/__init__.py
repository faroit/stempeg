from .read import read_stems
from .read import Info
from .read import StreamsReader, ChannelsReader
from .write import write_stems
from .write import write_audio
from .write import FilesWriter, StreamsWriter, ChannelsWriter, NIStemsWriter

from .cmds import check_available_aac_encoders

import re
import os
import subprocess as sp
from os import path as op
import argparse
import pkg_resources

__version__ = "0.2.0"


def example_stem_path():
    """Get the path to an included stem file.

    Returns
    -------
    filename : str
        Path to the stem file
    """
    return pkg_resources.resource_filename(
        __name__,
        'data/The Easton Ellises - Falcon 69.stem.mp4'
    )


def default_metadata():
    """Get the path to included stems metadata.

    Returns
    -------
    filename : str
        Path to the json file
    """
    return pkg_resources.resource_filename(
        __name__,
        'data/default_metadata.json'
    )


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


