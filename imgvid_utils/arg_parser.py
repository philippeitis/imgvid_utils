import os
import numbers

from . import file_ops as fo
from . import imagestacker as ims


def parse_arguments():
    import argparse

    parser = argparse.ArgumentParser()
    # TODO: excess images in directory? Insufficient images in directory?

    sources = parser.add_mutually_exclusive_group(required=True)
    sources.add_argument(
        "--dirs_in",
        dest="dirs_in",
        nargs="+",
        type=str,
        help="List any directories you want to use.",
    )
    sources.add_argument(
        "--files_in",
        dest="files_in",
        nargs="+",
        type=str,
        help="List any images or videos you want to use. Not compatible"
             "with -to_imgs, dirs_in. If -to_vid, must be videos.",
    )

    parser.add_argument(
        "--ext_in",
        dest="ext_in",
        type=str,
        nargs="*",
        choices=["png", "jpg", "mp4"],
        default=["png", "jpg"],
        help="Will select files with given extension for input. Ignored if --files_in provided.",
    )

    parser.add_argument(
        "--ext_out",
        dest="ext_out",
        type=str,
        choices=["png", "jpg", "mp4"],
        default="jpg",
        help="Outputs file with given extension."
             " Overriden by --to_vid, --to_img, and --to_imgs",
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

    output_formats = parser.add_mutually_exclusive_group()

    # output_formats.add_argument(
    #     "--to_img",
    #     dest="to_img",
    #     action="store_true",
    #     help="Will output an image file (default .jpg). Not compatible with --to_vid",
    # )

    output_formats.add_argument(
        "--to_vid",
        dest="to_vid",
        action="store_true",
        help="Will output a video file (default 30fps, .mp4). Not compatible with --to_img."
             " If multiple directories are provided, will only use first x*y videos."
             " If one directory is provided, will use first x*y videos.",
    )

    output_formats.add_argument(
        "--to_imgs",
        dest="to_imgs",
        action="store_true",
        help="Will output many image files (default .jpg)",
    )

    resize_in_out = parser.add_mutually_exclusive_group()
    resize_in_out.add_argument(
        "--resize_in",
        dest="resize_in",
        nargs=2,
        type=int,
        help="Sets the dimensions of the input image. "
             "Not compatible with -resize_out or -resize_down or -resize_up",
    )
    resize_in_out.add_argument(
        "--resize_out",
        dest="resize_out",
        nargs=2,
        type=int,
        help="Sets the dimensions of the output image. "
             "Not compatible with -resize_in or -resize_down or -resize_up",
    )

    resize_opts = parser.add_mutually_exclusive_group()
    resize_opts.add_argument(
        "--resize_up",
        dest="resize_up",
        action="store_true",
        help="Resizes all input images to the largest image in the set. "
             "Computed by area of image (eg. width * height). Will override --resize_in, --resize_out."
             " Not compatible with -resize_down, -resize_first.",
    )
    resize_opts.add_argument(
        "--resize_down",
        dest="resize_down",
        action="store_true",
        help="Resizes all input images to the smallest image in the set. "
             "Computed by area of image (eg. width * height). Will override --resize_in, --resize_out."
             " Not compatible with --resize_up, --resize_first",
    )
    resize_opts.add_argument(
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

    if mixed_ext(args.ext_in):
        parser.error("Must have exclusively image or video extensions.")

    if has_video_exts(args.ext_in):
        if args.to_imgs:
            parser.error("Can not select --to_imgs and have videos in ext in")
        args.to_vid = True

    if args.to_vid:
        if args.ext_out not in ["mp4"]:
            args.ext_out = "mp4"
            print("Output extension automatically set to %s." % args.ext_in)

    if args.read_matching_file_names:
        if not args.dirs_in:
            parser.error("--read_matching_file_names requires --dirs_in to be specified.")
        if args.cols * args.rows != len(args.dirs_in):
            parser.error(f"Provided --dirs_in of {len(args.dirs_in)} directories and output stacking"
                         f" of {args.cols} by {args.rows} images are not compatible.")
    return args


def has_video_exts(exts):
    return bool(set(exts).intersection({"mp4"}))


def has_image_exts(exts):
    return bool(set(exts).intersection({"png", "jpg"}))


def mixed_ext(exts):
    return has_image_exts(exts) and has_video_exts(exts)


def get_ext(args):
    ext_in = os.path.splitext(args.files_in[0])[1]
    return ext_in[1:]


# Checks if the extensions are equivalent.
def check_ext(ext1: str, ext2: str):
    ext1 = ext1.lower().strip(".")
    ext2 = ext2.lower().strip(".")
    return mixed_ext([ext1, ext2])


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
    if args.dirs_in:
        if args.to_imgs and not args.ext_in:
            raise EnvironmentError("No extension specified for images.")
        missing_dirs = fo.get_missing_dirs(args.dirs_in)
        if len(missing_dirs) != 0:
            pl = IsPlural(missing_dirs)
            dir_str = PluralizableString("director", "y", "ies", pl)
            do_str = PluralizableString("do", "es", "", pl)
            raise EnvironmentError(
                "The %s specified at %s %s not exist."
                % (dir_str, ", ".join(missing_dirs), do_str)
            )

    if args.files_in:
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

        missing_files = fo.get_missing_files(args.files_in)
        if len(missing_files) != 0:
            file_str = PluralizableString("file", "", "s", IsPlural(missing_files))
            raise EnvironmentError(
                "The %s specified at %s does not exist."
                % (file_str, ", ".join(missing_files))
            )
