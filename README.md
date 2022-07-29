# imgvid_utils

This repository is intended to provide useful functions for concatenating, stacking, and splitting images and video files.

The CLI provides access to these functions:
Stacking images vertically:
```
python -m imgvid_utils --vstack image1.jpg image2.jpg --name output.png
```

Stacking images horizontally:
```
python -m imgvid_utils --hstack image1.jpg image2.jpg --name output.png
```

Stacking images in an arbitrary fashion:
```
python -m imgvid_utils --files_in image1.jpg .. image25.jpg --rows 5 --cols 5 --name output.png
```

Stacking images in an arbitrary fashion from many directories:
```
python -m imgvid_utils --dirs_in dir1 ... dir25 --rows 5 --cols 5 --name output.png --to_imgs
```

Stacking videos in an arbitrary fashion from many source files:
```
python -m imgvid_utils --files_in video1.mp4 ... video25.mp4 --rows 5 --cols 5 --name output.mp4 --to_vid
```

Stacking videos in an arbitrary fashion from many directories:
```
python -m imgvid_utils --dirs_in dir1 ... dir25 rows 5 --cols 5 --name output.mp4 --to_vid
```

Splitting videos into component frames:
```
python -m imgvid_utils --files_in video1 --name output.png --to_imgs
```

Finding images with matching file names and concatenating them:
```
python -m imgvid_utils --dirs_in dir1 dir2 --read_matching_file_names
```

## Examples

### Defining a stacking
```python
from imgvid_utils.image import Stacking

stacking = Stacking(2, 2, "rd")
```

This stacking has 2 columns, 2 rows, and will stack images to the right and downwards.

### Stacking images in an arbitrary fashion:
```
python -m imgvid_utils --files_in image1.jpg .. image25.jpg --rows 5 --cols 5 --name output.png
```

### Using the API

imgvid_utils provides a flexible API based on frame sources and sinks.

### Defining frame sources

```python
from imgvid_utils import image as ims
from imgvid_utils import video as vs

# Groups the images by order of appearance in the provided lists
ims.FileIterator(
    [["file1.png", "file2.jpg", "file3.png"], ["file1.jpg", "file2.png", ...], ...],
    stacking=ims.Stacking(1, 2, "rd")
)

# Groups images by order of appearance in the provided directories
ims.DirectoryIterator(
    ["./path_to_first_directory", "./path_to_second_directory"],
    stacking=ims.Stacking(1, 2, "rd")
)

# A variant of DirectoryIterator which groups images with matching file names
# Output images are returned in lexographical order
ims.DirectoryIteratorMatchNames(
    ["./path_to_first_directory", "./path_to_second_directory"],
    stacking=ims.Stacking(1, 2, "rd")
)

# Groups the nth frame in each video
vs.VideoIterator(
    ["video1.mp4", "video2.mp4"],
    stacking=ims.Stacking(1, 2, "rd"),
)
```

### Resizing all input frames
```python
source.resize_in((640, 480))
```

### Resizing input frames on an individual basis
```python
source.resize(ims.Resize.FIRST)
# Choices are
# Resize.FIRST: Chooses the first set of dimensions
# Resize.UP: Chooses the dimensions with the largest area
# Resize.DOWN: Chooses the dimensions with the smallest area
```

### Controlling which frames are selected
```python
# Skips the first 10 frames of input, and output only 10 frames
source.skip(10).take(10)
```

### Chaining iterators:
```python
# Note: Resize transformations should only be applied once to avoid resizing artifacts
source = source1.chain(source2).resize(resize)
```

### Creating output
#### Writing files to a target directory
```python
source.write_images("output_dir", "prefix", "extension", self.choose_padding())
```

#### Writing files to a video
```python
### Requires source.resize_in() to be called first
source.write_video("path/to/video.mp4", video_format="mp4v", fps=24.0)
```

#### Processing images manually
```python
for image_data in source:
    file_name = image_data.file_name
    ext = image_data.ext
    image = image_data.images[0]
    do_something(file_name, ext, image)
```
