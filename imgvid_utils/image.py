from pathlib import Path

import cv2
from enum import Enum
from typing import Union, List, Tuple, Iterable, Optional
import os
import numpy as np

from . import file_ops as fo


def find(items: List, predicate) -> Optional[int]:
    """
    Returns the first index of an item in items that satisfies predicate
    :param items:
    :param predicate:
    :return:
    """
    for index, item in enumerate(items):
        if predicate(item):
            return index
    return None


class SkipIterator:
    def __init__(self, items: List, skip: int = 0):
        self.items = items
        self.ind = skip

    def skip(self, count: int = 0):
        self.ind += count
        return self

    def __iter__(self):
        return self

    def __next__(self):
        if self.ind >= len(self.items):
            raise StopIteration()
        item = self.items[self.ind]
        self.ind += 1
        return item

    def __len__(self):
        return len(self.items)

    def __getitem__(self, item: int):
        return self.items[item]


class ImageDataStore:
    __slots__ = ["images", "file_name", "ext"]

    def __init__(self, images, file_name, ext):
        self.images = images
        self.file_name = file_name
        self.ext = ext


class Transform:
    def apply(self, image_data: ImageDataStore) -> ImageDataStore:
        raise NotImplementedError()


class ResizeAll(Transform):
    def __init__(self, dims: Tuple[int, int]):
        self.dims = dims

    def apply(self, image_data: "ImageDataStore") -> "ImageDataStore":
        image_data.images = resize_images(image_data.images, self.dims)
        return image_data


class Resize(Transform, Enum):
    UP = 3
    DOWN = 4
    FIRST = 5
    NONE = 0

    def filter(self):
        return {
            Resize.FIRST: return_first,
            Resize.UP: return_max,
            Resize.DOWN: return_min,
        }.get(self, return_first)

    def choose(self, dims: Iterable[Tuple[int, int]]) -> Tuple[int, int]:
        return self.filter()(dims)

    def __str__(self):
        return self.name.lower()

    def apply(self, image_data: ImageDataStore) -> ImageDataStore:
        dims = self.choose(
            [(image.shape[1], image.shape[0]) for image in image_data.images]
        )
        image_data.images = resize_images(image_data.images, dims)
        return image_data


class Stacking(Transform):
    __slots__ = ["cols", "rows", "mode"]

    def __init__(self, cols, rows, mode):
        self.cols = cols
        self.rows = rows
        self.mode = mode

    @classmethod
    def default(cls):
        return cls(1, 1, "rd")

    def apply(self, image_data: ImageDataStore) -> ImageDataStore:
        """
        Expects an array of images a tuple (x,y) that represents how the images will be stacked, and a mode representing
        how the array will be stacked:

        eg. images = [img]*6, dimensions = (2,3), mode='rd':
        2 images per row, 3 rows, ordered from left to right, up to down
        :param image_data:       A set of opened images.
        :return:
        """
        x, y = self.cols, self.rows
        mode = self.mode

        images = image_data.images
        images_stacked = [[None] * x for _ in range(y)]

        # TODO: Excessive quantities of magic occurring here
        if mode[0] in ("l", "r"):
            for i in range(x * y):
                images_stacked[i // x if mode[1] == "d" else y - i // x - 1][
                    i % x if mode[0] == "r" else x - i % x - 1
                ] = images[i]
        elif mode[0] in ("u", "d"):
            for i in range(x * y):
                images_stacked[i % y if mode[0] == "d" else y - i % y - 1][
                    i // y if mode[1] == "r" else x - i // y - 1
                ] = images[i]
        image_data.images = [
            np.concatenate(
                tuple([np.concatenate(tuple(row), axis=1) for row in images_stacked]),
                axis=0,
            )
        ]
        return image_data


