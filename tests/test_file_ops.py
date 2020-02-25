import unittest
from src import file_ops as fo
import os
import shutil


class TestFileOps(unittest.TestCase):
    dirs_to_delete = []
    files_to_delete = []
    top_folder = "./test_suite/"

    def setUp(self):
        self.make_dir(self.top_folder)
        self.make_file("./test_suite/test.mp4")
        self.make_file("./test_suite/test1.mp4")
        self.make_file("./test_suite/test2.mp4")
        self.make_dir("./test_suite/images/")
        self.make_dir("./test_suite/images_new/")
        for i in range(25):
            self.make_file("./test_suite/images/image%d.mp4" % i)
            self.make_file("./test_suite/images/image%d.png" % i)
            self.make_file("./test_suite/images_new/image%d.png" % i)

    def tearDown(self):
        for file in self.files_to_delete:
            if os.path.exists(file):
                os.remove(file)
        self.files_to_delete = []
        for directory in self.dirs_to_delete:
            if os.path.exists(directory):
                shutil.rmtree(directory)
        self.dirs_to_delete = []

    def make_dir(self, dir_name):
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            self.dirs_to_delete.append(dir_name)

    def make_file(self, file_name):
        if not os.path.exists(file_name):
            open(file_name, 'a').close()
            self.files_to_delete.append(file_name)

    def test_check_files(self):
        self.assertTrue(fo.check_files("./test_suite/test.mp4"))
        self.assertTrue(fo.check_files(["./test_suite/test.mp4", "./test_suite/test1.mp4"]))
        self.assertFalse(fo.check_files(["./test_suite/"]))
        self.assertFalse(fo.check_files(["./test_suite/test.mp4", "./test_suite/test3.mp4"]))
        self.assertEqual(fo.check_files(["./test_suite/test.mp4", "./test_suite/test3.mp4"], return_missing=True),
                         ["./test_suite/test3.mp4"])

    def test_check_dirs(self):
        self.assertTrue(fo.check_dirs("./test_suite/"))
        self.assertTrue(fo.check_dirs(["./test_suite/"]))
        self.assertFalse(fo.check_dirs(["./test_suite/does_not_exist"]))
        self.assertEqual(fo.check_dirs(["./test_suite/", "./test_suite/does_not_exist"], return_missing=True),
                         ["./test_suite/does_not_exist"])

    def test_get_files(self):
        self.assertEqual(25, len(fo.get_files("./test_suite/images", ".mp4")))
        self.assertEqual(25, len(fo.get_files("./test_suite/images/", ".mp4")))
        self.assertEqual(25, len(fo.get_files("./test_suite/images/", ".pnG")))
        self.assertEqual(50, len(fo.get_files("./test_suite/images/", [".pnG", ".mp4"])))

    def assertFilePathEqual(self, path_one, path_two):
        return os.path.normpath(path_one) == os.path.normpath(path_two)

    def test_get_first_n_files(self):
        files = fo.get_first_n_files("./test_suite/images/", ".mp4", 10)
        self.assertEqual(10, len(files))
        for i in range(10):
            self.assertFilePathEqual("./test_suite/images/image%d.mp4" % i, files[i])

    def test_append_forward_slash_path(self):
        paths = ["a", "hello", "hello/", "/hello/"]
        paths_correct = ["a/", "hello/", "hello/", "/hello/"]
        self.assertEqual(paths_correct, fo.append_forward_slash_path(paths))
        self.assertEqual("string/", fo.append_forward_slash_path("string"))
        self.assertEqual("string/", fo.append_forward_slash_path("string/"))

    def test_clear_files(self):
        self.assertTrue(len(fo.get_files("./test_suite/images/", "mp4")) > 0)
        fo.clear_files("./test_suite/images", "mp4")
        self.assertTrue(len(fo.get_files("./test_suite/images/", "mp4")) == 0)

    def test_form_file_name(self):
        self.assertFilePathEqual("./hello/world.mp4", fo.form_file_name("./hello", "world.mp4", "mp4"))
        self.assertFilePathEqual("./hello/world.mp4", fo.form_file_name("./hello", "world.mp4.mp4", "mp4"))


if __name__ == '__main__':
    unittest.main()
