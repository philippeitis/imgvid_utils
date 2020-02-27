import cv2
from enum import Enum
from typing import Union, List, Iterable, Collection
import os
import numpy as np

from . import file_ops as fo


class Resize(Enum):
    RESIZE_UP = 3
    RESIZE_DOWN = 4
    RESIZE_FIRST = 5
    RESIZE_NONE = 0


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


class ImageGenerator:
    # TODO: allow multiple file extension inputs.
    def __init__(self, directories, ext="jpg", num=1):
        """
        Pass in paths to directories containing images, and extension
        of desired image inputs. Will return num images each iteration.

        :param directories: Input directories.
        :param ext:         Extension of file to return
        :param num:         Number of images to return each iteration.
        """
        self.directories = directories
        self.ext = ext
        self.num = num
        self.files = {}
        self._min_files = 0
        self.curr_index = 0
        self.active_dir = 0
        self.index = {}
        # Checks that all directories are valid.
        if not fo.check_dirs(self.directories):
            raise ValueError("One or more directories do not exist.")

        self.load_dirs()

    @property
    def min_files(self):
        return self._min_files

    @min_files.setter
    def min_files(self, min_files: Union[None, int]):
        """
        Sets the number of files that this iterator will output:
        If min_files <= 0, nothing will be returned. If min_files >= self.min_files, self.min_files remains unchanged.
        Otherwise, self.min_files = min_files

        :param min_files:
        :return:
        """
        if min_files is not None:
            if min_files < 0:
                self._min_files = 0
            elif min_files <= self._min_files:
                self._min_files = min_files

    # Loads all image paths into memory.
    def load_dirs(self):
        if isinstance(self.directories, str):
            self.files[0] = fo.get_files(self.directories, self.ext)
            self.index[0] = 0
            self._min_files = len(self.files[0]) - len(self.files[0]) % self.num
            if self._min_files == 0:
                raise ValueError(
                    "No images matching %s found in directories %s."
                    % (", ".join(self.ext), ", ".join(self.directories))
                )

        else:
            counter = 0
            for directory in self.directories:
                files = fo.get_files(self.directories[counter], self.ext)
                if self._min_files == 0:
                    self._min_files = len(files)
                elif self._min_files > len(files):
                    self._min_files = len(files)
                if self._min_files == 0:
                    print("No files found in " + directory)
                else:
                    self.files[counter] = files
                    self.index[counter] = 0
                    counter += 1

            if self._min_files == 0:
                raise ValueError(
                    "No images matching %s found in directories %s."
                    % (", ".join(self.ext), ", ".join(self.directories))
                )
            self._min_files = len(self.files[0]) - len(self.files[0]) % self.num

    def __iter__(self):
        return self

    # Returns num images in array.
    def __next__(self):
        """ Returns num images in an array. """
        if self.curr_index < self._min_files * len(self.files.keys()):
            output = []
            for i in range(self.num):
                output.append(
                    cv2.imread(self.files[self.active_dir][self.index[self.active_dir]])
                )
                self.index[self.active_dir] += 1
                self.curr_index += 1
                self.active_dir += 1
                self.active_dir %= len(self.files.keys())

            return ImageDataStore(output, None, None)
        else:
            raise StopIteration()


