#!/usr/bin/env python3


import os
import subprocess
import argparse
import json
from shutil import which
from pymediainfo import MediaInfo
import logging
from typing import Union


def log_message(message):
    file_handler = logging.FileHandler("logger.log")
    file_handler.setLevel(logging.DEBUG)
    logger = logging.getLogger()
    logger.addHandler(file_handler)
    return logger


class ffmpegProcesser():
    def __init__(self, source_file: str, video_rotation_info):
        self.source_file = source_file
        self.base_filename = os.path.basename(source_file)
        self.video_rotation_info = int(float(video_rotation_info))
        self.output_location = os.path.join(os.path.dirname(source_file), "corrected")

    def determine_rotations(self) -> Union[str , None]:
        rotations = None
        transpose_flag = ""
    
        if self.video_rotation_info != 0:
            rotations = int(self.video_rotation_info / 90)
            for i in range(rotations):
                if i == 0:
                    transpose_flag = "transpose=1,"
                else:
                    transpose_flag = transpose_flag + "transpose=1,"
            return transpose_flag[:-1]
        else:
            return None
        
    def remove_rotation(self):
        '''Caches temporary file in user temp storage'''

        if which("ffmpeg") is not None:
            self.temp_file = f'/tmp/{self.base_filename}'
            print(f"Removing rotation {self.source_file}")
            stdout, stderr = subprocess.Popen(
                ["ffmpeg",
                "-hide_banner",
                "-loglevel", "error",
                "-i", f"{self.source_file}",
                "-c", "copy", "-metadata:s:v:0",
                "rotate=0", self.temp_file], 
                universal_newlines=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE).communicate()
                    
            if stderr:
                if os.path.exists(self.temp_file):
                    clean_up_files(self.temp_file)
                return None

    def correct_orientation(self, transpose_flags):
        filename, ext = self.base_filename.split(".")
        if os.path.exists(f'{self.output_location}/{filename}.mp4'):
            clean_up_files(f'{self.output_location}/{filename}.mp4')

        vf_filters = """zscale=t=linear:npl=200,format=gbrpf32le,
                zscale=p=bt709,tonemap=tonemap=mobius:desat=2,
                zscale=t=bt709:m=bt709:r=tv,format=yuv420p"""
        
        if transpose_flags is not None:
            vf_filters = vf_filters + f",{transpose_flags}"
        if not os.path.exists(self.output_location):
            os.makedirs(self.output_location)
        if which("ffmpeg") is not None:
            stdout, stderr = subprocess.Popen(
                ["ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i", self.temp_file, "-vf", vf_filters,
                "-crf", "23",
                "-c:a", "copy",
                f"{self.output_location}/{filename}.mp4"], 
                universal_newlines=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
                ).communicate()
            if stdout:
                print(f'Error: {stdout}. Deleting {self.temp_file}')
                clean_up_files(self.temp_file)
                clean_up_files(f"{self.output_location}/{filename}.mp4")
            else:
                print("Done")

    def run_ffmpeg_commands(self):
        self.remove_rotation()
        self.correct_orientation(self.determine_rotations())


class metadataProcessor():
    def __init__(self, source_file: str):
        self.source_file = source_file
        self._video_metadata = None

    def get_rotation_metadata(self) -> str:
        for track in self.video_metadata['media']['track']:
            if track["StreamKind"] == "Video":
                rotation = track['Rotation']
                break
        return rotation
    @property
    def video_metadata(self) -> str:
        if self._video_metadata is None:
            '''Returns JSON of video rotation requested from MediaInfo'''

            media_info = MediaInfo.parse(
                    self.source_file,
                    output="JSON")
            self._video_object = json.loads(media_info)
            return self._video_object
        else:
            return self._video_object

def installed(program):
    ''' Check if a program is installed'''
    if which(program):
        return True
    else:
        return False


def clean_up_files(file: os.path):
    if not os.remove(file):
        return FileNotFoundError


def rotate_video(video_file_list: list):
    '''Obtain Video Rotate Information for a list of videos
    Calculates rotation  
    Executes Ffmpeg Rotation'''

    for file in video_file_list:        
        video_rotation_info = metadataProcessor(file).get_rotation_metadata()
        ffmpegProcesser(file, video_rotation_info).run_ffmpeg_commands()


acceptedFormats = ('.avi', '.mp4', '.mp3', '.mxf', '.mov', '.wav', '.aif')

if __name__ == "__main__":
    if not installed("ffprobe"):
        print("FFprobe Not Installed")
        exit(1)
    parser = argparse.ArgumentParser(
        description="A program that generates metadata summaries \
            and can extract audio from video files")
    parser.add_argument(
        "-f",
        "--files",
        nargs="*",
        help="Indivudal files or directories to process")

    args = parser.parse_args()

    fileList = []  # Create list of files to process.
    for files in args.files:
        if os.path.isdir(files):
            directoryFiles = sorted(os.listdir(files))
            for file in directoryFiles:
                if file.lower().endswith(acceptedFormats):
                    fileList.append(os.path.join(files, file))
        elif files.lower().endswith(acceptedFormats):
            fileList.append(os.path.abspath(files))

    sourceFiles = sorted(fileList)
    if not sourceFiles:
        print('No accepted files found. Drag files or folders or both.')
    else:
        rotate_video(sourceFiles)