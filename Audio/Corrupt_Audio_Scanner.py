import os
import sys
import csv
import time
import yaml
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import init, Fore, Style
from pathlib import Path
from tqdm import tqdm

# Initialize colorama
init(autoreset=True)


def handle_error_and_exit(message):
    """Display an error message and hold until the user exits the script."""
    sys.stdout.write(f"Error: {message}\nPress Enter to exit the script.")
    sys.stdout.flush()  # Ensure the message is displayed immediately
    input()
    sys.exit(f"{Fore.RED}Exiting due to error:{Style.RESET_ALL} {message}")


def load_config(config_path):
    """Load configuration from a YAML file."""
    try:
        with open(config_path, "r") as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        handle_error_and_exit(f"{Fore.RED}Configuration file '{config_path}' not found.")
    except yaml.YAMLError as e:
        handle_error_and_exit(f"{Fore.RED}Failed to parse configuration file. {e}")


# Get the directory of the current script
script_folder = Path(__file__).parent
CONFIG_FILE = script_folder / "Config" / "Config.yaml"

# Load configurations
config = load_config(CONFIG_FILE)

directories = config.get("DIRECTORIES")

# Ensure valid config values
if not directories or not isinstance(directories, list):
    handle_error_and_exit(f"{Fore.RED}'scan_directories' is missing or not a list in the configuration file.")

# Set max_workers to the number of available CPU cores
max_workers = os.cpu_count()

# Define audio file extensions to check
AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac", ".wma", ".alac"}

# Define paths
output_dir = script_folder / "Results"
output_dir.mkdir(exist_ok=True)
OUTPUT_CSV = output_dir / "Corrupt_Audio.csv"


def validate_audio_metadata(file_path):
    """Validate audio file metadata using ffprobe."""
    try:
        file_path = Path(file_path)
        if not file_path.is_file() or file_path.stat().st_size == 0:
            return file_path, "File is empty or does not exist"

        # Use ffprobe to validate the file's metadata
        command = [
            "ffprobe",
            "-v", "error",
            "-show_format",
            "-show_streams",
            str(file_path)
        ]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            return file_path, f"Metadata validation failed: {result.stderr.strip()}"

        return None  # Metadata is valid
    except Exception as e:
        return file_path, f"Metadata validation error: {str(e)}"


def validate_audio_playback(file_path):
    """Validate audio playback at the start, middle, and end using ffmpeg."""
    try:
        # Validate playback at the start
        start_command = ["ffmpeg", "-v", "error", "-hwaccel", "auto", "-ss", "0", "-i",
                         str(file_path), "-t", "5", "-f", "null", "-"]
        if subprocess.run(start_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode != 0:
            return file_path, "Playback failed at the start"

        # Get the file duration using ffprobe
        duration_command = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                            str(file_path)]
        duration_result = subprocess.run(duration_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        duration_str = duration_result.stdout.strip()
        if not duration_str:
            return file_path, "Failed to fetch file duration"
        duration = float(duration_str)
        midpoint = duration / 2

        # Validate playback at the middle
        middle_command = ["ffmpeg", "-v", "error", "-hwaccel", "auto", "-ss", str(midpoint), "-i",
                          str(file_path), "-t", "5", "-f", "null", "-"]
        if subprocess.run(middle_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode != 0:
            return file_path, "Playback failed at the middle"

        # Validate playback at the end
        end_command = ["ffmpeg", "-v", "error", "-hwaccel", "auto", "-sseof", "-5", "-i",
                       str(file_path), "-t", "5", "-f", "null", "-"]
        if subprocess.run(end_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode != 0:
            return file_path, "Playback failed at the end"

        return None  # Playback is valid
    except Exception as e:
        return file_path, f"Playback validation error: {str(e)}"


def validate_audio_file(file_path):
    """Combine metadata and playback validation for audio files."""
    # Validate metadata first
    metadata_result = validate_audio_metadata(file_path)
    if metadata_result:
        return metadata_result

    # Validate playback
    playback_result = validate_audio_playback(file_path)
    if playback_result:
        return playback_result

    return None  # File is valid


def get_audio_files(dirs):
    """Get all audio files from specified directories."""
    audio_files = []
    for directory in dirs:
        dir_path = Path(directory)
        if dir_path.is_dir():
            audio_files.extend(dir_path.rglob("*"))
    return [file for file in audio_files if file.suffix.lower() in AUDIO_EXTENSIONS and not file.name.startswith("._")]


def main():
    """Main function to process audio files."""
    print(f"{Fore.GREEN}Starting corruption scan for audio files...{Style.RESET_ALL}")

    start_time = time.time()
    audio_files = get_audio_files(directories)
    corrupted_files = []

    print(f"\nUsing {max_workers} threads for scanning.\n")
    print(f"{Fore.BLUE}{Style.BRIGHT}Found {len(audio_files)} audio files to scan.{Style.RESET_ALL}\n")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(validate_audio_file, file): file for file in audio_files}

        for future in tqdm(
                as_completed(futures),
                total=len(audio_files),
                unit=" file",  # Explicitly set 'file' as the unit
                bar_format=f"{{desc}}: {Fore.RED}{Style.BRIGHT} {{rate_fmt}}"
                           f"{Fore.YELLOW}{Style.BRIGHT} | ETA: {{remaining}} | "
                           f"{Fore.RED}{Style.BRIGHT}{{n}}/{{total}} files"):

            result = future.result()
            if result:
                corrupted_files.append(result)

    with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["File Path", "Error"])
        writer.writerows(corrupted_files)

    end_time = time.time()
    elapsed_time = end_time - start_time
    hours = int(elapsed_time // 3600)
    minutes = int((elapsed_time % 3600) // 60)
    seconds = int(elapsed_time % 60)
    print(f"\n{Fore.GREEN}Scan complete!{Style.RESET_ALL}")
    print(f"Total corrupted files: {len(corrupted_files)}")
    print(f"Time elapsed: {hours} hours, {minutes} minutes, {seconds} seconds\n")
    print(f"Results saved to: {OUTPUT_CSV}\n")


if __name__ == "__main__":
    main()