class GenericImageIterator:
    def __init__(self, stacking: Stacking = Stacking.default()):
        """
        Samples filtered images from the provided directories in order of appearance.
        Pass in paths to directories containing images, and extension
        of desired image inputs. Will return as many images as needed to fill the stacking.
        May sample unevenly.

        :param directories: Input directories.
        :param exts:        Extension(s) of file to return
        :param num:         Number of images to return each iteration.
        """
        self.transforms: List[Transform] = [stacking]
        self._max_iters = 0
        self._num_iters = 0

    def _name_file(self):
        return str(self._num_iters), None

    def _replace_transform(self, transform: Transform):
        target_ind = find(self.transforms, lambda x: isinstance(x, transform.__class__))
        if target_ind is not None:
            self.transforms[target_ind] = transform
        else:
            self.transforms.append(transform)

    def resize_in(self, dims: Tuple[int, int]):
        if type(self.transforms[0]) not in {Resize, ResizeAll}:
            self.transforms.insert(0, ResizeAll(dims))
        else:
            self.transforms[0] = ResizeAll(dims)
        return self

    def resize_individual(self, resize: Resize):
        if type(self.transforms[0]) not in {Resize, ResizeAll}:
            self.transforms.insert(0, resize)
        else:
            self.transforms[0] = resize
        return self

    def skip(self, items: int):
        raise NotImplementedError()

    def take(self, count: int):
        """
        Sets the number of files that this iterator will output:
        If items <= 0, nothing will be returned. If max_iters >= self.items, self.max_iters remains unchanged.
        Otherwise, self.max_iters = max_iters

        :param count:   The maximum number of iterations that should occur.
        :return:
        """

        self._max_iters = count
        return self

    def chain(self, iterator):
        return ChainIterator([self, iterator])

    def size(self) -> Optional[Tuple[int, int]]:
        stacking_index = find(self.transforms, lambda t: isinstance(t, Stacking))
        stacking = self.transforms[stacking_index]
        index = find(self.transforms, lambda t: isinstance(t, ResizeAll))
        if index is not None:
            dims = self.transforms[index].dims
            return dims[0] * stacking.cols, dims[1] * stacking.rows
        return None

    def choose_padding(self) -> int:
        """
        Chooses the minimum padding to ensure that counter filenames are equal in length.
        :return:
        """
        return len(str(self._max_iters - 1))

    def write_images(
        self,
        dir: str = "./",
        prefix: str = "",
        ext: Optional[str] = None,
        pad: Optional[int] = None,
    ):
        """
        Takes all the images generated by `self` and writes them to their specified file path.
        If no extension is provided, defaults to image file extension, and then to .jpg
        Use self.choose_padding() to ensure that filenames generated through a counter (eg. "0", "1", ...),
        are padded to the same length.

        :param dir:     The target directory
        :param prefix:  A filename prefix
        :param ext:     The desired output extension
        :param pad:     Number of letters to pad the filename with
        :return:
        """
        if ext:
            ext = fo.prepend_dot(ext)

        for image_data in self:
            file_name = image_data.file_name.zfill(pad) if pad else image_data.file_name
            path = (Path(dir) / (prefix + file_name)).with_suffix(
                ext or image_data.ext or ".jpg"
            )
            path.parent.mkdir(exist_ok=True)
            cv2.imwrite(str(path), image_data.images[0])

    def write_video(self, path: str, video_format: str = "mp4v", fps: float = 24.0):
        if self.size() is None:
            raise ValueError(
                f"{self.__class__.__name__} must be initialized with .resize_in() or .resize_out() before calling .write_video()"
            )

        supported_extensions = [".mp4"]
        if Path(path).suffix.lower() not in supported_extensions:
            raise ValueError(
                "Extension %s is not currently supported."
                % (Path(path).suffix.lower(),)
            )

        video_format = cv2.VideoWriter_fourcc(*video_format)
        # apiPreference may be required depending on cv2 version.

        vid = cv2.VideoWriter(
            filename=path,
            apiPreference=0,
            fourcc=video_format,
            fps=fps,
            frameSize=self.size(),
        )

        for image_data in self:
            vid.write(image_data.images[0])
        vid.release()

    def __iter__(self):
        return self

    def __next__(self):
        raise NotImplementedError()

    def _apply_transforms(self, images: ImageDataStore):
        for transform in self.transforms:
            images = transform.apply(images)
        return images


class ChainIterator(GenericImageIterator):
    def __init__(self, iterators: List[GenericImageIterator]):
        super().__init__()
        self.iterators = iterators[::-1]
        self._max_iters = sum(it._max_iters for it in self.iterators)
        self.num_iterators = len(self.iterators)

    def skip(self, items: int):
        while self.iterators and items > 0:
            last = self.iterators[-1]
            if last._max_iters > items:
                items -= last._max_iters
                self.iterators.pop()
            else:
                last.skip(items)
                break

    def chain(self, iterator: GenericImageIterator):
        self.iterators.insert(0, iterator)
        self._max_iters += iterator._max_iters
        self.num_iterators += 1
        return self

    def _name_file(self):
        return str(self._num_iters), None

    def __next__(self):
        while self.iterators:
            try:
                image_data = next(self.iterators[-1])
                image_data = self._apply_transforms(image_data)
                image_data.file_name = (
                    f"{self.num_iterators - len(self.iterators)}_{image_data.file_name}"
                )
                self._num_iters += 1
                return image_data
            except StopIteration:
                self._num_iters -= 1
                self.iterators.pop()
        raise StopIteration


class FileIterator(GenericImageIterator):
    """
    Combines images in order of appearance in each of the provided lists of paths
    """

    def __init__(
        self,
        paths: Union[List[str], List[List[str]]],
        stacking: Stacking = None,
    ):
        if paths and isinstance(paths[0], str):
            paths = [paths]

        super().__init__(stacking=stacking or Stacking(len(paths), 1, "rd"))

        if not all(fo.check_files_exist(paths_) for paths_ in paths):
            raise ValueError("One or more files not found.")

        self.files = [SkipIterator(paths_) for paths_ in paths]
        self._max_iters = max(len(paths_) for paths_ in paths)

        num_images = stacking.cols * stacking.rows
        if num_images != len(paths):
            raise ValueError(
                f"Number of file lists provided ({len(paths)}) does not match number required to fill frame ({num_images} file lists required)"
            )

    def skip(self, count: int):
        for files in self.files:
            files.skip(count)
        return self

    def __next__(self):
        """Returns num images in an array."""
        if self._num_iters >= self._max_iters:
            raise StopIteration()

        output = [cv2.imread(next(files)) for files in self.files]
        name, ext = self._name_file()
        images = ImageDataStore(output, name, ext)
        self._num_iters += 1

        return self._apply_transforms(images)


