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
        image_width //= args.cols
        image_height //= args.rows
        return image_width, image_height

    if args.dirs_in is not None:
        return ims.get_dimensions_dirs(
            args.dirs_in, args.ext_in, ap.get_resize_enum(args)
        )
    else:
        return ims.get_dimensions_files(
            args.files_in, args.ext_in, ap.get_resize_enum(args)
        )


if __name__ == "__main__":
    import arg_parser as ap
    import videostacker as vs
    import imagestacker as ims
    import file_ops as fo

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

    image_width, image_height = get_correct_dimensions(args)

    print(
        "Output file will have dimensions: %d x %d px."
        % (image_width * args.cols, image_height * args.rows,)
    )

    if args.to_vid:
        print(args)
        if args.dirs_in is not None and args.ext_in not in ["mp4"]:
            vs.make_video_from_images(
                args.dirs_in,
                args.ext_in,
                args.dir_out,
                args.name,
                args.ext_out,
                fps=args.fps,
                cols=args.cols,
                rows=args.rows,
                width=image_width,
                height=image_height,
            )
        elif args.files_in is not None:
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

    else:
        if args.files_in is not None:
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
