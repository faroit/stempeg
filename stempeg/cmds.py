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


def ffmpeg_and_ffprobe_exists():
    global FFMPEG_PATH, FFPROBE_PATH
    if FFMPEG_PATH is None:
        FFMPEG_PATH = find_cmd("ffmpeg")

    if FFPROBE_PATH is None:
        FFPROBE_PATH = find_cmd("ffprobe")

    return FFMPEG_PATH is not None and FFPROBE_PATH is not None


def mp4box_exists():
    global MP4BOX_PATH
    if MP4BOX_PATH is None:
        MP4BOX_PATH = find_cmd("mp4box")
    return MP4BOX_PATH is not None


if not ffmpeg_and_ffprobe_exists():
    raise RuntimeError(
        'ffmpeg or ffprobe could not be found! '
        'Please install them before using stempeg. '
        'See: https://github.com/faroit/stempeg'
    )