class DirectoryIterator(FileIterator):
    """
    Combines images in order of appearance in each of the provided directories
    """

    def __init__(
        self, directories, exts=("jpg",), stacking: Stacking = Stacking.default()
    ):
        if isinstance(directories, str):
            directories = [directories]
        if not directories:
            raise ValueError("No directories provided.")

        if not fo.check_dirs_exist(directories):
            raise ValueError("One or more provided directories do not exist.")

        num_images = stacking.cols * stacking.rows
        if num_images != len(directories):
            raise ValueError(
                f"Number of directories provided ({len(directories)}) does not match number required to fill frame ({num_images} directories required)"
            )

        super().__init__(self._load_dirs(directories, exts), stacking)

    def _load_dirs(self, directories: List[str], exts: List[str]):
        files = []
        for directory in directories:
            files.append(fo.get_files(directory, exts))
            if len(files[-1]) == 0:
                raise ValueError(
                    f"No images matching ext {', '.join(exts)} found in {directory}"
                )
        return files


class DirectoryIteratorMatchNames(DirectoryIterator):
    """
    Produces images ordered lexographically by filename, where each image consists of images with matching filenames
    in each of the provided directories.
    """

    def _load_dir(self, directory: str, exts: List[str]):
        files = fo.get_files(directory, exts)

        if not files:
            raise ValueError(f"No files found in {directory}")

        return {os.path.basename(f_name): f_name for f_name in files}

    def _load_dirs(self, directories: List[str], exts: List[str]):
        """Finds and stores all file names which exist across all directories."""
        possible_file_names = set()
        candidates = []
        for i, directory in enumerate(directories):
            files = self._load_dir(directory, exts)
            if i == 0:
                possible_file_names = set(files.keys())
            else:
                possible_file_names &= set(files.keys())

            if not possible_file_names:
                raise ValueError("No file names in common.")

            candidates.append(files)

        common_files = sorted(list(possible_file_names))
        return [
            SkipIterator([candidate[common_file] for common_file in common_files])
            for candidate in candidates
        ]

    def _name_file(self):
        path = Path(self.files[0][self._num_iters])
        return path.stem, path.suffix


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
    stacking: Stacking = Stacking.default(),
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

    if isinstance(files_in, str):
        files_in = [files_in]

    images = [cv2.imread(file) for file in files_in]
    cv2.imwrite(file_name, stacking.apply(resize_images(images, size)))


def dimensions(files: Union[List[str], str]):
    """
    Returns the appropriate dimensions given resize.
    :param files:    One or more files with dimensions of interest
    :return:
    """
    if isinstance(files, str):
        files = [files]

    for file in files:
        ext = Path(file).suffix.lstrip(".")
        ext_cat = fo.FileCategory.from_str(ext)
        if ext_cat == fo.FileCategory.IMAGE:
            yield get_img_dimensions(file)
        else:
            yield get_video_dimensions(file)


def get_dimensions_dirs(
    dirs_in: Union[List[str], str], exts: Union[List[str], str], resize: Resize
):
    """
    Returns the appropriate dimensions given resize.
    :param dirs_in:     One or more directories with files of interest
    :param exts:        The file extension(s).
    :param resize:      A Resize enum.
    :return:
    """
    if isinstance(dirs_in, str):
        dirs_in = [dirs_in]

    def dimension_generator():
        for dir_in in dirs_in:
            try:
                yield resize.choose(dimensions(fo.get_files(dir_in, exts)))
            except ValueError:
                continue

    try:
        return resize.choose(dimension_generator())
    except ValueError:
        if isinstance(exts, str):
            exts = [exts]
        raise ValueError(
            "No files with given extension(s) %s found in any directory."
            % (", ".join(exts),)
        )


def get_img_dimensions(img: str):
    """
    Given a list of file paths, returns the dimensions of the images corresponding to the file paths
    :param img:         File path pointing to image file.
    :return:            List of corresponding file dimensions.
    """
    file = cv2.imread(img)
    return file.shape[1], file.shape[0]


def get_video_dimensions(video: str):
    """
    Given a list of file paths, returns the dimensions of the videos corresponding to the file paths.

    :param video:       File path pointing to video file.
    :return:            List of corresponding file dimensions.
    """
    file = cv2.VideoCapture(video)
    dims = (
        int(file.get(cv2.CAP_PROP_FRAME_WIDTH)),
        int(file.get(cv2.CAP_PROP_FRAME_HEIGHT)),
    )
    file.release()
    return dims


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
