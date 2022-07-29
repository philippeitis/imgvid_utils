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
        return ims.get_dimensions_dirs(args.dirs_in, args.ext_in, args.resize)

    if not args.files_in:
        raise EnvironmentError("No files provided.")

    return args.resize.choose(ims.dimensions(args.files_in))


if __name__ == "__main__":
    from . import arg_parser as ap
    from . import video as vs
    from . import image as ims
    from . import file_ops as fo

    import os

    args = ap.parse_arguments()

    input_args = [args.dirs_in, args.ext_in] if args.dirs_in else [args.files_in]
    size = get_correct_dimensions(args)

    vargs = {
        "stacking": ims.Stacking(args.cols, args.rows, "rd"),
    }

    os.makedirs(os.path.dirname(args.dir_out), exist_ok=True)

    if args.read_matching_file_names:
        source = ims.DirectoryIteratorMatchNames(
            args.dirs_in, **vargs
        ).resize_individual(args.resize)
    elif args.dirs_in:
        if fo.has_image_exts(args.ext_in):
            source = ims.DirectoryIterator(
                args.dirs_in, args.ext_in, **vargs
            ).resize_in(size)
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
            source = vs.VideoIterator(files_in, **vargs).resize_in(size)
    else:
        if fo.has_image_exts(args.ext_in):
            source = ims.FileIterator(args.files_in, **vargs).resize_in(size)
        else:
            source = vs.VideoIterator(
                args.files_in, lock_framerate=not args.fps_unlock, **vargs
            ).resize_in(size)

    if args.max_imgs:
        source = source.take(args.max_imgs)

    print(
        "Output file will have dimensions: %d x %d px."
        % (size[0] * args.cols, size[1] * args.rows)
    )

    if args.to_imgs:
        source = source.rename(args.dir_out, args.name, args.ext_out)
        source.write_images()
    elif args.to_vid:
        source.write_video(
            fo.form_file_name(args.dir_out, args.name, args.ext_out), fps=args.fps
        )
    else:
        raise NotImplementedError()
