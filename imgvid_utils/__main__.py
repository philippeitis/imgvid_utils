def get_correct_dimensions_vstack(args):
    if args.resize_in:
        return args.resize_in
    elif args.resize_out:
        image_width, image_height = args.resize_out
        if args.vstack and image_height % len(args.vstack) != 0:
            raise EnvironmentError(
                "Output height must be a multiple of image stacking number."
            )
        if args.hstack and image_width % len(args.hstack) != 0:
            raise EnvironmentError(
                "Output width must be a multiple of image stacking number."
            )
        cols = len(args.hstack) if args.hstack else 1
        rows = len(args.vstack) if args.vstack else 1
        return image_width // cols, image_height // rows

    return ims.get_dimensions_files(
        args.vstack or args.hstack, args.ext_in, ap.get_resize_enum(args)
    )


def get_correct_dimensions(args):
    if args.resize_in:
        return args.resize_in
    elif args.resize_out:
        image_width, image_height = args.resize_out
        if image_width % args.cols != 0:
            raise EnvironmentError(
                "Output width must be a multiple of image stacking number."
            )
        if image_height % args.rows != 0:
            raise EnvironmentError(
                "Output height must be a multiple of image stacking number."
            )
        return image_width // args.cols, image_height // args.rows

    if args.dirs_in:
        return ims.get_dimensions_dirs(
            args.dirs_in, args.ext_in, ap.get_resize_enum(args)
        )
    else:
        return ims.get_dimensions_files(
            args.files_in, args.ext_in, ap.get_resize_enum(args)
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

    if args.vstack or args.hstack:
        files = args.vstack or args.hstack
        ims.make_image_from_images(
            files,
            os.path.dirname(args.dest) or "./",
            os.path.basename(args.dest),
            fo.get_ext(args.dest),
            stacking=stacking,
            size=get_correct_dimensions_vstack(args),
        )
        exit()

    os.makedirs(os.path.dirname(args.dir_out), exist_ok=True)

    if args.read_matching_file_names:
        size = (None, None)
        if args.resize_in:
            size = args.resize_in
        elif args.resize_out:
            size = args.resize_out
        ims.make_images_from_folders_match(
            args.dirs_in,
            args.dir_out,
            args.max_imgs,
            stacking,
            ap.get_resize_enum(args),
            size,
        )
        exit()

    size = get_correct_dimensions(args)

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
                    args.ext_out,
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