class ImageGeneratorMatchToName:
    # TODO: allow multiple file extension inputs.
    def __init__(self, directories):
        """

        :param directories: Directories from which to draw images.
        """
        self.directories = directories
        self.files = {}
        self.num_imgs = 0
        self.curr_index = 0
        self.possible_file_names_arr = []
        # Checks that all directories are valid.
        if fo.check_dirs(self.directories):
            self.load_dirs()
        else:
            raise ValueError("One or more directories do not exist.")

    @property
    def min_files(self):
        return self.num_imgs

    @min_files.setter
    def min_files(self, min_files: Union[None, int]):
        if min_files is not None:
            if min_files < 0:
                self.num_imgs = 0
            elif min_files <= self.num_imgs:
                self.num_imgs = min_files

    def load_dirs(self):
        """ Finds and stores all file names which exist across all directories. """
        possible_file_names = set()
        if isinstance(self.directories, str):
            self.files[0] = {
                os.path.basename(f_name): f_name
                for f_name in fo.get_files(self.directories, ["jpg", "png"])
            }
            possible_file_names = set(self.files[0].keys())
        else:
            for counter, directory in enumerate(self.directories):
                files = fo.get_files(self.directories[counter], ["jpg", "png"])
                if not files:
                    raise ValueError(f"No files found in {directory}")

                self.files[counter] = {
                    os.path.basename(f_name): f_name for f_name in files
                }
                if counter == 0:
                    possible_file_names = set(self.files[counter].keys())
                else:
                    possible_file_names &= set(self.files[counter].keys())

        self.possible_file_names_arr = sorted(list(possible_file_names))
        self.num_imgs = len(self.possible_file_names_arr)

        if self.num_imgs == 0:
            raise ValueError("No file names in common.")

    def __iter__(self):
        """ Returns all instances of images with matching file names, in alphabetical order. """
        return self

    def __next__(self):
        if self.curr_index < self.num_imgs:
            output = []
            file_name = self.possible_file_names_arr[self.curr_index]

            for file_dict in self.files.values():
                output.append(cv2.imread(file_dict[file_name]))
            self.curr_index += 1

            return ImageDataStore(
                output, os.path.splitext(file_name)[0], os.path.splitext(file_name)[-1]
            )
        else:
            raise StopIteration()


def stack_images(images, dimensions, mode="rd"):
    """
    Expects an array of images a tuple (x,y) that represents how the images will be stacked, and a mode representing
    how the array will be stacked:

    eg. images = [img]*6, dimensions = (2,3), mode='rd':
    2 images per row, 3 rows, ordered from left to right, up to down
    :param images:
    :param dimensions:
    :param mode:
    :return:
    """
    x = dimensions[0]
    y = dimensions[1]
    images_stacked = [None] * y
    for i in range(y):
        images_stacked[i] = [None] * x
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


def resize_images(images, dimensions: (int, int)):
    """
    Resizes all of the images to the specified dimensions.
    :param images:
    :param dimensions:
    :return:
    """
    for i in range(len(images)):
        images[i] = cv2.resize(images[i], dimensions)
    return images


def make_image_from_images(
    files_in: Union[List[str], str],
    dir_out="./",
    file_name="output",
    ext_out="jpg",
    cols: int = 1,
    rows: int = 1,
    width: int = 640,
    height: int = 480,
    mode: str = "rd",
):
    file_name = fo.form_file_name(dir_out, file_name, ext_out)
    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    if isinstance(files_in, str):
        cv2.imwrite(file_name, cv2.imread(files_in))
    elif len(files_in) == 1:
        cv2.imwrite(file_name, cv2.imread(files_in[0]))
    else:
        images = []
        for file in files_in:
            images.append(cv2.imread(file))
        cv2.imwrite(
            file_name,
            stack_images(
                resize_images(images, (width, height)), (cols, rows), mode=mode
            ),
        )


def make_images_from_folders_match(
    dirs_in,
    dir_out,
    max_imgs=None,
    cols=1,
    rows=1,
    resize_opt: Resize = Resize.RESIZE_FIRST,
    width=None,
    height=None,
    mode="rd",
):
    image_iter = ImageGeneratorMatchToName(dirs_in)
    counter: int = 0

    if resize_opt == Resize.RESIZE_UP:
        fn = return_max
    elif resize_opt == Resize.RESIZE_DOWN:
        fn = return_min
    else:
        fn = return_first

    image_iter.min_files = max_imgs
    os.makedirs(dir_out, exist_ok=True)
    for image_data in image_iter:
        if max_imgs is None or counter < max_imgs:
            images = image_data.images
            file_name = fo.form_file_name(dir_out, image_data.file_name, image_data.ext)
            if width is None or height is None:
                dimensions = [(image.shape[1], image.shape[0]) for image in images]
                temp_width, temp_height = fn(dimensions)
                cv2.imwrite(
                    file_name,
                    stack_images(
                        resize_images(images, (temp_width, temp_height)),
                        (cols, rows),
                        mode=mode,
                    ),
                )
            else:
                cv2.imwrite(
                    file_name,
                    stack_images(
                        resize_images(images, (width, height)), (cols, rows), mode=mode
                    ),
                )
            counter += 1
        else:
            break


