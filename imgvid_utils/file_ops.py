import enum
import os
import glob

from typing import Union, List


def is_file(file: str) -> bool:
    return os.path.exists(file) and os.path.isfile(file)


def get_missing_files(files: Union[str, List[str]]) -> List[str]:
    """
    Returns all missing files.

    :param files: one or more files to check.
    :return:
    """
    if isinstance(files, str):
        return [] if is_file(files) else [files]

    return [file for file in files if not is_file(file)]


def check_files_exist(files: Union[str, List[str]]) -> bool:
    """
    Returns true if all files exist, otherwise false.

    :param files: one or more files to check.
    :return:
    """
    if isinstance(files, str):
        return is_file(files)

    return all((is_file(file) for file in files))


def is_dir(directory: str) -> bool:
    return os.path.exists(directory) and os.path.isdir(directory)


def get_missing_dirs(directories: Union[str, List[str]]) -> List[str]:
    """
    Returns all directories from directories which don't exist.

    :param directories: one or more directories to check.
    :return:
    """
    if isinstance(directories, str):
        return [] if is_dir(directories) else [directories]

    return [directory for directory in directories if not is_dir(directory)]


def check_dirs_exist(directories: Union[str, List[str]]) -> bool:
    """
    Returns true if all directories exist, otherwise false.

    :param      directories: one or more directories to check.
    :return:
    """
    if isinstance(directories, str):
        return is_dir(directories)

    return all((is_dir(directory) for directory in directories))


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


def get_files(directory: str, ext: Union[List[str], str]) -> List[str]:
    """
    Returns a list of file names in the given directory ending in the given extensions

    :param directory:   one or more directories to search.
    :param ext:         one or more extensions to match.
    :return:
    """
    jpg_subset = [".jpeg", ".jpg"]
    png_subset = [".png"]
    if ext is None:
        ext = jpg_subset + png_subset
    elif isinstance(ext, str):
        if "jpg" in ext.lower():
            ext = jpg_subset
        elif "png" in ext.lower():
            ext = png_subset
        elif "mp4" in ext.lower():
            ext = [".mp4", ".MP4"]
        else:
            ext = [ext]
    else:
        ext = ext

    extensions = [prepend_dot(extx) for extx in ext]
    directory = append_forward_slash_path(directory)
    frames = {
        frame
        for ext1 in extensions
        for frame in glob.glob(f"{directory}*{match_all_cases(ext1)}")
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
    dirs = []
    for directory in directories:
        dirs.append(get_files(append_forward_slash_path(directory), ext))
    dir_exhausted = [False] * len(dirs)

    curr_dir = 0
    curr_index = 0
    output = []
    while len(output) < num:
        # Directory has no images left
        if curr_index >= len(dirs[curr_dir]):
            # Given directory is "exhausted": no images left
            dir_exhausted[curr_dir] = True
            # All directories are exhausted.
            if all(dir_exhausted):
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
    return ("." if ext[0] != "." else "") + ext


def append_forward_slash_path(
    paths: Union[List[str], str]
) -> Union[List[str], str, None]:
    """
    Returns the input string(s), in the same format as they were passed in, with a minimum of one forward slash
    at the end, given that no forward slash exists at the end.

    :param paths: one or more paths to add a forward slash to.
    :return:
    """
    if paths is None:
        return None
    if isinstance(paths, str):
        if paths[-1] != "/":
            paths += "/"
        return paths
    else:
        output = [path + ("/" if path[-1] != "/" else "") for path in paths]
        return output


def clear_files(folder: str, *argv) -> None:
    """
    Clears the given folder of any and all files that match any extension provided.
    :param folder: folder to remove extensions from.
    :param argv: one or more extensions.
    :return:
    """
    folder = append_forward_slash_path(folder)
    for ext in argv:
        for f in glob.glob(os.path.join(folder) + "*" + prepend_dot(ext)):
            os.remove(f)


def form_file_name(dir_out: str, file_name: str, ext: str) -> str:
    """
    Removes excess extensions in the file_name and returns a fully formed file name, cleaned of excess extensions.
    :param dir_out:     path to a directory.
    :param file_name:   A file name with zero or more extensions.
    :param ext:         the file extension
    :return:
    """
    split_name = os.path.splitext(file_name)
    return os.path.join(dir_out, split_name[0] + prepend_dot(ext))


def get_ext(file):
    """
    Returns the file extension without any precending dots.
    :param file:    The file from which to get the extension.
    :return:
    """
    return os.path.splitext(file)[1][1:]


class FileCategory(enum.Enum):
    VIDEO = 0
    IMAGE = 1

    @classmethod
    def from_str(cls, s: str) -> "Self":
        return {"mp4": cls.VIDEO, "png": cls.IMAGE, "jpg": cls.IMAGE}[s]


def has_video_exts(exts):
    video_exts = {"mp4"}
    if isinstance(exts, str):
        return exts in video_exts
    return bool(set(exts).intersection(video_exts))


def has_image_exts(exts):
    image_exts = {"png", "jpg"}
    if isinstance(exts, str):
        return exts in image_exts
    return bool(set(exts).intersection(image_exts))
