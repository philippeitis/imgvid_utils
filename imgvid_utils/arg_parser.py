import os
import numbers

from . import file_ops as fo
from . import image as ims


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
        help="List any images you want to stack vertically",
    )

    lazy_choices.add_argument(
        "--hstack",
        nargs="+",
        type=str,
        help="List any images you want to stack horizontally",
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
        "with --dirs_in.",
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
        choices=[ims.Resize.UP, ims.Resize.DOWN, ims.Resize.FIRST],
        type=get_resize_enum,
        default="first",
        help="Resizes the images according to the choice. "
        "down resizes each image to the smallest image. "
        "up resizes each image to the largest image. "
        "first resizes each image to the first image seen.",
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
        default=30.0,
        type=float,
        help="Frame rate of output video. Not compatible if videos are passed in.",
    )

    parser.add_argument(
        "--fps_unlock",
        dest="fps_unlock",
        action="store_true",
        help="Removes the requirement for input videos to have matching framerates. "
        "May cause issues with frames not matching up if framerates do not match.",
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


def mixed_ext(exts) -> bool:
    return fo.has_image_exts(exts) and fo.has_video_exts(exts)


# Assumes args has resize_up, resize_down, and resize_first
def get_resize_enum(s) -> ims.Resize:
    """
    Identifies which option has been selected.

    :param s:
    :return:
    """
    return {
        "up": ims.Resize.UP,
        "down": ims.Resize.DOWN,
        "first": ims.Resize.FIRST,
    }.get(s, ims.Resize.NONE)


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


def parse_lazy_arguments(args):
    """
    Checks that the arguments for lazy image manipulation are correct.

    :param args:
    :return:        A boolean indicating whether lazy arguments exist.
    """
    if not (args.vstack or args.hstack):
        return

    args.files_in = args.vstack or args.hstack
    args.vstack = bool(args.vstack)
    args.hstack = bool(args.hstack)
    args.cols, args.rows = (
        (len(args.files_in), 1) if args.hstack else (1, len(args.files_in))
    )


def validate_dirs(parser, args):
    if not args.dirs_in:
        return

    if args.to_imgs and not args.ext_in:
        parser.error("No extension specified for input images.")

    missing_dirs = fo.get_missing_dirs(args.dirs_in)

    if missing_dirs:
        pl = IsPlural(missing_dirs)
        dir_str = PluralizableString("director", "y", "ies", pl)
        do_str = PluralizableString("do", "es", "", pl)
        parser.error(
            "The %s specified at %s %s not exist."
            % (dir_str, ", ".join(missing_dirs), do_str)
        )


def validate_files(parser, args):
    if not args.files_in:
        return

    image_delta = len(args.files_in) - args.cols * args.rows

    if image_delta < 0:
        parser.error(
            "Not enough photos given to generate an image or video stacked %d by %d (requires %d images or "
            "videos, %d given)"
            % (args.cols, args.rows, args.cols * args.rows, len(args.files_in))
        )

    if image_delta > 0:
        print("Last %d files will not be included in output" % image_delta)

    missing_files = fo.get_missing_files(args.files_in)

    if missing_files:
        pl = IsPlural(missing_files)
        dir_str = PluralizableString("file", "", "s", pl)
        do_str = PluralizableString("do", "es", "", pl)
        parser.error(
            "The %s specified at %s %s not exist."
            % (dir_str, ", ".join(missing_files), do_str)
        )


def validate_extensions(parser, args):
    """
    Validate that the extensions provided are correct and are not mixed.

    :param parser:
    :param args:
    :return:
    """
    if args.files_in:
        args.ext_in = {fo.get_ext(file) for file in args.files_in}

    if mixed_ext(args.ext_in):
        parser.error("Must have exclusively images or videos as input.")

    if not args.dirs_in:
        return

    if args.to_vid and args.ext_out not in {"mp4"}:
        args.ext_out = "mp4"
        print("Output extension automatically set to %s." % args.ext_out)


def validate_arguments(parser):
    """
    Checks that all file paths are correct and that no conflicting variables exist.

    :param parser:  An argparse.ArgumentParser object.
    :return:        A set of parsed and valid arguments.
    """

    args = parser.parse_args()
    args.dir_out = args.dir_out or os.path.dirname(args.name) or "./"
    args.ext_out = args.ext_out or fo.get_ext(args.name)
    args.name = ".".join(os.path.splitext(os.path.basename(args.name))[:-1])

    parse_lazy_arguments(args)

    validate_extensions(parser, args)
    validate_dirs(parser, args)
    validate_files(parser, args)

    if args.read_matching_file_names:
        if not args.dirs_in:
            parser.error(
                "--read_matching_file_names requires --dirs_in to be specified."
            )
        if args.cols * args.rows != len(args.dirs_in):
            parser.error(
                f"Provided --dirs_in of {len(args.dirs_in)} directories and output stacking"
                f" of {args.cols} by {args.rows} images are not compatible."
            )

    return args
