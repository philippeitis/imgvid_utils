def validate_resize_out(cols, rows, dims):
    width, height = dims

    if width % cols != 0:
        raise EnvironmentError(
            "Output width must be a multiple of image stacking number."
        )

    if height % rows != 0:
        raise EnvironmentError(
            "Output height must be a multiple of image stacking number."
        )

    return width // cols, height // rows


def get_correct_dimensions(args):
    if args.resize_in:
        return args.resize_in

    if args.resize_out:
        if args.vstack or args.hstack:
            cols, rows = (len(args.hstack), 1) if args.hstack else (1, len(args.vstack))
        else:
            cols, rows = args.cols, args.rows
        return validate_resize_out(cols, rows, args.resize_out)

    if args.read_matching_file_names:
        return None

    if args.dirs_in:
        return ims.get_dimensions_dirs(
            args.dirs_in, args.ext_in, args.resize
        )

    files = (args.vstack or args.vstack) or args.files_in

    if not files:
        raise EnvironmentError(
            "No files provided."
        )
    return ims.get_dimensions_files(
        files, args.ext_in, args.resize
    )


def generate_stacking(args):
    if args.vstack:
        return ims.Stacking(1, len(args.vstack), "rd")
    elif args.hstack:
        return ims.Stacking(len(args.hstack), 1, "rd")
    return ims.Stacking(args.cols, args.rows, "rd")


if __name__ == "__main__":
    from . import arg_parser as ap
    from . import videostacker as vs
    from . import imagestacker as ims
    from . import file_ops as fo

    import os

    args = ap.parse_arguments()
    stacking = generate_stacking(args)

    size = get_correct_dimensions(args)

    if args.vstack or args.hstack:
        files = args.vstack or args.hstack
        ims.make_image_from_images(
            files,
            os.path.dirname(args.dest) or "./",
            os.path.basename(args.dest),
            fo.get_ext(args.dest),
            stacking=stacking,
            size=size,
        )
        exit()

    os.makedirs(os.path.dirname(args.dir_out), exist_ok=True)

    if args.read_matching_file_names:
        ims.make_images_from_folders_match(
            args.dirs_in,
            args.dir_out,
            args.max_imgs,
            stacking,
            args.resize,
            size,
        )
        exit()

    print(
        "Output file will have dimensions: %d x %d px."
        % (size[0] * args.cols, size[1] * args.rows,)
    )

    if args.to_vid:
        if args.dirs_in:
            if fo.has_image_exts(args.ext_in):
                if len(args.dirs_in) != args.cols * args.rows:
                    print("Images will not be drawn from the supplied directories evenly")
                vs.make_video_from_images(
                    args.dirs_in,
                    args.ext_in,
                    args.dir_out,
                    args.name,
                    ext_out=args.ext_out,
                    stacking=stacking,
                    size=size,
                    fps=args.fps,
                )
            else:
                files_in = fo.get_first_n_files(
                    args.dirs_in, args.ext_in, args.cols * args.rows
                )
                if len(files_in) != args.cols * args.rows:
                    raise ValueError(
                        "Insufficient files found in %s" % ", ".join(args.dirs_in)
                    )
                print(
                    "Automatically selected these video files to concatenate: %s"
                    % (", ".join(files_in))
                )
                vs.make_video_from_videos(
                    files_in,
                    args.dir_out,
                    args.name,
                    args.ext_out,
                    stacking=stacking,
                    size=size,
                )

        elif args.files_in:
            vs.make_video_from_videos(
                args.files_in,
                args.dir_out,
                args.name,
                args.ext_out,
                stacking=stacking,
                size=size,
            )

    else:
        if args.files_in:
            ims.make_image_from_images(
                args.files_in,
                args.dir_out,
                args.name,
                args.ext_out,
                stacking=stacking,
                size=size,
            )
        else:
            ims.make_images_from_folders(
                args.dirs_in,
                args.ext_in,
                args.dir_out,
                args.name,
                ext_out=args.ext_out,
                max_imgs=args.max_imgs,
                stacking=stacking,
                size=size,
            )
