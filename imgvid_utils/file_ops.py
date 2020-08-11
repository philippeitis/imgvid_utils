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

    :param directories: one or more directories to check.
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
    return "".join("[%s%s]" % (c.lower(), c.upper()) if c.isalpha() else c for c in strx)


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
        extensions = jpg_subset + png_subset
    elif isinstance(ext, str):
        if "jpg" in ext.lower():
            extensions = jpg_subset
        elif "png" in ext.lower():
            extensions = png_subset
        elif "mp4" in ext.lower():
            extensions = [".mp4", ".MP4"]
        else:
            extensions = [ext]
    else:
        extensions = ext

    extensions = [("." if extx[0] != "." else "") + extx for extx in extensions]
    directory = append_forward_slash_path(directory)
    frames = [
        frame for ext1 in extensions for frame in glob.glob(f"{directory}*{match_all_cases(ext1)}")
    ]

    return sorted(list(set(frames)))


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
        ext = ("." if ext[0] != "." else "") + ext
        for f in glob.glob(os.path.join(folder) + "*" + ext):
            os.remove(f)


def form_file_name(dir_out: str, file_name: str, ext: str) -> str:
    """
    Removes excess extensions in the file_name and returns a fully formed file name, cleaned of excess extensions.
    :param dir_out: path to a directory.
    :param file_name:  a file name with zero or more extensions.
    :param ext: the extension the file name should end in.
    :return:
    """
    # Needs to check that file_name doesn't contain an extension.
    split_name = os.path.splitext(file_name)
    ext = ("." if ext[0] != "." else "") + ext
    if len(split_name) > 1:
        file_name = ".".join(split_name[:-1])
    return os.path.join(dir_out, file_name + ext)
