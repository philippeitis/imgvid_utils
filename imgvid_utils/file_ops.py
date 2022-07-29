import enum
import glob
import os
from pathlib import Path

from typing import Union, List
from os.path import isdir, isfile


def append_forward_slash_path(path: str) -> str:
    """
    Appends a forward slash to the path if one is not present.
    :return:
    """
    return path if path[-1] == "/" else path + "/"


def get_missing_files(files: Union[str, List[str]]) -> List[str]:
    """
    Returns all missing files.

    :param files: one or more files to check.
    :return:
    """
    if isinstance(files, str):
        return [] if isfile(files) else [files]

    return [file for file in files if not isfile(file)]


def check_files_exist(files: Union[str, List[str]]) -> bool:
    """
    Returns true if all files exist, otherwise false.

    :param files: one or more files to check.
    :return:
    """
    if isinstance(files, str):
        return isfile(files)

    return all(isfile(file) for file in files)


def get_missing_dirs(directories: Union[str, List[str]]) -> List[str]:
    """
    Returns all directories from directories which don't exist.

    :param directories: one or more directories to check.
    :return:
    """
    if isinstance(directories, str):
        return [] if isdir(directories) else [directories]

    return [directory for directory in directories if not isdir(directory)]


def check_dirs_exist(directories: Union[str, List[str]]) -> bool:
    """
    Returns true if all directories exist, otherwise false.

    :param      directories: one or more directories to check.
    :return:
    """
    if isinstance(directories, str):
        return isdir(directories)

    return all(isdir(directory) for directory in directories)


def match_all_cases(strx: str):
    """
    Exists to provide compatibility for Unix systems.
    Source: https://stackoverflow.com/questions/8151300/ignore-case-in-glob-on-linux

    :param strx: Any string.
    :return:     Returns a regex which will match the same string.
    """
    return "".join(
        "[%s%s]" % (c.lower(), c.upper()) if c.isalpha() else c for c in strx
    )


def get_files(directory: str, extensions: Union[List[str], str]) -> List[str]:
    """
    Returns a list of file names in the given directory ending in the given extensions

    :param directory:   one or more directories to search.
    :param extensions:  one or more extensions to match.
    :return:
    """

    if isinstance(extensions, str):
        jpg_subset = [".jpeg", ".jpg"]
        extensions = {
            "jpg": jpg_subset,
            "jpeg": jpg_subset,
            "png": [".png"],
            "mp4": [".mp4"],
        }.get(extensions.lower().lstrip("."), [extensions])

    directory = append_forward_slash_path(directory)
    extensions = [prepend_dot(ext) for ext in extensions]
    frames = {
        file
        for ext in extensions
        # TODO: when Python min_ver is 3.10, use root_dir=directory
        for file in glob.glob(f"{directory}*{match_all_cases(ext)}")
    }

    return sorted(list(frames))


def get_first_n_files(
    directories: Union[List[str], str], ext: Union[List[str], str], num: int
) -> List[str]:
    """
    Returns the first n files in the directories that match the given extensions, as evenly as possible.
    In the event that less than num files exist, will return all matches found.

    :param directories: one or more directories to search.
    :param ext: one or more extensions to match.
    :param num: number of files that should be matched and returned.
    :return:
    """
    if not isinstance(directories, list):
        directories = [directories]
    dirs = [get_files(directory, ext) for directory in directories]

    exhausted_dirs = set()

    curr_dir = 0
    curr_index = 0
    output = []
    while len(output) < num:
        # Directory has no images left
        if curr_index >= len(dirs[curr_dir]):
            exhausted_dirs.add(curr_dir)
            # Given directory is "exhausted": no images left
            exhausted_dirs.add(curr_dir)
            # All directories are exhausted.
            if len(exhausted_dirs) == len(dirs):
                return output
        else:
            # Otherwise, append next image in directory.
            output.append(dirs[curr_dir][curr_index])
        # Move to next image in directory.
        curr_dir += 1
        if curr_dir % len(dirs) == 0:
            curr_index += 1
            curr_dir = 0
    return output


def prepend_dot(ext: str) -> str:
    return ext if ext[0] == "." else "." + ext


def clear_files(directory: str, *exts) -> None:
    """
    Clears the given folder of any and all files that match any extension provided.
    :param directory: folder to remove extensions from.
    :param exts: one or more extensions.
    :return:
    """
    directory = append_forward_slash_path(directory)
    for ext in exts:
        ext = prepend_dot(ext)
        # TODO: when Python min_ver is 3.10, use root_dir=directory
        for file in glob.glob(f"{directory}*{ext}"):
            os.remove(file)


def form_file_name(dir_out: str, file_name: str, ext: str) -> str:
    """
    Removes excess extensions in the file_name and returns a fully formed file name, cleaned of excess extensions.
    :param dir_out:     path to a directory.
    :param file_name:   A file name with zero or more extensions.
    :param ext:         the file extension
    :return:
    """
    return str((Path(dir_out) / file_name).with_suffix(prepend_dot(ext)))


def get_ext(file: str):
    """
    Returns the file extension without any preceding dots.
    :param file:    The file from which to get the extension.
    :return:
    """
    return Path(file).suffix.lstrip(".")


class FileCategory(enum.Enum):
    VIDEO = 0
    IMAGE = 1

    @classmethod
    def from_str(cls, s: str) -> "FileCategory":
        return {"mp4": cls.VIDEO, "png": cls.IMAGE, "jpg": cls.IMAGE}[s]


def has_video_exts(exts: Union[List[str], str]):
    video_exts = {"mp4"}
    if isinstance(exts, str):
        return exts in video_exts
    return bool(set(exts).intersection(video_exts))


def has_image_exts(exts: Union[List[str], str]):
    image_exts = {"png", "jpg"}
    if isinstance(exts, str):
        return exts in image_exts
    return bool(set(exts).intersection(image_exts))
