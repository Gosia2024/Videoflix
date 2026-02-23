"""
Background tasks for video processing.

Handles asynchronous HLS conversion using FFmpeg
triggered after a video upload.
"""
from pathlib import Path
import django_rq
from django.conf import settings
from .models import Video
from .utils import create_output_directory, build_ffmpeg_command, run_ffmpeg

@django_rq.job
def convert_video_to_hls(video_id: int):
    """
    Convert a video file into multiple HLS resolutions
    (480p, 720p, 1080p) using FFmpeg.
    """
    video = Video.objects.get(id=video_id)

    input_path = video.file.path
    base_output_path = Path(settings.MEDIA_ROOT) / "videos" / str(video.id)

    for resolution in ["480p", "720p", "1080p"]:
        output_dir = create_output_directory(base_output_path, resolution)
        output_file = str(output_dir / "index.m3u8")

        command = build_ffmpeg_command(input_path, output_file, resolution)
        run_ffmpeg(command)