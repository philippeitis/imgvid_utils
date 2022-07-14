from typing import Union, List, Tuple

import cv2
import os

from . import file_ops as fo
from . import imagestacker as ims
from .imagestacker import Stacking


def get_video_dims(video) -> Tuple[int, int]:
    return int(video.get(cv2.CAP_PROP_FRAME_WIDTH)), int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))


class VideoIterator:
    def __init__(self, paths_to_videos, stacking=Stacking.default(), frame_lock=True):
        """
        Initializes a video iterator that will return num frames per iteration from each video in paths_to_videos.

        :param paths_to_videos:     The file paths to the videos to read
        :param num:                 The number of frames to return each iteration.
        """
        if not fo.check_files_exist(paths_to_videos):
            raise ValueError("One or more videos not found.")
        if isinstance(paths_to_videos, str):
            self.paths = [paths_to_videos]
        else:
            self.paths = paths_to_videos

        self.stacking = stacking
        self.num = stacking.cols * stacking.rows
        self.videos = [None] * len(self.paths)
        self.videos_completed = [False] * len(self.paths)
        self.last_frame = [None] * len(self.paths)
        self.active_vid = 0
        self.fps = 0
        self.dims = None
        self.num_frames = 0
        self.frame_lock = frame_lock
        self._load_videos()

    def _set_dims(self):
        """
        If one or more dimensions are not already set, sets the image dimensions automatically.
        Assumes that all videos have been initialized.
        """
        if self.dims is None:
            self.dims = ims.return_min([get_video_dims(video) for video in self.videos])

    def _load_video(self, counter):
        video = self.paths[counter]
        self.last_frame[counter] = None
        self.videos[counter] = cv2.VideoCapture(video)
        self.videos_completed[counter] = False
        if self.frame_lock:
            if self.fps != 0:
                if self.fps != self.videos[counter].get(cv2.CAP_PROP_FPS):
                    raise ValueError("Video FPS does not match.")
            else:
                self.fps = self.videos[counter].get(cv2.CAP_PROP_FPS)

        self.num_frames = max(
            self.num_frames, int(self.videos[0].get(cv2.CAP_PROP_FRAME_COUNT))
        )

    def _load_videos(self):
        """
        Loads the videos into memory, initializes variables.

        :return:
        """
        for counter in range(len(self.paths)):
            self._load_video(counter)
        self._set_dims()

    def __iter__(self):
        return self

    # Returns num frames from all videos. If one video has reached the end, will keep last frame.
    def __next__(self):
        if not all(self.videos_completed):
            output = []
            for i in range(self.num):
                if not self.videos_completed[self.active_vid]:
                    success, image = self.videos[self.active_vid].read()
                    if success:
                        self.last_frame[self.active_vid] = image
                    else:
                        self.videos_completed[self.active_vid] = True
                output.append(self.last_frame[self.active_vid])
                self.active_vid = (self.active_vid + 1) % len(self.videos)
            return ims.ImageDataStore(output, None, None)
        else:
            raise StopIteration()


# ORDER OF ARGUMENTS:
# input_paths, [input file types], output_path, [output file types], [num_imgs]
#  cols, rows, [dimension altering], width, height, mode


# TODO: add support for more video formats
def make_video_from_generator(
    image_iter: ims.ImageGenerator,
    dir_out="./",
    file_name="output",
    ext_out="mp4",
    video_format="mp4v",
    fps=24,
    size: Tuple[int, int] = None,
):
    """
    Creates, and saves a video with the file_name, encoded using video_format containing each video in files_in,
    containing each image in dirs_in with the appropriate extension, in order of appearance, with each individual image
    resized to width, height, stacked col x row.

    eg. dirs_in a b c d
    cols 2
    rows 2
    frame = a[i] b[i]
            c[i] d[i]
    where x[i] refers to the ith file in that directory

    :param image_iter:      An iterator producing image frames
    :param dir_out:         directory to output the file to. If it does not exist, it will be created automatically.
    :param file_name:       name of output video
    :param ext_out:         output extension for the video (default mp4)
    :param video_format:    format to encode the video in (default mp4v)
    :param fps:             fps of output video.
    :param size:            Dimensions of each component image in px.
    :return:                nothing
    """

    supported_extensions = ["mp4"]
    if ext_out not in supported_extensions:
        raise ValueError("Extension %s is not currently supported." % (ext_out,))

    video_format = cv2.VideoWriter_fourcc(*video_format)
    # apiPreference may be required depending on cv2 version.

    width, height = size

    vid = cv2.VideoWriter(
        filename=fo.form_file_name(dir_out, file_name, ext_out),
        apiPreference=0,
        fourcc=video_format,
        fps=fps,
        frameSize=(width * image_iter.stacking.cols, height * image_iter.stacking.rows),
    )
    for images_data in image_iter:
        vid.write(
            ims.stack_images(
                ims.resize_images(images_data.images, (width, height)), image_iter.stacking
            )
        )
    vid.release()


