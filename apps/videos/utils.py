import subprocess
from pathlib import Path


RESOLUTION_MAP = {
    "480p": "854x480",
    "720p": "1280x720",
    "1080p": "1920x1080",
}


def create_output_directory(base_path: Path, resolution: str) -> Path:
    output_path = base_path / resolution
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def build_ffmpeg_command(input_file: str, output_file: str, resolution: str):
    scale_value = RESOLUTION_MAP[resolution]

    return [
        "ffmpeg",
        "-i", input_file,
        "-vf", f"scale={scale_value}",
        "-profile:v", "baseline",
        "-level", "3.0",
        "-start_number", "0",
        "-hls_time", "10",
        "-hls_list_size", "0",
        "-f", "hls",
        output_file,
    ]


def run_ffmpeg(command: list):
    subprocess.run(command, check=True)