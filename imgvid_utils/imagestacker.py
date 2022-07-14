import cv2
from enum import Enum
from typing import Union, List, Tuple, Iterable
import os
import numpy as np

from . import file_ops as fo


class Resize(Enum):
    UP = 3
    DOWN = 4
    FIRST = 5
    NONE = 0

    def filter(self):
        return {
            Resize.FIRST: return_first,
            Resize.UP: return_max,
            Resize.DOWN: return_min
        }.get(self, return_first)

    def choose(self, dims: Iterable[Tuple[int, int]]) -> Tuple[int, int]:
        return self.filter()(dims)

    def __str__(self):
        return self.name.lower()


class Stacking:
    __slots__ = ["cols", "rows", "mode"]

    def __init__(self, cols, rows, mode):
        self.cols = cols
        self.rows = rows
        self.mode = mode

    @classmethod
    def default(cls):
        return cls(1, 1, "rd")


class ImageDataStore:
    __slots__ = ["images", "_file_name", "_ext"]

    def __init__(self, images, file_name, ext):
        self.images = images
        self._file_name = file_name
        self._ext = ext

    @property
    def ext(self):
        return self._ext

    @property
    def file_name(self):
        return self._file_name


class ImageIterator:
    # TODO: allow multiple file extension inputs.
    def __init__(self, directories, exts=None, stacking: Stacking = None):
        """
        Pass in paths to directories containing images, and extension
        of desired image inputs. Will return num images each iteration.
        May sample unevenly.

        :param directories: Input directories.
        :param exts:        Extension(s) of file to return
        :param num:         Number of images to return each iteration.
        """
        self.stacking = stacking or Stacking.default()

        if isinstance(directories, str):
            self.directories = [directories]
        else:
            if len(directories) == 0:
                raise ValueError("No directories provided.")
            self.directories = directories

        self.ext = exts or ["jpg"]
        self.stacking = stacking or Stacking.default()
        self.num = self.stacking.cols * self.stacking.rows

        if len(directories) % self.num != 0:
            raise ValueError("Directories will not be sampled evenly.")

        self.files = {}
        self._max_iters = 0
        self._max_index = 0
        self.curr_index = 0
        self.active_dir = 0

        self.index = [0] * len(self.directories)

        if not fo.check_dirs_exist(self.directories):
            raise ValueError("One or more directories do not exist.")

        self._load_dirs()

    @property
    def dimensions(self):
        return ()

    @property
    def max_iters(self):
        return self._max_iters

    @max_iters.setter
    def max_iters(self, max_iters: Union[None, int]):
        """
        Sets the number of files that this iterator will output:
        If max_iters <= 0, nothing will be returned. If max_iters >= self.max_iters, self.max_iters remains unchanged.
        Otherwise, self.max_iters = max_iters

        :param max_iters:   The maximum number of iterations that should occur.
        :return:
        """
        if max_iters is not None:
            if max_iters < 0:
                self._max_iters = 0
            elif max_iters <= self._max_iters:
                self._max_iters = max_iters

    def _load_dir(self, counter):
        files = fo.get_files(self.directories[counter], self.ext)
        self.files[counter] = files
        self.index[counter] = 0
        len_files = len(files)
        candidate_iters = len_files - len_files % self.num
        if self._max_iters == 0:
            self._max_iters = candidate_iters
        elif self._max_iters > candidate_iters:
            self._max_iters = candidate_iters

    def _load_dirs(self):
        for counter in range(len(self.directories)):
            self._load_dir(counter)
            if self._max_iters == 0:
                raise ValueError(
                    "Insufficiently many images found matching ext %s in directories %s."
                    % (", ".join(self.ext), ", ".join(self.directories[counter]))
                )
        self._max_index = self._max_iters * len(self.files)

    def __iter__(self):
        return self

    def __next__(self):
        """ Returns num images in an array. """
        if self.curr_index >= self._max_index:
            raise StopIteration()

        output = []
        for i in range(self.num):
            output.append(
                cv2.imread(self.files[self.active_dir][self.index[self.active_dir]])
            )
            self.index[self.active_dir] += 1
            self.curr_index += 1
            self.active_dir += 1
            self.active_dir %= len(self.files)

        return ImageDataStore(output, str(self.curr_index), None)


