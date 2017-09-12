"""Converts the DSD100 Dataset to stems

requirements: install `dsdtools` via pip
"""
import dsdtools
import os
import os.path as op
import numpy as np
import sys
import stempeg

dsd = dsdtools.DB()

output_path = 'dsdstems'

if not os.path.exists(output_path):
    os.makedirs(output_path)

for track in dsd.load_dsd_tracks():
    sys.stdout.write("Convert Track: %d\b" % track.id)
    sys.stdout.write("\r")
    sys.stdout.flush()
    stems = []
    stems_path = op.join(
        output_path, op.basename(track.filename) + '.stem.mp4'
    )

    # append the mixture
    stems.append(track.audio)

    # append the targets
    for target_name, target_track in track.targets.iteritems():
        if target_name == 'accompaniment':
            continue
        stems.append(target_track.audio)

    # write stems
    S = np.array(stems)
    stempeg.write_stems(S, stems_path, track.rate)
