import os
import numbers

from . import file_ops as fo
from . import imagestacker as ims


def parse_arguments():
    import argparse

    parser = argparse.ArgumentParser()
    # TODO: excess images in directory? Insufficient images in directory?
    parser.add_argument(
        "--dirs_in",
        dest="dirs_in",
        nargs="*",
        type=str,
        help="List any directories you want to use.",
    )
    parser.add_argument(
        "--files_in",
        dest="files_in",
        nargs="*",
        type=str,
        help="List any images or videos you want to use. Not compatible"
        "with -to_imgs, dirs_in. If -to_vid, must be videos.",
    )
    parser.add_argument(
        "--ext_in",
        dest="ext_in",
        type=str,
        choices=["png", "jpg", "mp4"],
        help="Will select files with given extension for input.",
    )
    parser.add_argument(
        "--ext_out",
        dest="ext_out",
        type=str,
        choices=["png", "jpg", "mp4"],
        help="Outputs file with given extension."
        " Overriden by -to_vid, -to_img, and -to_imgs",
    )
    parser.add_argument(
        "--dir_out",
        dest="dir_out",
        type=str,
        default="./output/",
        help="Output directory.",
    )
    parser.add_argument(
        "--name",
        dest="name",
        type=str,
        default="file",
        help="File name. Do not include in dir_out",
    )
    parser.add_argument(
        "--to_vid",
        dest="to_vid",
        action="store_true",
        help="Will output a video file (default 30fps, .mp4). Not compatible with --to_img."
        " If multiple directories are provided, will only use first x*y videos."
        " If one directory is provided, will use first x*y videos.",
    )
    parser.add_argument(
        "--to_img",
        dest="to_img",
        action="store_true",
        help="Will output an image file (default .jpg). Not compatible with --to_vid",
    )
    parser.add_argument(
        "--to_imgs",
        dest="to_imgs",
        action="store_true",
        help="Will output many image files (default .jpg)",
    )

    parser.add_argument(
        "--resize_in",
        dest="resize_in",
        nargs=2,
        type=int,
        help="Sets the dimensions of the input image. "
        "Not compatible with -resize_out or -resize_down or -resize_up",
    )
    parser.add_argument(
        "--resize_out",
        dest="resize_out",
        nargs=2,
        type=int,
        help="Sets the dimensions of the output image. "
        "Not compatible with -resize_in or -resize_down or -resize_up",
    )
    parser.add_argument(
        "--resize_up",
        dest="resize_up",
        action="store_true",
        help="Resizes all input images to the largest image in the set. "
        "Computed by area of image (eg. width * height). Will override --resize_in, --resize_out."
        " Not compatible with -resize_down, -resize_first.",
    )
    parser.add_argument(
        "--resize_down",
        dest="resize_down",
        action="store_true",
        help="Resizes all input images to the smallest image in the set. "
        "Computed by area of image (eg. width * height). Will override --resize_in, --resize_out."
        " Not compatible with --resize_up, --resize_first",
    )
    parser.add_argument(
        "--resize_first",
        dest="resize_first",
        action="store_true",
        help="Resizes all input images to first small image in the set. --resize_in, --resize_out. "
        " Not compatible with --resize_up, --resize_down.",
    )

    parser.add_argument(
        "--cols",
        dest="cols",
        type=int,
        default=1,
        help="Number of images or videos placed side by side, horizontally.",
    )
    parser.add_argument(
        "--rows",
        dest="rows",
        type=int,
        default=1,
        help="Number of images or videos stacked on top of each other," " vertically.",
    )

    parser.add_argument(
        "--fps",
        dest="fps",
        default=30,
        type=int,
        help="Frame rate of video. Not compatible if videos are passed in.",
    )
    parser.add_argument(
        "--max",
        dest="max_imgs",
        default=None,
        type=int,
        help="Maximum number of images to output (eg. if folder has 1000 images, output only 10.",
    )
    parser.add_argument(
        "--read_matching_file_names",
        action="store_true",
        help="Will concatenate files with the same name from each directory,"
        " and will resize on a per image basis unless a width and height are specified.",
    )

    args = parser.parse_args()
    args.dir_out = fo.append_forward_slash_path(args.dir_out)
    args.dirs_in = fo.append_forward_slash_path(args.dirs_in)
    validate_arguments(args)
    if args.ext_in == "mp4":
        args.to_vid = True
    # Set default extension if none given
    if args.ext_in is None and args.dirs_in is not None:
        args.ext_in = ["png", "jpg"]
        print("Input extension set to %s." % (",".join(args.ext_in),))

    if args.to_vid:
        if args.ext_out not in ["mp4"]:
            args.ext_out = "mp4"
            print("Output extension automatically set to %s." % args.ext_in)

    if args.ext_out is None:
        args.ext_out = "jpg"
        print("Output extension automatically set to %s." % args.ext_out)

    print(args)
    return args


