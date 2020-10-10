import os
import numbers

from . import file_ops as fo
from . import imagestacker as ims


def parse_arguments():
    import argparse

    parser_x = argparse.ArgumentParser()
    parser_y = parser_x.add_mutually_exclusive_group()
    lazy_parser = parser_y.add_argument_group()
    lazy_choices = lazy_parser.add_mutually_exclusive_group()

    lazy_choices.add_argument(
        "--vstack",
        nargs="+",
        type=str,
        help="List any images you want to stack vertically"
    )

    lazy_choices.add_argument(
        "--hstack",
        nargs="+",
        type=str,
        help="List any images you want to stack horizontally"
    )

    parser = parser_y.add_argument_group()
    # TODO: excess images in directory? Insufficient images in directory?

    sources = parser.add_mutually_exclusive_group()

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
        default=None,
        help="Outputs file with given extension."
             " Overridden by --to_vid, --to_img, --to_imgs, and set from --name by default.",
    )

    parser.add_argument(
        "--dir_out",
        dest="dir_out",
        type=str,
        default=None,
        help="Output directory. Set from --name by default.",
    )

    parser.add_argument(
        "--name",
        dest="name",
        type=str,
        default="./output/file.jpg",
        help="File name. Sets --dir_out and --ext_out if not already specified.",
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

    resize = parser.add_mutually_exclusive_group()
    resize.add_argument(
        "--resize_in",
        dest="resize_in",
        nargs=2,
        type=int,
        help="Sets the dimensions of the input image. "
             "Not compatible with -resize_out or -resize_down or -resize_up",
    )
    resize.add_argument(
        "--resize_out",
        dest="resize_out",
        nargs=2,
        type=int,
        help="Sets the dimensions of the output image. "
             "Not compatible with -resize_in or -resize_down or -resize_up",
    )

    resize.add_argument(
        "--resize",
        dest="resize",
        choices=[val for val in ims.Resize],
        type=get_resize_enum,
        default="first",
        help="Resizes the images according to the choice. "
             "down resizes each image to the smallest image. "
             "up resizes each image to the largest image. "
             "first resizes each image to the first image seen."
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

    return validate_arguments(parser_x)


def mixed_ext(exts):
    return fo.has_image_exts(exts) and fo.has_video_exts(exts)


# Checks if the extensions are equivalent.
def check_ext(ext1: str, ext2: str):
    """
    Checks if the ext1 is equivalent to ext2

    :param ext1:
    :param ext2:
    :return:
    """
    ext1 = ext1.lower().strip(".")
    ext2 = ext2.lower().strip(".")
    return not mixed_ext([ext1, ext2])


# Assumes args has resize_up, resize_down, and resize_first
def get_resize_enum(s) -> ims.Resize:
    """
    Identifies which option has been selected.

    :param s:
    :return:
    """
    if s == "up":
        return ims.Resize.UP

    if s == "down":
        return ims.Resize.DOWN

    if s == "first":
        return ims.Resize.FIRST

    return ims.Resize.NONE


class IsPlural:
    def __init__(self, pl):
        if hasattr(pl, "__len__") and (not isinstance(pl, str)):
            self.is_plural = len(pl) != 1
        elif isinstance(pl, numbers.Number):
            self.is_plural = abs(pl) != 1
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


def validate_lazy_arguments(parser, args) -> bool:
    """
    Checks that the arguments for lazy image manipulation are correct.

    :param parser:
    :param args:
    :return:        A boolean indicating whether lazy arguments exist.
    """
    if args.vstack or args.hstack:
        args.files_in = args.vstack or args.hstack
        args.vstack = bool(args.vstack)
        args.hstack = bool(args.hstack)

        args.cols, args.rows = (len(args.files_in), 1) if args.hstack else (1, len(args.files_in))
        missing_files = fo.get_missing_files(args.files_in)

        if len(missing_files) != 0:
            pl = IsPlural(missing_files)
            dir_str = PluralizableString("file", "", "s", pl)
            do_str = PluralizableString("do", "es", "", pl)
            parser.error(
                "The %s specified at %s %s not exist."
                % (dir_str, ", ".join(missing_files), do_str)
            )
        return True
    return False


def validate_dirs(parser, args) -> bool:
    if args.dirs_in:
        if args.to_imgs and not args.ext_in:
            parser.error("No extension specified for images.")
        missing_dirs = fo.get_missing_dirs(args.dirs_in)
        if len(missing_dirs) != 0:
            pl = IsPlural(missing_dirs)
            dir_str = PluralizableString("director", "y", "ies", pl)
            do_str = PluralizableString("do", "es", "", pl)
            parser.error(
                "The %s specified at %s %s not exist."
                % (dir_str, ", ".join(missing_dirs), do_str)
            )
        return True
    return False


def validate_files(parser, args) -> bool:
    if args.files_in:
        if len(args.files_in) < args.cols * args.rows:
            parser.error(
                "Not enough photos given to generate an image or video of dimensions %d by %d (requires %d images or "
                "videos, %d given)"
                % (args.cols, args.rows, args.cols * args.rows, len(args.files_in))
            )

        first_ext = os.path.splitext(args.files_in[0])
        for path in args.files_in:
            if not os.path.exists(path):
                parser.error("File %s not found." % path)
            if not check_ext(first_ext[1], os.path.splitext(path)[1]):
                parser.error("Video and image files can not be included.")

        missing_files = fo.get_missing_files(args.files_in)
        if len(missing_files) != 0:
            file_str = PluralizableString("file", "", "s", IsPlural(missing_files))
            parser.error(
                "The %s specified at %s does not exist."
                % (file_str, ", ".join(missing_files))
            )
        return True
    return False


def validate_extensions(parser, args):
    """
    Validate that the extensions provided are correct.

    :param parser:
    :param args:
    :return:
    """
    if mixed_ext(args.ext_in):
        parser.error("Must have exclusively image or video extensions.")

    if fo.has_video_exts(args.ext_in):
        if args.to_imgs:
            parser.error("Can not select --to_imgs and have videos in ext in")
        args.to_vid = True

    if args.to_vid:
        if args.ext_out not in ["mp4"]:
            args.ext_out = "mp4"
            print("Output extension automatically set to %s." % args.ext_out)


def validate_arguments(parser):
    """
    Checks that all file paths are correct and that no conflicting variables exist.

    :param parser:  An argparse.ArgumentParser object.
    :return:        A set of parsed and valid arguments.
    """

    args = parser.parse_args()
    args.dir_out = args.dir_out or os.path.dirname(args.name)
    args.dir_out = fo.append_forward_slash_path(args.dir_out)
    args.ext_out = args.ext_out or fo.get_ext(args.name)
    args.name = ".".join(os.path.splitext(os.path.basename(args.name))[:-1])

    if validate_lazy_arguments(parser, args):
        return args

    if not validate_dirs(parser, args):
        validate_files(parser, args)

    validate_extensions(parser, args)

    if args.read_matching_file_names:
        if not args.dirs_in:
            parser.error("--read_matching_file_names requires --dirs_in to be specified.")
        if args.cols * args.rows != len(args.dirs_in):
            parser.error(f"Provided --dirs_in of {len(args.dirs_in)} directories and output stacking"
                         f" of {args.cols} by {args.rows} images are not compatible.")

    return args
