import unittest
from src import videostacker as vs
from src import file_ops as fo
import os
import cv2


class TestVideoStacker(unittest.TestCase):

    # add frame equals.
    def assertFilePathEqual(self, path_one, path_two):
        return os.path.normpath(path_one) == os.path.normpath(path_two)

    def test_videosplit(self):
        vs.split_video("./src/test_files/00000.MTS", "temp/", "kitty", "png", frame_count=100, start_frame=15)
        self.assertEqual(100, len(fo.get_files("./temp/", "png")))
        files = fo.get_files("./temp", "png")
        for i in range(100):
            self.assertTrue(self.assertFilePathEqual("./temp/kitty%s.png" % str(i).zfill(99), files[i]))

        fo.clear_files("./temp/", "png")

    def test_video_from_videos(self):
        vs.make_video_from_videos(["./src/test_files/00000.MTS", "./src/test_files/00000.MTS"]
                                  , "temp/", "kitty", "mp4", cols=2, rows=1, width=800, height=600)

        video = cv2.VideoCapture("./src/test_files/00000.MTS")
        fps = video.get(cv2.CAP_PROP_FPS)
        num_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        ret = True
        while ret:
            ret, frame = video.read()
        video.release()
        vid = cv2.VideoCapture("./temp/kitty.mp4")
        width_vid = int(vid.get(cv2.CAP_PROP_FRAME_WIDTH))
        height_vid = int(vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps_vid = vid.get(cv2.CAP_PROP_FPS)
        num_frames_vid = int(vid.get(cv2.CAP_PROP_FRAME_COUNT))
        ret = True
        while ret:
            ret, frame = video.read()
        vid.release()

        self.assertEqual(num_frames, num_frames_vid)
        self.assertEqual(fps, fps_vid)
        self.assertEqual(1600, width_vid)
        self.assertEqual(600, height_vid)


if __name__ == '__main__':
    unittest.main()
