import argparse
import pystems as ps
import soundfile as sf


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'input',
    )
    args = parser.parse_args()

    S, sr = ps.read_stems(args.input)
    for i in range(S.shape[0]):
        sf.write("ch%s.wav" % i, S[i].T, sr)
