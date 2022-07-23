#!/usr/bin/env python3


from cgitb import handler
import os
import subprocess
import argparse
import json
from shutil import which
from pymediainfo import MediaInfo
import logging


def log_message(message):
    file_handler = logging.FileHandler("logger.log")
    file_handler.setLevel(logging.DEBUG)
    logger = logging.getLogger()
    logger.addHandler(file_handler)

    return logger


class ffmpegProcesser():
    def __init__(self, source_file, video_rotation_info):
        self.source_file = source_file
        self.base_filename = os.path.basename(source_file)
        self.video_rotation_info = int(float(video_rotation_info))
        self.output_location = os.path.join(os.path.dirname(source_file), "corrected")


    def determine_rotations(self):
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

        print(transpose_flag)
        
    def remove_rotation(self):
        '''Caches temporary file in user temp storage'''

        if which("ffmpeg") is not None:
            self.temp_file = f'/tmp/{self.base_filename}'
            print(f"Removing rotation {self.source_file}")
            stdout, stderr = subprocess.Popen(
                [
                    "ffmpeg", "-hide_banner", "-loglevel", "error",
                    "-i", f"{self.source_file}",
                    "-c", "copy", "-metadata:s:v:0",
                    "rotate=0", self.temp_file] , 
                    universal_newlines=True, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE
                    ).communicate()
                    
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
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error",
                "-i", self.temp_file, "-vf", vf_filters,
                "-crf", "23",
                "-c:a", "copy",
                f"{self.output_location}/{filename}.mp4"] , 
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
    def __init__(self, source_file):
        self.source_file = source_file
        self.video_object = None

    def get_rotation_metadata (self) -> int:
        for i in range(len(self.video_object)):
            
            if self.video_object['media']['track'][i]["StreamKind"] == "Video":
                rotation = self.video_object['media']['track'][1]['Rotation']
                break

        return rotation

    def parse_video_data(self) -> str:
        '''Returns JSON of video rotation requested from MediaInfo'''

        
        media_info = MediaInfo.parse(self.source_file,
                    output="JSON")
        self.video_object = json.loads(media_info)
        if self.video_object is not None:
            rotation_data = self.get_rotation_metadata()
            if rotation_data:
                return rotation_data
            else:
                print("No attributes found")
                return None
        else:
            print("No attributes found")
            return None

def installed(program):
    ''' Check if a program is installed'''
    if which(program):
        return True
    else:
        return False

def clean_up_files(file: os.path):
    if not os.remove(file):
        return FileNotFoundError

    



def rotate_video(videoFileList):
    '''Obtain Video Rotate Information for a list of videos
    Calculates rotation  
    Executes Ffmpeg Rotation'''

    aggregatedRotationInfo = []
    for file in videoFileList:        
        video_rotation_info = metadataProcessor(file).parse_video_data()
        ffmpegProcesser(file,video_rotation_info).run_ffmpeg_commands()


acceptedFormats = ('.avi', '.mp4', '.mp3', '.mxf', '.mov', '.wav', '.aif')

if __name__ == "__main__":
    if not installed("ffprobe"):
        print("FFprobe Not Installed")
        exit(1)
    parser = argparse.ArgumentParser(description="A program that generates metadata summaries and can extract audio from video files")
    parser.add_argument("-f", "--files", nargs="*", help="Indivudal files or directories to process")

    args = parser.parse_args()

    fileList = [] #Create list of files to process.
    for files in args.files:
        if os.path.isdir(files):
            directoryFiles = sorted(os.listdir(files))
            for file in directoryFiles:
                if file.lower().endswith(acceptedFormats):
                    fileList.append(os.path.join(files, file))
        elif os.path.isfile(files):
            if files.lower().endswith(acceptedFormats):
                fileList.append(os.path.abspath(files))

    sourceFiles = sorted(fileList)
    if not sourceFiles:
        print('No accepted files found. Drag files or folders or both.')
    else:
        rotate_video(sourceFiles)        

