import pytest

from  src.rotate_video import metadataProcessor, rotate_video, ffmpegProcesser, installed


def test_program_installed():
    assert installed("ffmpeg") == True


def test_program_not_installed():
    assert installed("pymediainfo") == False


@pytest.fixture
def file_list():
    video_files = list(
        "/Users/ehernand/Downloads/IMG_4899.MOV"
    )
    return video_files


def test_file_not_found():
    with pytest.raises(NameError):
        metadataProcessor(file).get_rotation_metadata()


def test_libmedia_binary_not_found(file_list):
    with pytest.raises(RuntimeError):
        for file in file_list:
            video_metadata = metadataProcessor(file).video_metadata()
            assert isinstance(video_metadata, dict)

def test_ffmpeg_installed():
    ffmpeg = installed('ffmpeg')
    assert ffmpeg

def test_video_rotation_type(file_list):
    with pytest.raises(RuntimeError):
        for file in file_list:
            rotate_video = metadataProcessor(file).get_rotation_metadata()
            assert isinstance(rotate_video, int)