def make_video_from_images(
    files_in,
    dir_out="./",
    file_name="output",
    ext_out="mp4",
    video_format="mp4v",
    fps=24,
    size: Tuple[int, int] = None,
):
    """
    Creates, and saves a video with the file_name, encoded using video_format containing each video in files_in,
    containing each image in files_in in order of appearance, with each individual image resized to width, height.

    :param files_in:        List of files to read and place into the video.
    :param dir_out:         directory to output the file to. If it does not exist, it will be created automatically.
    :param file_name:       name of output video
    :param ext_out:         output extension for the video (default mp4)
    :param video_format:    format to encode the video in (default mp4v)
    :param fps:             desired fps of output video.
    :param size:            Dimensions of each component image in px.
    :return:                nothing
    """

    supported_extensions = ["mp4"]
    if ext_out not in supported_extensions:
        raise ValueError("Extension %s is not currently supported." % (ext_out,))

    video_format = cv2.VideoWriter_fourcc(*video_format)
    # apiPreference may be required depending on cv2 version.
    if isinstance(files_in, str):
        files_in = [files_in]

    exts = list({os.path.splitext(file_name)[-1] for file_name in files_in})

    size = size or ims.get_dimensions_files(files_in, exts, ims.Resize.FIRST)

    vid = cv2.VideoWriter(
        filename=fo.form_file_name(dir_out, file_name, ext_out),
        apiPreference=0,
        fourcc=video_format,
        fps=fps,
        frameSize=size,
    )

    for image in files_in:
        im = cv2.imread(image)
        vid.write(ims.resize_images([im], size)[0])
    vid.release()


# Splits video into a given number of frames, or all frames if frame_count = -1, and saves frames to output_dir,
# with sequential filenames (eg. 0000.png, 0001.png ... 9999.png, 0000.png is frame #1)
def split_video(
    file_in: str,
    dir_out: str,
    file_name: str = "",
    ext_out: str = "png",
    frame_count: int = -1,
    start_frame: int = 0,
    end_frame: int = None,
):
    """
    Takes each individual frame from the video file_in, and outputs it as an image with the file_name followed by a
    padded counter corresponding to that image's position in the video (eg. 0001) to dir_out. ext_out,
    starting at start_frame and going to end_frame. Outputs frame_count stills if end_frame is not specified.

    :param file_in:         List of files to read and place into the video.
    :param dir_out:         directory to output the file(s) to. If it does not exist, it will be created automatically.
    :param file_name:       The initial portion of the filename common to each file.
    :param ext_out:         output extension for the stills
    :param frame_count:     number of frames to save, starting at start frame. Overrides end_frame. (default -1, or all)
    :param start_frame:     first frame of video to save (default 0, beginning of video)
    :param end_frame:       frame of video to save to (not including) (default -1, end of video)
    :return:                Frame names in sequential order.
    """
    frames = []

    ext_out = ("" if ext_out[0] == "." else ".") + ext_out

    os.makedirs(dir_out, exist_ok=True)

    vid_iterator = VideoIterator(file_in)
    num_frames = vid_iterator.num_frames

    if end_frame is not None and frame_count == -1:
        frame_count = min(end_frame, num_frames) - start_frame
    else:
        frame_count = min(
            frame_count, num_frames
        ) if frame_count != -1 else num_frames
    if frame_count < 1:
        raise ValueError("Values passed in result in no or negative frames of output.")

    num_zeros = len(str(frame_count - 1))

    for i in range(start_frame):
        next(vid_iterator)

    for frame, counter in zip(vid_iterator, range(frame_count)):
        temp_name = os.path.join(
            dir_out,
            f"{file_name}{str(counter).zfill(num_zeros)}{ext_out}",
        )
        frames.append(temp_name)
        cv2.imwrite(temp_name, frame.images[0])

    return frames
