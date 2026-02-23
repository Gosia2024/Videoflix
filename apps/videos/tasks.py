# import os
# import subprocess
# import django_rq
# from django.conf import settings
# from .models import Video


# @django_rq.job
# def convert_video_to_hls(video_id):
#     video = Video.objects.get(id=video_id)

#     input_path = video.file.path
#     output_dir = os.path.join(settings.MEDIA_ROOT, f"videos/{video.id}/720p")

#     os.makedirs(output_dir, exist_ok=True)

#     output_path = os.path.join(output_dir, "index.m3u8")

#     command = [
#         "ffmpeg",
#         "-i", input_path,
#         "-profile:v", "baseline",
#         "-level", "3.0",
#         "-start_number", "0",
#         "-hls_time", "10",
#         "-hls_list_size", "0",
#         "-f", "hls",
#         output_path
#     ]

#     subprocess.run(command)

from pathlib import Path
import django_rq
from django.conf import settings
from .models import Video
from .utils import create_output_directory, build_ffmpeg_command, run_ffmpeg


@django_rq.job
def convert_video_to_hls(video_id: int):
    video = Video.objects.get(id=video_id)

    input_path = video.file.path
    base_output_path = Path(settings.MEDIA_ROOT) / "videos" / str(video.id)

    for resolution in ["480p", "720p", "1080p"]:
        output_dir = create_output_directory(base_output_path, resolution)
        output_file = str(output_dir / "index.m3u8")

        command = build_ffmpeg_command(input_path, output_file, resolution)
        run_ffmpeg(command)