#
#
def make_images_from_folders(
    dirs_in: Union[List[str], str],
    ext_in: Union[List[str], str] = "jpg",
    dir_out: str = "./",
    file_name: str = "output",
    ext_out="jpg",
    max_imgs: int = None,
    cols: int = 1,
    rows: int = 1,
    width: int = 640,
    height: int = 480,
    mode="rd",
):
    """
    Draws images with the given extension equally from each folder, resizes each
     individual image to width x height, concatenates them according to the mode, and saves them to dir_out.
    :param dirs_in:
    :param ext_in:
    :param dir_out:
    :param file_name:
    :param ext_out:
    :param max_imgs:
    :param cols:
    :param rows:
    :param width:
    :param height:
    :param mode:
    :return:
    """
    image_iter = ImageGenerator(dirs_in, ext=ext_in, num=cols * rows)
    os.makedirs(dir_out, exist_ok=True)

    image_iter._min_files = max_imgs
    num_zeros = len(str(image_iter._min_files // image_iter.num - 1))
    for counter, image_data in enumerate(image_iter):
        temp_file_name = fo.form_file_name(
            dir_out, file_name + str(counter).zfill(num_zeros), ext_out
        )
        cv2.imwrite(
            temp_file_name,
            stack_images(
                resize_images(image_data.images, (width, height)),
                (cols, rows),
                mode=mode,
            ),
        )


def get_dimensions_dirs(dirs_in: Union[List[str], str], ext: str, resize: Resize):
    """
    Returns the appropriate dimensions given resize.
    :param dirs_in:
    :param ext:
    :param resize:
    :return:
    """
    if resize == Resize.RESIZE_FIRST:
        return get_first_dimensions_dirs(dirs_in, ext)
    if resize == Resize.RESIZE_UP:
        return get_max_dimensions_dirs(dirs_in, ext)
    if resize == Resize.RESIZE_DOWN:
        return get_min_dimensions_dirs(dirs_in, ext)
    else:
        return get_first_dimensions_dirs(dirs_in, ext)


def get_dimensions_files(files_in: Union[List[str], str], ext: str, resize: Resize):
    if resize == Resize.RESIZE_FIRST:
        return get_first_dimensions_files(files_in, ext)
    if resize == Resize.RESIZE_UP:
        return get_max_dimensions_files(files_in, ext)
    if resize == Resize.RESIZE_DOWN:
        return get_min_dimensions_files(files_in, ext)
    else:
        return get_first_dimensions_files(files_in, ext)


def get_first_dimensions_dirs(
    dirs_in: Union[List[str], str], ext_in: Union[List[str], str]
):
    """
    Returns the dimensions of the first valid file found with any extension in ext_in. Order
    :param dirs_in:
    :param ext_in:
    :return:
    """

    if len(dirs_in) == 0:
        raise ValueError("Insufficient directories.")

    if isinstance(dirs_in, str):
        return get_first_dimensions_files(fo.get_files(dirs_in, ext_in), ext_in)
    else:
        for dir_in in dirs_in:
            try:
                return get_first_dimensions_files(fo.get_files(dir_in, ext_in), ext_in)
            except ValueError:
                continue
        if isinstance(ext_in, str):
            ext_in = [ext_in]
        raise ValueError(
            "No files with given extension %s found in any directory."
            % (", ".join(ext_in),)
        )


def get_min_dimensions_dirs(
    dirs_in: Union[List[str], str], ext_in: Union[List[str], str]
):
    """
    Returns the minimum dimensions of any file matching the specified extensions across all
    directories in dirs_in.
    :param dirs_in:
    :param ext_in:
    :return:
    """

    if len(dirs_in) == 0:
        raise ValueError("Insufficient directories.")

    if isinstance(dirs_in, str):
        return get_min_dimensions_files(fo.get_files(dirs_in, ext_in), ext_in)
    else:
        dims = []
        for dir_in in dirs_in:
            try:
                dims.append(
                    get_min_dimensions_files(fo.get_files(dir_in, ext_in), ext_in)
                )
            except ValueError:
                continue
        try:
            return return_min(dims)
        except ValueError:
            raise ValueError(
                "No files with given extension %s found in any directory." % (ext_in,)
            )


def get_max_dimensions_dirs(
    dirs_in: Union[List[str], str], ext_in: Union[List[str], str]
):
    """
    Returns the maximum dimensions of any file matching the specified extensions across all
    directories in dirs_in.
    :param dirs_in:
    :param ext_in:
    :return:
    """

    if len(dirs_in) == 0:
        raise ValueError("Insufficient directories.")

    if isinstance(dirs_in, str):
        return get_max_dimensions_files(fo.get_files(dirs_in, ext_in), ext_in)
    else:
        dims = []
        for dir_in in dirs_in:
            try:
                dims.append(
                    get_max_dimensions_files(fo.get_files(dir_in, ext_in), ext_in)
                )
            except ValueError:
                continue
        try:
            return return_max(dims)
        except ValueError:
            if isinstance(ext_in, str):
                ext_str = ext_in
            else:
                ext_str = ", ".join(ext_in)

            raise ValueError(
                f"No files with extension(s) ({ext_str}) found in any directory."
            )


def get_first_dimensions_files(
    files_in: Union[Iterable[str], str], ext_in: Union[Collection[str], str]
):
    """
    Will get the dimensions of the first file in files_in

    :param files_in:
    :param ext_in:
    :return:
    """
    if isinstance(files_in, str):
        files_in = [files_in]

    if len(files_in) == 0:
        raise ValueError("get_first_dimensions_files requires at least one file.")

    if "mp4" not in ext_in:
        return return_first(get_img_dimensions(files_in))
    else:
        return return_first(get_video_dimensions(files_in))


def get_min_dimensions_files(
    files_in: Union[List[str], str], ext_in: Union[List[str], str]
):
    """
    Gets the smallest dimensions of the input files.
    :param files_in:
    :param ext_in:
    :return:
    """
    if isinstance(files_in, str):
        files_in = [files_in]

    if len(files_in) == 0:
        raise ValueError("get_min_dimensions_files requires at least one file.")

    if "mp4" not in ext_in:
        return return_min(get_img_dimensions(files_in))
    else:
        return return_min(get_video_dimensions(files_in))


def get_max_dimensions_files(
    files_in: Union[List[str], str], ext_in: Union[List[str], str]
):
    """
    Gets the minimum and maximum dimensions of the files in the list with the given extension(s).
    :param files_in:    A list of input files for which to get dimensions for.
    :param ext_in:      The format of the files (eg. mp4, jpeg, png)
    :return:
    """
    if isinstance(files_in, str):
        files_in = [files_in]

    if len(files_in) == 0:
        raise ValueError("get_max_dimensions_files requires at least one file.")

    if "mp4" not in ext_in:
        return return_max(get_img_dimensions(files_in))
    else:
        return return_max(get_video_dimensions(files_in))


def get_img_dimensions(imgs_in: Union[List[str], str]):
    """
    Given a list of file paths, returns the dimensions of the images corresponding to the file paths
    :param imgs_in:     List of file paths corresponding to image files.
    :return:            List of corresponding file dimensions.
    """
    dims_list = []
    for img in imgs_in:
        file = cv2.imread(img)
        dims_list.append((file.shape[1], file.shape[0]))

    return dims_list


def get_video_dimensions(videos_in: Union[List[str], str]):
    """
    Given a list of file paths, returns the dimensions of the videos corresponding to the file paths.

    :param videos_in:   List of file paths corresponding to video files.
    :return:            List of corresponding file dimensions.
    """
    dims_list = []
    for vid in videos_in:
        file = cv2.VideoCapture(vid)
        dims_list.append(
            (
                int(file.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(file.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            )
        )
        file.release()

    return dims_list


def return_first(arr: list):
    """
    Returns the first element in an array.
    :param arr:     Any list.
    :return:        The first element in the list.
    """
    return arr[0] if len(arr) > 0 else None


def return_max(list_of_dims):
    """
    Returns the dimensions that produce the maximum area.
    In the event of a tie, will return the first match.

    :param list_of_dims: A list of dimensions.
    :return:             The dimensions with the greatest area.
    """
    return max(list_of_dims, key=lambda dim: dim[0] * dim[1])


def return_min(list_of_dims):
    """
    Returns the dimensions that produce the minimum area.
    In the event of a tie, will return the first match.

    :param list_of_dims: A list of dimensions.
    :return:             The dimensions with the minimum area.
    """
    return min(list_of_dims, key=lambda dim: dim[0] * dim[1])
