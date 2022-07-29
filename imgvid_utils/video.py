from typing import Union, List, Tuple

import cv2

from . import file_ops as fo
from . import image as ims
from .image import Stacking


def video_dimensions(video) -> Tuple[int, int]:
    return int(video.get(cv2.CAP_PROP_FRAME_WIDTH)), int(
        video.get(cv2.CAP_PROP_FRAME_HEIGHT)
    )


class VideoIterator(ims.GenericImageIterator):
    def __init__(
        self,
        paths: Union[List[str], str],
        stacking: Stacking = Stacking.default(),
        lock_framerate: bool = True,
    ):
        """
        Initializes a video iterator that will return num frames per iteration from each video in paths_to_videos.

        :param paths:     The file paths to the videos to read
        :param num:                 The number of frames to return each iteration.
        """
        super().__init__(stacking=stacking)

        if isinstance(paths, str):
            paths = [paths]

        self.paths = paths

        if not fo.check_files_exist(paths):
            raise ValueError("One or more videos not found.")

        self.videos = []
        self.frame_index = 0
        self.completed_videos = set()
        self.last_frame = [None] * len(self.paths)
        self.fps = None
        self.frame_lock = lock_framerate
        self._load_videos()

    def _set_dims(self):
        """
        If one or more dimensions are not already set, sets the image dimensions automatically.
        Assumes that all videos have been initialized.
        """
        self.resize_in(
            ims.Resize.DOWN.choose(video_dimensions(video) for video in self.videos)
        )

    def _load_video(self, counter):
        video = cv2.VideoCapture(self.paths[counter])
        self.videos.append(video)
        if self.frame_lock:
            if self.fps not in {None, video.get(cv2.CAP_PROP_FPS)}:
                raise ValueError("Video FPS does not match.")
            else:
                self.fps = video.get(cv2.CAP_PROP_FPS)

    def _load_videos(self):
        """
        Loads the videos into memory, initializes variables.

        :return:
        """
        for counter in range(len(self.paths)):
            self._load_video(counter)
        self._max_iters = max(
            video.get(cv2.CAP_PROP_FRAME_COUNT) for video in self.videos
        )
        self._set_dims()

    def __iter__(self):
        return self

    # Returns num frames from all videos. If one video has reached the end, will keep last frame.
    def __next__(self):
        if self._num_iters >= self._max_iters:
            raise StopIteration()

        output = []
        for i, video in enumerate(self.videos):
            if i not in self.completed_videos:
                success, image = video.read()
                if success:
                    self.last_frame[i] = image
                else:
                    video.release()
                    self.completed_videos.add(i)
            output.append(self.last_frame[i])

        name, ext = self._name_file()
        images = ims.ImageDataStore(output, name, ext)
        self._num_iters += 1
        self.frame_index += 1

        return self._apply_transforms(images)

    def skip(self, count: int):
        self.frame_index += count
        for i, video in enumerate(self.videos):
            if i not in self.completed_videos:
                video.set(cv2.CAP_PROP_POS_FRAMES, self.frame_index)
        return self

    def take(self, count: int):
        self._max_iters = count
        return self
