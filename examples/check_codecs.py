"""Opens a stem file prints stream info
"""
import stempeg


if __name__ == '__main__':
    # read stems
    Info = stempeg.check_available_aac_encoders()
    print(Info)
