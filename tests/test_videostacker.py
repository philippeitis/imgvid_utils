import unittest
from imgvid_utils import video as vs
from imgvid_utils import file_ops as fo
from imgvid_utils.make_random_vid import make_random_vid
import os
import cv2


class TestVideoStacker(unittest.TestCase):

    # add frame equals.
    def assertFilePathEqual(self, path_one, path_two):
        return os.path.normpath(path_one) == os.path.normpath(path_two)

    def test_video_raises_error_on_non_existent_file(self):
        self.assertRaises(ValueError, vs.VideoIterator, "./test_files/i_do_not_exist.mp4", "temp/")

    def test_videosplit(self):
        path = "./tests/test_files/vsplit_00000.mp4"
        os.makedirs("./tests/test_files/", exist_ok=True)
        make_random_vid(path)
        vs.VideoIterator(path).write_images("./tests/temp/", "random", "png", 2)
        files = fo.get_files("./tests/temp/", "png")
        self.assertEqual(100, len(files))
        for i, file in enumerate(files):
            expected = "./tests/temp/random%s.png" % str(i).zfill(2)
            self.assertTrue(self.assertFilePathEqual(expected, file), msg=f"{expected} != {file}")

        fo.clear_files("./tests/temp/", "png")

    def test_video_from_videos(self):
        path1 = "./tests/test_files/vfv_00001.mp4"
        path2 = "./tests/test_files/vfv_00002.mp4"
        make_random_vid(path1)
        make_random_vid(path2)

        frames = 0
        for _ in vs.VideoIterator([path1, path2]):
            frames += 1

        self.assertEqual(frames, 100, "number of frames should be equal to 100")

    def test_video_stack(self):
        path1 = "./tests/test_files/vstack_00001.mp4"
        path2 = "./tests/test_files/vstack_00002.mp4"
        make_random_vid(path1)
        make_random_vid(path2)

        test_path = "./tests/temp/vstack_out.mp4"
        vs.VideoIterator([path1, path2]).write_video(test_path)
        video = cv2.VideoCapture(test_path)
        self.assertEqual(video.get(cv2.CAP_PROP_FPS), 24.0)
        self.assertEqual(vs.video_dimensions(video), (128, 48))
        self.assertEqual(video.get(cv2.CAP_PROP_FRAME_COUNT), 100.0)

    def test_concatenate_videos(self):
        path1 = "./tests/test_files/cv_00001.mp4"
        path2 = "./tests/test_files/cv_00002.mp4"
        make_random_vid(path1)
        make_random_vid(path2)

        frames = 0
        for _ in vs.VideoIterator(path1).chain(vs.VideoIterator(path2)):
            frames += 1

        self.assertEqual(frames, 200, "number of frames should be equal to 200")

    def test_concatenate_videos_write(self):
        path1 = "./tests/test_files/cvw_00001.mp4"
        path2 = "./tests/test_files/cvw_00002.mp4"
        make_random_vid(path1)
        make_random_vid(path2)

        test_path = "./tests/temp/cvw_out.mp4"
        vs.VideoIterator(path1).chain(vs.VideoIterator(path2)).resize_in((64, 48)).write_video(test_path)
        video = cv2.VideoCapture(test_path)
        self.assertEqual(video.get(cv2.CAP_PROP_FPS), 24.0)
        self.assertEqual(vs.video_dimensions(video), (64, 48))
        self.assertEqual(video.get(cv2.CAP_PROP_FRAME_COUNT), 200.0)

if __name__ == '__main__':
    unittest.main()
