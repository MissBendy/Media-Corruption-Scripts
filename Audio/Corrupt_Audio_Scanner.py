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


def check_python_version():
    """Ensure the script is running on a compatible Python version."""
    current_version = sys.version_info

    # Ensure that the Python version is between 3.10 and 3.13
    if current_version < (3, 10) or current_version >= (3, 14):
        handle_error_and_exit(
            f"{Fore.RED}This script requires Python version between 3.10 and 3.13. {Style.RESET_ALL}\n"
            f"You are using Python {current_version.major}.{current_version.minor}.")
    print(f"{Fore.YELLOW}Python version is compatible. Proceeding with the script...{Style.RESET_ALL}")


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
AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".flac", ".m4a"}

# Define paths
output_dir = script_folder / "Results"
output_dir.mkdir(exist_ok=True)
OUTPUT_CSV = output_dir / "Corrupt_Audio.csv"


def validate_audio_ffprobe(file_path):
    """Validate audio files using ffprobe."""
    try:
        file_path = Path(file_path)
        if not file_path.is_file() or file_path.stat().st_size == 0:
            return file_path, "File is empty or does not exist"

        # Use ffprobe to check the file
        command = [
            "ffprobe",
            "-v", "error",
            "-show_format",
            "-show_streams",
            str(file_path)
        ]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            return file_path, f"FFprobe Error: {result.stderr.strip()}"

        return None  # File is valid
    except Exception as e:
        return file_path, f"Unexpected Error: {str(e)}"


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
        futures = {executor.submit(validate_audio_ffprobe, file): file for file in audio_files}

        for future in tqdm(
                as_completed(futures),
                total=len(audio_files),
                bar_format=f"{Fore.RED}{Style.BRIGHT}{{rate_fmt}} {Fore.YELLOW}{Style.BRIGHT}| ETA: {{remaining}} | {Fore.RED}{Style.BRIGHT}{{n_fmt}}/{{total_fmt}} files",
                unit=" file"
        ):
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
    check_python_version()
    main()
