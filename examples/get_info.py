"""Opens a stem file prints stream info
"""
import argparse
import stempeg


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'input',
    )
    args = parser.parse_args()

    # read stems
    Info = stempeg.read_info(args.input)
    print(Info)
