import sys
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)


# Define handle_error_and_exit first
def handle_error_and_exit(message):
    """Display an error message and hold until the user exits the script."""
    sys.stdout.write(f"Error: {message}\nPress Enter to exit the script.")
    sys.stdout.flush()  # Ensure the message is displayed immediately
    input()
    sys.exit(f"Exiting due to error: {message}")


# Ensure Python version is compatible
def check_python_version():
    """Ensure the script is running on a compatible Python version."""
    current_version = sys.version_info

    # Ensure that the Python version is between 3.10 and 3.12
    if current_version < (3, 10) or current_version >= (3, 13):
        handle_error_and_exit(
            f"{Fore.RED}This script requires Python version between 3.10 and 3.12. {Style.RESET_ALL}\n"
            f"You are using Python {current_version.major}.{current_version.minor}."
        )
    print(f"{Fore.YELLOW}Python version is compatible. Proceeding with the script...{Style.RESET_ALL}")


# Check Python version before any imports
check_python_version()

import os
import csv
import time
import soundfile as sf
import yaml
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from mutagen import File
from mutagen import MutagenError
from pydub import AudioSegment
from tqdm import tqdm


def load_config(config_path):
    """
    Load configuration from a YAML file.
    :param config_path: Path to the YAML configuration file.
    :return: Dictionary containing configuration settings.
    """
    try:
        with open(config_path, "r") as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        handle_error_and_exit(
            f"{Fore.RED}Configuration file '{config_path}' not found. Please provide the correct file.")
    except yaml.YAMLError as e:
        handle_error_and_exit(f"{Fore.RED}Failed to parse configuration file. {e}")


# Define the audio file extensions to check
AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".flac", ".m4a"}

# Load configurations
CONFIG_FILE = "Config/Config.yaml"
config = load_config(CONFIG_FILE)

# Extract directories and thread count from the configuration
directories = config.get("DIRECTORIES")
max_workers = config.get("MAX_THREADS")

if not directories or not isinstance(directories, list):
    handle_error_and_exit(f"{Fore.RED}'scan_directories' is missing or not a list in the configuration file.")
if not isinstance(max_workers, int) or max_workers <= 0:
    handle_error_and_exit(f"{Fore.RED}'max_threads' must be a positive integer in the configuration file.")

# Get the main script's directory
script_dir = Path(__file__).parent

# Define paths to 'Results' directory
output_dir = script_dir / "Results"

# Ensure 'Results' directory exists
output_dir.mkdir(exist_ok=True)

# Path for the CSV output file inside 'Results'
OUTPUT_CSV = output_dir / "Corrupt_Files.csv"


# Function to check audio file with stricter validation
def strict_audio_validation(file_path):
    try:
        # Skip empty or zero-byte files early
        if os.path.getsize(file_path) == 0:
            return file_path, "File is empty"

        # Skip files starting with "._"
        if os.path.basename(file_path).startswith("._"):
            return None

        # Attempt to open with Mutagen (basic check)
        audio = File(file_path)
        if audio is None:
            return file_path, "Unrecognized or corrupted (Mutagen)"

        # Additional stricter checks based on file extension
        ext = os.path.splitext(file_path.lower())[1]
        if ext in [".wav", ".flac"]:
            with sf.SoundFile(file_path) as f:
                f.read(10)  # Read a small part to validate
        elif ext in [".mp3", ".m4a", ".ogg"]:
            audio_segment = AudioSegment.from_file(file_path)
            if len(audio_segment) == 0:
                return file_path, "File is empty or corrupted (Pydub)"

        return None  # File is valid
    except MutagenError as e:
        return file_path, f"Mutagen Error: {str(e)}"
    except sf.LibsndfileError as e:
        return file_path, f"SoundFile Error: {str(e)}"
    except Exception as e:
        return file_path, f"Error: {str(e)}"


# Function to get all audio files from multiple directories
def get_audio_files(data):
    audio_files = []
    for directory in data:
        if not os.path.isdir(directory):
            continue

        for root, _, files in os.walk(directory):
            for file in files:
                if file.startswith("._"):
                    continue  # Ignore "._" prefixed files
                if any(file.lower().endswith(ext) for ext in AUDIO_EXTENSIONS):
                    audio_files.append(os.path.join(root, file))
    return audio_files


# Main function
def main():
    # Green text for starting the scan message
    print(f"{Fore.GREEN}Starting corruption scan for audio files...{Style.RESET_ALL}")

    start_time = time.time()

    # Get the list of audio files
    audio_files = get_audio_files(directories)

    corrupted_files = []

    print(f"\nUsing {max_workers} threads for scanning.\n")
    print(f"{Fore.BLUE}{Style.BRIGHT}Found {len(audio_files)} audio files to scan.{Style.RESET_ALL}\n")

    # Process files with ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(strict_audio_validation, file): file for file in audio_files}

        # Display progress bar with blue color
        for future in tqdm(
                as_completed(futures),
                total=len(audio_files),
                bar_format=(
                        f"{Fore.RED}{Style.BRIGHT}{'{rate_fmt}'}"  # Rate colored red with bright style
                        f"{Fore.YELLOW}{Style.BRIGHT}{' | ETA: {remaining} | '}"  # ETA colored yellow with bright style
                        f"{Fore.RED}{Style.BRIGHT}{'{n_fmt}/{total_fmt}'} files"),
                # Files count colored red with bright style
                unit=" file"
        ):
            result = future.result()
            if result:
                corrupted_files.append(result)

    # Write results to CSV
    with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["File Path", "Error"])
        for file_path, error in corrupted_files:
            writer.writerow([file_path, error])

    # Final report
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
    # Ensure Python version is compatible
    main()