class ImageGeneratorMatchToName:
    # TODO: allow multiple file extension inputs.
    def __init__(self, directories, max_iters=None, exts=None):
        """

        :param directories: Directories from which to draw images.
        """

        if isinstance(directories, str):
            self.directories = [directories]
        else:
            if len(directories) == 0:
                raise ValueError("No directories provided.")
            self.directories = directories

        self.file_location_in_dir = {}

        self.curr_index = 0
        self.candidates = []
        self._max_iters = 0

        self.exts = exts or ["jpg", "png"]

        if fo.check_dirs_exist(self.directories):
            self._load_dirs()
            self.max_iters = max_iters
        else:
            raise ValueError("One or more directories do not exist.")

    @property
    def max_iters(self):
        return self._max_iters

    @max_iters.setter
    def max_iters(self, max_iters: Union[None, int]):
        if max_iters is not None:
            if max_iters < 0:
                self._max_iters = 0
            elif max_iters < self._max_iters:
                self._max_iters = max_iters

    def _load_dir(self, counter):
        directory = self.directories[counter]
        files = fo.get_files(directory, self.exts)

        if not files:
            raise ValueError(f"No files found in {directory}")

        self.file_location_in_dir[counter] = {
            os.path.basename(f_name): f_name for f_name in files
        }

        return self.file_location_in_dir[counter].keys()

    def _load_dirs(self):
        """ Finds and stores all file names which exist across all directories. """
        possible_file_names = set()
        for counter in range(len(self.directories)):
            if counter == 0:
                possible_file_names = set(self._load_dir(counter))
            else:
                possible_file_names &= set(self._load_dir(counter))

        if not possible_file_names:
            raise ValueError("No file names in common.")

        self.candidates = sorted(list(possible_file_names))
        self._max_iters = len(self.candidates)

    def __iter__(self):
        """ Returns all instances of images with matching file names, in alphabetical order. """
        return self

    def __next__(self):
        if self.curr_index < self._max_iters:
            output = []
            file_name = self.candidates[self.curr_index]
            for file_dict in self.file_location_in_dir.values():
                # TODO: Handle special file name errors
                output.append(cv2.imread(file_dict[file_name]))
            self.curr_index += 1
            base, *_, ext = os.path.splitext(file_name)
            return ImageDataStore(output, base, ext)
        else:
            raise StopIteration()


def stack_images(images, stacking: Stacking):
    """
    Expects an array of images a tuple (x,y) that represents how the images will be stacked, and a mode representing
    how the array will be stacked:

    eg. images = [img]*6, dimensions = (2,3), mode='rd':
    2 images per row, 3 rows, ordered from left to right, up to down
    :param images:       A set of opened images.
    :param stacking:     A Stacking object, which defines how the images should be stacked.
    :return:
    """
    x, y = stacking.cols, stacking.rows
    mode = stacking.mode

    images_stacked = [None] * y
    for i in range(y):
        images_stacked[i] = [None] * x
    # TODO: Excessive quantities of magic occurring here
    if mode[0] in ("l", "r"):
        for i in range(x * y):
            images_stacked[i // x if mode[1] == "d" else y - i // x - 1][
                i % x if mode[0] == "r" else x - i % x - 1
            ] = images[i]
    elif mode[0] in ("u", "d"):
        for i in range(x * y):
            images_stacked[i % y if mode[0] == "d" else y - i % y - 1][
                i // y if mode[0] == "r" else x - i // y - 1
            ] = images[i]
    return np.concatenate(
        tuple([np.concatenate(tuple(row), axis=1) for row in images_stacked]), axis=0
    )


def resize_images(images, dimensions: Tuple[int, int]):
    """
    Resizes all of the images to the specified dimensions.
    :param images:          A set of opened images.
    :param dimensions:      The dimensions to resize the images to.
    :return:
    """
    return [cv2.resize(img, dimensions) for img in images]


def make_image_from_images(
    files_in: Union[List[str], str],
    dir_out="./",
    file_name="output",
    ext_out="jpg",
    stacking: Stacking = None,
    size: Tuple[int, int] = (640, 480),
):
    """

    :param files_in:    List of files to read and place into the image.
    :param dir_out:     The directory to output the file(s) to. If it does not exist, it will be created.
    :param file_name:   The initial portion of the filename common to each file.
    :param ext_out:     Output extension for the images.
    :param stacking:    A Stacking object, which defines how the component images should be stacked.
    :param size:        Dimensions of each component image in px.
    :return:
    """
    file_name = fo.form_file_name(dir_out, file_name, ext_out)
    os.makedirs(os.path.dirname(file_name), exist_ok=True)

    stacking = stacking or Stacking.default()

    if isinstance(files_in, str):
        files_in = [files_in]

    images = []
    for file in files_in:
        images.append(cv2.imread(file))
    cv2.imwrite(
        file_name,
        stack_images(
            resize_images(images, size), stacking
        ),
    )


def make_images_from_folders_match(
    image_iter: ImageGeneratorMatchToName,
    dir_out,
    resize_opt: Resize = Resize.FIRST,
    stacking: Stacking = Stacking.default(),
    size: Tuple[int, int] = None,
):
    """

    :param image_iter:
    :param dir_out:         directory to output the file(s) to. If it does not exist, it will be created automatically.
    :param resize_opt:      How each set of images should be resized.
    :param stacking:        A Stacking object, which defines how the component images should be stacked.
    :param size:            Dimensions of each component image in px.
    :return:
    """
    os.makedirs(dir_out, exist_ok=True)

    def dims(images):
        return size or resize_opt.choose([(image.shape[1], image.shape[0]) for image in images])

    for image_data in image_iter:
        images = image_data.images
        file_name = fo.form_file_name(dir_out, image_data.file_name, image_data.ext)
        cv2.imwrite(
            file_name,
            stack_images(
                resize_images(images, dims(images)), stacking
            ),
        )


