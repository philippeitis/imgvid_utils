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
        return validate_resize_out(args.cols, args.rows, args.resize_out)

    if args.read_matching_file_names:
        return None

    if args.dirs_in:
        return ims.get_dimensions_dirs(
            args.dirs_in, args.ext_in, args.resize
        )

    if not args.files_in:
        raise EnvironmentError(
            "No files provided."
        )

    return ims.get_dimensions_files(
        args.files_in, args.ext_in, args.resize
    )


if __name__ == "__main__":
    from . import arg_parser as ap
    from . import videostacker as vs
    from . import imagestacker as ims
    from . import file_ops as fo

    import os

    args = ap.parse_arguments()

    input_args = [args.dirs_in, args.ext_in] if args.dirs_in else [args.files_in]
    output_args = [args.dir_out, args.name, args.ext_out]
    vargs = {
        "stacking": ims.Stacking(args.cols, args.rows, "rd"),
        "size": get_correct_dimensions(args)
    }

    os.makedirs(os.path.dirname(args.dir_out), exist_ok=True)

    if args.read_matching_file_names:
        ims.make_images_from_folders_match(
            args.dirs_in,
            args.dir_out,
            **vargs,
            resize_opt=args.resize,
            max_imgs=args.max_imgs,

        )
        exit()

    print(
        "Output file will have dimensions: %d x %d px."
        % (vargs["size"][0] * args.cols, vargs["size"][1] * args.rows)
    )

    if args.to_vid:
        if args.dirs_in:
            if fo.has_image_exts(args.ext_in):
                if len(args.dirs_in) != args.cols * args.rows:
                    print("Images will not be drawn from the supplied directories evenly")
                vs.make_video_from_folders(*input_args, *output_args, **vargs, fps=args.fps)
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
                vs.make_video_from_videos(files_in, *output_args, **vargs)
        else:
            vs.make_video_from_videos(*input_args, *output_args, **vargs)
    else:
        if args.files_in:
            ims.make_image_from_images(*input_args, *output_args, **vargs)
        else:
            ims.make_images_from_folders(*input_args, *output_args, **vargs, max_imgs=args.max_imgs)
