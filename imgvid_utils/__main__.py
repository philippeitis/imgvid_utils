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
        return image_width // args.cols, image_height // args.rows

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


if __name__ == "__main__":
    from . import arg_parser as ap
    from . import videostacker as vs
    from . import imagestacker as ims
    from . import file_ops as fo

    import os

    args = ap.parse_arguments()

    os.makedirs(os.path.dirname(args.dir_out), exist_ok=True)

    if args.read_matching_file_names:
        image_width, image_height = None, None
        if args.resize_in:
            image_width, image_height = args.resize_in
        elif args.resize_out:
            image_width, image_height = args.resize_out
        ims.make_images_from_folders_match(
            args.dirs_in,
            args.dir_out,
            args.max_imgs,
            args.cols,
            args.rows,
            ap.get_resize_enum(args),
            image_width,
            image_height,
        )
        exit()

    if args.vstack or args.hstack:
        files = args.vstack or args.hstack
        if args.vstack:
            cols = 1
            rows = len(args.vstack)
        else:
            cols = len(args.hstack)
            rows = 1

        image_width, image_height = get_correct_dimensions_vstack(args)
        ims.make_image_from_images(
            files,
            os.path.dirname(args.dest) or "./",
            os.path.basename(args.dest),
            fo.get_ext(args.dest),
            cols=cols,
            rows=rows,
            width=image_width,
            height=image_height,
        )
        exit()

    image_width, image_height = get_correct_dimensions(args)

    print(
        "Output file will have dimensions: %d x %d px."
        % (image_width * args.cols, image_height * args.rows,)
    )

    if args.to_vid:
        if args.dirs_in:
            if ap.has_image_exts(args.ext_in):
                vs.make_video_from_images(
                    args.dirs_in,
                    args.ext_in,
                    args.dir_out,
                    args.name,
                    args.ext_out,
                    cols=args.cols,
                    rows=args.rows,
                    width=image_width,
                    height=image_height,
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
                    cols=args.cols,
                    rows=args.rows,
                    width=image_width,
                    height=image_height,
                )

        elif args.files_in:
            vs.make_video_from_videos(
                args.files_in,
                args.dir_out,
                args.name,
                args.ext_out,
                cols=args.cols,
                rows=args.rows,
                width=image_width,
                height=image_height,
            )

    else:
        if args.files_in:
            ims.make_image_from_images(
                args.files_in,
                args.dir_out,
                args.name,
                args.ext_out,
                cols=args.cols,
                rows=args.rows,
                width=image_width,
                height=image_height,
            )
        else:
            ims.make_images_from_folders(
                args.dirs_in,
                args.ext_in,
                args.dir_out,
                args.name,
                ext_out=args.ext_out,
                max_imgs=args.max_imgs,
                rows=args.rows,
                cols=args.cols,
                width=image_width,
                height=image_height,
            )
