import re
import subprocess as sp
import logging
import os

FFMPEG_PATH = None
FFPROBE_PATH = None
MP4BOX_PATH = None


def find_cmd(cmd):
    try:
        from shutil import which
        return which(cmd)
    except ImportError:
        import os
        for path in os.environ["PATH"].split(os.pathsep):
            if os.access(os.path.join(path, cmd), os.X_OK):
                return path

    return None


def ffmpeg_exists():
    global FFMPEG_PATH
    # check environment variable
    if "FFMPEG_PATH" in os.environ:
        env_path = os.environ["FFMPEG_PATH"]
        FFMPEG_PATH = find_cmd(env_path)
    else:
        FFMPEG_PATH = find_cmd("ffmpeg")

    return FFMPEG_PATH is not None


def ffprobe_exists():
    global FFPROBE_PATH
    if "FFPROBE_PATH" in os.environ:
        env_path = os.environ["FFPROBE_PATH"]
        FFPROBE_PATH = find_cmd(env_path)
    else:
        FFPROBE_PATH = find_cmd("ffprobe")

    return FFPROBE_PATH is not None


def mp4box_exists():
    global MP4BOX_PATH
    print(MP4BOX_PATH)

    if "MP4BOX_PATH" in os.environ:
        env_path = os.environ["MP4BOX_PATH"]
        MP4BOX_PATH = find_cmd(env_path)
    else:
        MP4BOX_PATH = find_cmd("MP4Box")
        print(MP4BOX_PATH)

    return MP4BOX_PATH is not None


if not ffmpeg_exists():
    raise RuntimeError(
        "ffmpeg could not be found! "
        "Please install it before using stempeg. "
        "See: https://github.com/faroit/stempeg"
    )


if not ffprobe_exists():
    raise RuntimeError(
        "ffprobe could not be found! "
        "Please install it before using stempeg. "
        "See: https://github.com/faroit/stempeg"
    )


def check_available_aac_encoders():
    """Returns the available AAC encoders

    Returns:
        list(str): List of available encoder codecs from ffmpeg

    """
    cmd = [
        FFMPEG_PATH,
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


def get_aac_codec():
    """Checks codec and warns if `libfdk_aac` codec
     is not available.

    Returns:
        str: ffmpeg aac codec name
    """
    avail = check_available_aac_encoders()
    if avail is not None:
        if 'libfdk_aac' in avail:
            codec = 'libfdk_aac'
        else:
            logging.warning(
                "For the better audio quality, install `libfdk_aac` codec."
            )
            codec = 'aac'
    else:
        codec = 'aac'

    return codec
