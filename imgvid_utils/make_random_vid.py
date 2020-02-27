from enum import Enum
import cv2


class Channel(Enum):
    RED = 1
    BLUE = 2
    GREEN = 3
    ALL = 4


# Input paths should be video files. Output should be full path.
# Will stack or videos in directory x by y, and resize each input image to width by height px.
def make_random_vid(output_path, width=64, height=48, num_frames=100, fps=24):
    fformat = "mp4v"
    fformat = cv2.VideoWriter_fourcc(*fformat)

    vid = cv2.VideoWriter(
        filename=output_path,
        apiPreference=0,
        fourcc=fformat,
        fps=fps,
        frameSize=(width, height),
    )
    for i in range(num_frames):
        vid.write(make_static_img(width, height))
    vid.release()


def make_static_img(width, height, channels=None):
    from numpy import zeros
    from numpy.random import randint

    if channels is None:
        channels = [Channel.ALL]

    # Image is in BGR format.
    if Channel.ALL in channels:
        return randint(0, 255, (height, width, 3)).astype("uint8")
    arr1 = zeros((height, width, 3))
    if Channel.BLUE in channels:
        arr1[:, :, 0] = randint(0, 255, (height, width))
    if Channel.GREEN in channels:
        arr1[:, :, 1] = randint(0, 255, (height, width))
    if Channel.RED in channels:
        arr1[:, :, 2] = randint(0, 255, (height, width))

    return arr1.astype("uint8")


def save_static_img(output_path, width, height, channels=Channel.ALL):
    if isinstance(channels, list):
        cv2.imwrite(output_path, make_static_img(width, height, channels))
    else:
        cv2.imwrite(output_path, make_static_img(width, height, [channels]))
