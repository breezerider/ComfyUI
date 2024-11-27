### 🗻 This file is created through the spirit of Mount Fuji at its peak
# TODO(yoland): clean up this after I get back down
import pytest
import os
import tempfile
from unittest.mock import patch

import comfyui.folder_paths

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname


def test_get_directory_by_type():
    test_dir = "/test/dir"
    comfyui.folder_paths.set_output_directory(test_dir)
    assert comfyui.folder_paths.get_directory_by_type("output") == test_dir
    assert comfyui.folder_paths.get_directory_by_type("invalid") is None

def test_annotated_filepath():
    assert comfyui.folder_paths.annotated_filepath("test.txt") == ("test.txt", None)
    assert comfyui.folder_paths.annotated_filepath("test.txt [output]") == ("test.txt", comfyui.folder_paths.get_output_directory())
    assert comfyui.folder_paths.annotated_filepath("test.txt [input]") == ("test.txt", comfyui.folder_paths.get_input_directory())
    assert comfyui.folder_paths.annotated_filepath("test.txt [temp]") == ("test.txt", comfyui.folder_paths.get_temp_directory())

def test_get_annotated_filepath():
    default_dir = "/default/dir"
    assert comfyui.folder_paths.get_annotated_filepath("test.txt", default_dir) == os.path.join(default_dir, "test.txt")
    assert comfyui.folder_paths.get_annotated_filepath("test.txt [output]") == os.path.join(comfyui.folder_paths.get_output_directory(), "test.txt")

def test_add_model_folder_path():
    comfyui.folder_paths.add_model_folder_path("test_folder", "/test/path")
    assert "/test/path" in comfyui.folder_paths.get_folder_paths("test_folder")

def test_recursive_search(temp_dir):
    os.makedirs(os.path.join(temp_dir, "subdir"))
    open(os.path.join(temp_dir, "file1.txt"), "w").close()
    open(os.path.join(temp_dir, "subdir", "file2.txt"), "w").close()

    files, dirs = comfyui.folder_paths.recursive_search(temp_dir)
    assert set(files) == {"file1.txt", os.path.join("subdir", "file2.txt")}
    assert len(dirs) == 2  # temp_dir and subdir

def test_filter_files_extensions():
    files = ["file1.txt", "file2.jpg", "file3.png", "file4.txt"]
    assert comfyui.folder_paths.filter_files_extensions(files, [".txt"]) == ["file1.txt", "file4.txt"]
    assert comfyui.folder_paths.filter_files_extensions(files, [".jpg", ".png"]) == ["file2.jpg", "file3.png"]
    assert comfyui.folder_paths.filter_files_extensions(files, []) == files

@patch("comfyui.folder_paths.recursive_search")
@patch("comfyui.folder_paths.folder_names_and_paths")
def test_get_filename_list(mock_folder_names_and_paths, mock_recursive_search):
    mock_folder_names_and_paths.__getitem__.return_value = (["/test/path"], {".txt"})
    mock_recursive_search.return_value = (["file1.txt", "file2.jpg"], {})
    assert comfyui.folder_paths.get_filename_list("test_folder") == ["file1.txt"]

def test_get_save_image_path(temp_dir):
    with patch("comfyui.folder_paths.output_directory", temp_dir):
        full_output_folder, filename, counter, subfolder, filename_prefix = comfyui.folder_paths.get_save_image_path("test", temp_dir, 100, 100)
        assert os.path.samefile(full_output_folder, temp_dir)
        assert filename == "test"
        assert counter == 1
        assert subfolder == ""
        assert filename_prefix == "test"