def make_images_from_iterator(
    image_iter: ImageIterator,
    dir_out: str = "./",
    base_name: str = "output",
    ext_out="jpg",
    max_imgs: int = None,
    size: Tuple[int, int] = (640, 480),
):
    """
    Draws images with the given extension(s) equally from each folder, resizes each
     individual image to width x height, concatenates them according to the mode, and saves them to dir_out.
    :param dir_out:         directory to output the file(s) to. If it does not exist, it will be created automatically.
    :param base_name:       The initial portion of the filename common to each file.
    :param ext_out:         output extension for the images
    :param max_imgs:        Maximum number of output images.
    :param size:            Dimensions of each component image in px.
    :return:
    """
    os.makedirs(dir_out, exist_ok=True)
    num_zeros = len(str(image_iter.max_iters - 1))

    for counter, image_data in enumerate(image_iter):
        if counter >= max_imgs:
            break

        file_name = fo.form_file_name(
            dir_out, base_name + image_data.file_name.zfill(num_zeros), ext_out
        )

        cv2.imwrite(
            file_name,
            stack_images(
                resize_images(image_data.images, size),
                image_iter.stacking,
            ),
        )


def get_dimensions_files(
    files_in: Union[List[str], str],
    exts: Union[List[str], str],
    resize: Resize
):
    """
    Returns the appropriate dimensions given resize.
    :param files_in:    One or more files with dimensions of interest
    :param exts:        The file extension(s).
    :param resize:      A Resize enum.
    :return:
    """
    if isinstance(files_in, str):
        files_in = [files_in]

    if len(files_in) == 0:
        raise ValueError("get_dimensions_files requires at least one file.")

    if not fo.has_video_exts(exts):
        return resize.choose(get_img_dimensions(files_in))
    else:
        return resize.choose(get_video_dimensions(files_in))


def get_dimensions_dirs(dirs_in: Union[List[str], str], ext: str, resize: Resize):
    """
    Returns the appropriate dimensions given resize.
    :param dirs_in:     One or more directories with files of interest
    :param ext:         The file extension(s).
    :param resize:      A Resize enum.
    :return:
    """
    if isinstance(dirs_in, str):
        return get_dimensions_files(fo.get_files(dirs_in, ext), ext, resize)

    if len(dirs_in) == 0:
        raise ValueError("Insufficient directories.")

    def dimension_generator():
        for dir_in in dirs_in:
            try:
                yield get_dimensions_files(fo.get_files(dir_in, ext), ext, resize)
            except ValueError:
                continue

    try:
        return resize.choose(dimension_generator())
    except ValueError:
        if isinstance(ext, str):
            ext = [ext]
        raise ValueError(
            "No files with given extension(s) %s found in any directory."
            % (", ".join(ext),)
        )


def get_img_dimensions(imgs_in: Iterable[str]):
    """
    Given a list of file paths, returns the dimensions of the images corresponding to the file paths
    :param imgs_in:     List of file paths corresponding to image files.
    :return:            List of corresponding file dimensions.
    """
    for img in imgs_in:
        file = cv2.imread(img)
        yield file.shape[1], file.shape[0]


def get_video_dimensions(videos_in: Iterable[str]):
    """
    Given a list of file paths, returns the dimensions of the videos corresponding to the file paths.

    :param videos_in:   List of file paths corresponding to video files.
    :return:            List of corresponding file dimensions.
    """
    for vid in videos_in:
        file = cv2.VideoCapture(vid)
        yield (int(file.get(cv2.CAP_PROP_FRAME_WIDTH)),
               int(file.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        file.release()


def return_first(items):
    """
    Returns the first element in an array.
    :param items:       Any iterable.
    :return:            The first item in the iterable, or None if the iterable is empty.
    """
    try:
        return next(items)
    except TypeError:
        return next(iter(items))
    except StopIteration:
        return None


def return_max(list_of_dims: Iterable[Tuple[int, int]]) -> Tuple[int, int]:
    """
    Returns the dimensions that produce the maximum area.
    In the event of a tie, will return the first match.

    :param list_of_dims: A list of dimensions.
    :return:             The dimensions with the greatest area.
    """
    return max(list_of_dims, key=lambda dim: dim[0] * dim[1], default=None)


def return_min(list_of_dims: Iterable[Tuple[int, int]]) -> Tuple[int, int]:
    """
    Returns the dimensions that produce the minimum area.
    In the event of a tie, will return the first match.

    :param list_of_dims: A list of dimensions.
    :return:             The dimensions with the minimum area.
    """
    return min(list_of_dims, key=lambda dim: dim[0] * dim[1], default=None)
