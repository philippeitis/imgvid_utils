from typing import Union, List

import cv2
import os

from . import file_ops as fo
from . import imagestacker as ims


class VideoIterator:
    def __init__(self, paths_to_videos, num=1):
        """ Initializes a video iterator that will return num frames per iteration from each video in paths_to_videos.

        :param paths_to_videos:
        :param num:
        """
        if not fo.check_files(paths_to_videos):
            raise ValueError("One or more videos not found.")

        self.num = num
        self.videos = {}
        self.paths = paths_to_videos
        self.videos_completed = {}
        self.last_frame = {}
        self.active_vid = 0
        self.fps = 0
        self.width = None
        self.height = None
        self.num_frames = 0
        self.load_videos()

    def find_min_dims(self):
        """
        Will find the smallest video dimensions. Assumes that all videos have been initialized.
        """
        if self.height is None or self.width is None:
            dims = []
            for video in self.videos.values():
                dims.append(
                    (
                        int(video.get(cv2.CAP_PROP_FRAME_WIDTH)),
                        int(video.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                    )
                )
            self.width, self.height = ims.return_min(dims)

    def load_videos(self):
        """
        Loads the videos into memory, initializes variables.

        :return:
        """
        if isinstance(self.paths, str):
            self.last_frame[0] = None
            self.videos[0] = cv2.VideoCapture(self.paths)
            self.width = int(self.videos[0].get(cv2.CAP_PROP_FRAME_WIDTH))
            self.height = int(self.videos[0].get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.fps = self.videos[0].get(cv2.CAP_PROP_FPS)
            self.num_frames = int(self.videos[0].get(cv2.CAP_PROP_FRAME_COUNT))
            self.videos_completed[0] = False
        else:
            counter = 0
            for video in self.paths:
                self.last_frame[counter] = None
                self.videos[counter] = cv2.VideoCapture(video)
                self.videos_completed[counter] = False
                if self.fps != 0:
                    if int(self.fps) != int(self.videos[counter].get(cv2.CAP_PROP_FPS)):
                        raise ValueError("Video FPS does not match.")
                else:
                    self.fps = self.videos[counter].get(cv2.CAP_PROP_FPS)
                self.num_frames = max(
                    self.num_frames, int(self.videos[0].get(cv2.CAP_PROP_FRAME_COUNT))
                )
                counter += 1
            self.find_min_dims()

    def __iter__(self):
        return self

    # Returns num frames from all videos. If one video has reached the end, will keep last frame.
    def __next__(self):
        if not all(self.videos_completed.values()):
            output = []
            for i in range(self.num):
                if not self.videos_completed[self.active_vid]:
                    success, image = self.videos[self.active_vid].read()
                    if success:
                        self.last_frame[self.active_vid] = image
                    else:
                        self.videos_completed[self.active_vid] = True
                output.append(self.last_frame[self.active_vid])
                self.active_vid += 1
                self.active_vid %= len(self.videos.keys())
            return output
        else:
            raise StopIteration()


# ORDER OF ARGUMENTS:
# input_paths, [input file types], output_path, [output file types], [num_imgs]
#  cols, rows, [dimension altering], width, height, mode

# TODO: add support for more video formats
def make_video_from_images(
    dirs_in,
    ext_in="jpg",
    dir_out="./",
    file_name="output",
    ext_out="mp4",
    video_format="mp4v",
    fps=24,
    cols=1,
    rows=1,
    width=None,
    height=None,
):
    """Creates, and saves a video with the file_name, encoded using video_format containing each video in files_in,
    containing each image in dirs_in with the appropriate extension, in order of appearance, with each individual image
    resized to width, height, stacked col x row.

    eg. dirs_in a b c d
    cols 2
    rows 2
    frame = a[i] b[i]
            c[i] d[i]
    where x[i] refers to the ith file in that directory

    :param dirs_in:         List of files to read and place into the video.
    :param ext_in:          choose files in the directory with the given extension(s).
    :param dir_out:         directory to output the file to. If it does not exist, it will be created automatically.
    :param file_name:       name of output video
    :param ext_out:         output extension for the video (default mp4)
    :param video_format:    format to encode the video in (default mp4v)
    :param fps:             desired fps of output video.
    :param cols:            number of images placed side by side (default 1)
    :param rows:            number of images placed vertically (default 1)
    :param width:           width of each sub component in px (resulting video will be width * col px high).
    :param height:          height of each sub component in px (resulting video will be height * row px high).
    :return:                nothing
    """

    supported_extensions = ["mp4"]
    if ext_out not in supported_extensions:
        raise ValueError("Extension %s is not currently supported." % (ext_out,))

    video_format = cv2.VideoWriter_fourcc(*video_format)
    # apiPreference may be required depending on cv2 version.
    image_iter = ims.ImageGenerator(dirs_in, ext_in, cols * rows)
    vid = cv2.VideoWriter(
        filename=fo.form_file_name(dir_out, file_name, ext_out),
        apiPreference=0,
        fourcc=video_format,
        fps=fps,
        frameSize=(width * cols, height * rows),
    )
    for images_data in image_iter:
        vid.write(
            ims.stack_images(
                ims.resize_images(images_data.images, (width, height)), (cols, rows)
            )
        )
    vid.release()


def make_video_from_array(
    files_in,
    dir_out="./",
    file_name="output",
    ext_out="mp4",
    video_format="mp4v",
    fps=24,
    width=None,
    height=None,
):
    """ Creates, and saves a video with the file_name, encoded using video_format containing each video in files_in,
    containing each image in files_in in order of appearance, with each individual image resized to width, height.

    :param files_in:        List of files to read and place into the video.
    :param dir_out:         directory to output the file to. If it does not exist, it will be created automatically.
    :param file_name:       name of output video
    :param ext_out:         output extension for the video (default mp4)
    :param video_format:    format to encode the video in (default mp4v)
    :param fps:             desired fps of output video.
    :param width:           width of each sub component in px (resulting video will be width * col px high).
    :param height:          height of each sub component in px (resulting video will be height * row px high).
    :return:                nothing
    """

    supported_extensions = ["mp4"]
    if ext_out not in supported_extensions:
        raise ValueError("Extension %s is not currently supported." % (ext_out,))

    video_format = cv2.VideoWriter_fourcc(*video_format)
    # apiPreference may be required depending on cv2 version.
    if isinstance(files_in, str):
        files_in = [files_in]
    exts = set([os.path.splitext(file_name)[-1] for file_name in files_in])

    if width is None or height is None:
        width, height = ims.get_first_dimensions_files(files_in, exts)

    vid = cv2.VideoWriter(
        filename=fo.form_file_name(dir_out, file_name, ext_out),
        apiPreference=0,
        fourcc=video_format,
        fps=fps,
        frameSize=(width, height),
    )

    for image in files_in:
        im = cv2.imread(image)
        vid.write(ims.resize_images([im], (width, height))[0])
    vid.release()


# Input paths should be video files. Output should be full path.
# Will stack or videos in directory x by y, and resize each input image to width by height px.
def make_video_from_videos(
    files_in: Union[List[str], str],
    dir_out: str = "./",
    file_name: str = "output",
    ext_out: str = "mp4",
    video_format: str = "mp4v",
    cols: int = 1,
    rows: int = 1,
    width: int = None,
    height: int = None,
) -> None:
    """ Creates, and saves a video with the file_name, encoded using video_format containing each video in files_in,
    stacked col x row, in order of appearance, with each individual video frame resized to width, height.

    :param files_in:        List of files to read and place into the video.
    :param dir_out:         directory to output the file to. If it does not exist, it will be created automatically
    :param file_name:       Name of output video
    :param ext_out:         output extension for the video (default mp4)
    :param video_format:    format to encode the video in (default mp4v)
    :param cols:            number of images placed side by side (default 1)
    :param rows:            number of images placed vertically (default 1)
    :param width:           width of each sub component in px (resulting video will be width * col px high).
    :param height:          height of each sub component in px (resulting video will be height * row px high).
    :return:                nothing
    """

    supported_extensions = ["mp4"]
    if ext_out not in supported_extensions:
        raise ValueError("Extension %s is not currently supported." % (ext_out,))

    video_format = cv2.VideoWriter_fourcc(*video_format)
    video_iter = VideoIterator(files_in, cols * rows)

    if width is None:
        width = video_iter.width
    if height is None:
        height = video_iter.height

    vid = cv2.VideoWriter(
        filename=fo.form_file_name(dir_out, file_name, ext_out),
        apiPreference=0,
        fourcc=video_format,
        fps=video_iter.fps,
        frameSize=(width * cols, height * rows),
    )
    for images in video_iter:
        vid.write(
            ims.stack_images(ims.resize_images(images, (width, height)), (cols, rows))
        )
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
    end_frame: int = -1,
):
    """ Takes each individual frame from the video file_in, and outputs it as an image with the file_name followed by a
    padded counter corresponding to that image's position in the video (eg. 0001) to dir_out. ext_out,
    starting at start_frame and going to end_frame. Outputs frame_count stills if end_frame is not specified.

    :param file_in:         List of files to read and place into the video.
    :param dir_out:         directory to output the file to. If it does not exist, it will be created automatically.
    :param file_name:       first part of output file names.
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
    num_frames: int = vid_iterator.num_frames
    if end_frame != -1 and frame_count == -1:
        frame_count = min(end_frame, num_frames) - start_frame
    else:
        frame_count: int = min(
            frame_count, num_frames
        ) if frame_count != -1 else num_frames
    if frame_count < 1:
        raise ValueError("Values passed in result in no or negative frames of output.")
    num_zeros = len(str(frame_count - 1))

    for frame, counter in zip(vid_iterator, range(0, num_frames)):
        # Need to eat initial video frames.
        if frame_count > counter - start_frame >= 0:
            temp_name = os.path.join(
                dir_out,
                f"{file_name}{str(counter - start_frame).zfill(num_zeros)}{ext_out}",
            )
            frames.append(temp_name)
            cv2.imwrite(temp_name, frame[0])
        elif counter > start_frame + frame_count:
            return frames

    return frames