def get_ext(args):
    if args.files_in is not None:
        ext_in = os.path.splitext(args.files_in[0])[1]
        return ext_in[1:]


# Checks if the extensions are equivalent.
def check_ext(ext1: str, ext2: str):
    if ext1.lower() == ext2.lower():
        return True
    elif ext1.lower() in [".png", ".jpg"] and ext2.lower() in [".png", ".jpg"]:
        return True
    else:
        return False


# Assumes args has resize_up, resize_down, and resize_first
def get_resize_enum(args):
    if args.resize_up:
        return ims.Resize.RESIZE_UP
    elif args.resize_down:
        return ims.Resize.RESIZE_DOWN
    elif args.resize_first:
        return ims.Resize.RESIZE_FIRST
    else:
        return ims.Resize.RESIZE_NONE


class IsPlural:
    def __init__(self, pl):
        if hasattr(pl, "__len__") and (not isinstance(pl, str)):
            self.is_plural = len(pl) > 1
        elif isinstance(pl, numbers.Number):
            self.is_plural = abs(pl) > 1
        else:
            self.is_plural = False


class PluralizableString:
    def __init__(
        self,
        base_string: str,
        non_plural_end: str,
        plural_end: str,
        pluralizable: IsPlural,
    ):
        self.text: str = base_string + (
            plural_end if pluralizable.is_plural else non_plural_end
        )

    def __repr__(self):
        return self.text


# Checks that all file paths are correct and that no conflicting variables exist.
def validate_arguments(args):
    if args.dirs_in is not None and args.files_in is not None:
        raise EnvironmentError("Can only specify -dirs_in or -files_in")
    if args.dirs_in is not None and (args.to_img or args.to_imgs) and not args.ext_in:
        raise EnvironmentError("No extension specified for images. ")
    if args.dirs_in is not None:
        missing_dirs = fo.check_dirs(args.dirs_in, return_missing=True)
        if len(missing_dirs) != 0:
            pl = IsPlural(missing_dirs)
            dir_str = PluralizableString("director", "y", "ies", pl)
            do_str = PluralizableString("do", "es", "", pl)
            raise EnvironmentError(
                "The %s specified at %s %s not exist."
                % (dir_str, ", ".join(missing_dirs), do_str)
            )

    if args.files_in is not None:
        if len(args.files_in) < args.cols * args.rows:
            raise EnvironmentError(
                "Not enough photos given to generate an image or video of dimensions %d by %d (requires %d images or "
                "videos, %d given)"
                % (args.cols, args.rows, args.cols * args.rows, len(args.files_in))
            )

        first_ext = os.path.splitext(args.files_in[0])
        for path in args.files_in:
            if not os.path.exists(path):
                raise EnvironmentError("File %s not found." % path)
            if not check_ext(first_ext[1], os.path.splitext(path)[1]):
                raise EnvironmentError("Video and image files can not be included.")

        missing_files = fo.check_files(args.files_in, return_missing=True)
        if len(missing_files) != 0:
            file_str = PluralizableString("file", "", "s", IsPlural(missing_files))
            raise EnvironmentError(
                "The %s specified at %s does not exist."
                % (file_str, ", ".join(missing_files))
            )

    if (
        (args.resize_up and args.resize_down)
        or (args.resize_up and args.resize_first)
        or (args.resize_first and args.resize_down)
    ):
        raise EnvironmentError(
            "Choose one of --resize_up, --resize_down, --resize_first."
        )
    if args.resize_in is not None and args.resize_out is not None:
        raise EnvironmentError("Choose one of --resize_in or --resize_out.")
    if (args.to_vid and args.to_img) or (args.to_img and args.to_imgs):
        raise EnvironmentError(
            "--to_img is not compatible with either --to_vid or --to_imgs."
        )
