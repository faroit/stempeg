import argparse
import stempeg


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'input',
    )
    args = parser.parse_args()

    # read stems
    S, sr = stempeg.read_stems(args.input)
    print(S.shape)
    # write strems
    stempeg.write_stems(S, "out.mp4", sr)
