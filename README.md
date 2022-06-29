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
from imgvid_utils.imagestacker import Stacking

stacking = Stacking(2, 2, "rd")
```

This stacking has 2 columns, 2 rows, and will stack images to the right and downwards.

### Stacking images in an arbitrary fashion:
```
python -m imgvid_utils --files_in image1.jpg .. image25.jpg --rows 5 --cols 5 --name output.png
```

### Stacking images in an arbitrary fashion from many images
```python
from imgvid_utils import imagestacker

imagestacker.make_image_from_images(
    files_in,
    dir_out="./",
    file_name="output",
    ext_out="jpg",
    stacking=None,
    size=(640, 480),
)
```

### Stacking videos in an arbitrary fashion from many source directories with images
```python
from imgvid_utils import videostacker

videostacker.make_video_from_folders(
    dirs_in,
    ext_in="jpg",
    dir_out="./",
    file_name="output",
    ext_out="mp4",
    video_format="mp4v",
    fps=24,
    stacking=None,
    size=None,
)
```

### Stacking videos in an arbitrary fashion from many source images
```python
from imgvid_utils import videostacker

videostacker.make_video_from_images(
    files_in,
    dir_out="./",
    file_name="output",
    ext_out="mp4",
    video_format="mp4v",
    fps=24,
    size=None,
)
```

### Stacking videos in an arbitrary fashion from many source videos
```python
from imgvid_utils import videostacker

videostacker.make_video_from_videos(
    files_in,
    dir_out= "./",
    file_name="output",
    ext_out="mp4",
    video_format="mp4v",
    stacking=None,
    size=None,
    fps_lock=True,
)

```

### Splitting videos into component frames
```python
from imgvid_utils import videostacker

videostacker.split_video(
    file_in,
    dir_out,
    file_name="",
    ext_out="png",
    frame_count=-1,
    start_frame=0,
    end_frame=None,
)
```

### Finding images with matching file names and concatenating them
```python
from imgvid_utils import imagestacker

imagestacker.make_images_from_folders_match(
    dirs_in,
    dir_out,
    max_imgs=None,
    resize_opt=imagestacker.Resize.FIRST,
    stacking=None,
    size=None,
)
```
