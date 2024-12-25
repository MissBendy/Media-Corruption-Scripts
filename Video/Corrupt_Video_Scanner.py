import os
import sys
import csv
import time
import yaml
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import init, Fore, Style
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


# Resolve the base path dynamically based on the script's location
BASE_PATH = os.path.dirname(os.path.abspath(__file__))

# Define dynamic paths for configuration file and results directory
CONFIG_FILE = os.path.join(BASE_PATH, "Config", "Config.yaml")
RESULTS_DIR = os.path.join(BASE_PATH, "Results")

# Ensure the Results directory exists
os.makedirs(RESULTS_DIR, exist_ok=True)

try:
    with open(CONFIG_FILE, "r") as config_file:
        config = yaml.safe_load(config_file)
        DIRECTORIES = config["DIRECTORIES"]
        OUTPUT_FILES = {section: os.path.join(RESULTS_DIR, filename) for section, filename in
                        config["OUTPUT_FILES"].items()}
except (FileNotFoundError, KeyError, yaml.YAMLError) as config_error:
    handle_error_and_exit(
        f"{Fore.RED}Configuration file '{CONFIG_FILE}' is missing or invalid. Error: {str(config_error)}"
    )

# Video file extensions to check
VIDEO_EXTENSIONS = (".mkv", ".avi", ".mp4")


def is_video_corrupted(filepath):
    """
    Check if a video file is corrupted using FFmpeg's ffprobe.
    Returns True if the file is corrupted, otherwise False.
    """
    try:
        # Run ffprobe command to verify the file
        with open(os.devnull, "w") as devnull:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "error",  # Only output errors
                    "-i", filepath,  # Input file
                    "-show_entries", "stream=codec_type",
                    "-of", "default=noprint_wrappers=1",
                ],
                stdout=devnull,
                stderr=devnull,
                check=False
            )
        return result.returncode != 0  # Non-zero return code means the file is corrupted
    except subprocess.SubprocessError as subprocess_error:
        handle_error_and_exit(f"{Fore.RED}Error during video corruption check for '{filepath}': {subprocess_error}")
        return True  # Treat unexpected subprocess errors as corruption


def process_section(section_name, directories, output_file):
    """
    Process all directories for a specific section (TV, Anime, or Movies).
    Logs corrupted files to a CSV file.
    """
    corrupted_files = []
    all_files = []

    # Collect all video files from directories
    for directory in directories:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.startswith("._"):  # Ignore files starting with ._
                    continue
                if file.lower().endswith(VIDEO_EXTENSIONS):
                    all_files.append(os.path.join(root, file))

    # Parallel processing using ThreadPoolExecutor
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(is_video_corrupted, filepath): filepath for filepath in all_files}

        with tqdm(total=len(all_files), desc=f"Processing {section_name}", unit=" file", dynamic_ncols=True,
                  bar_format=f"{{desc}}: {Fore.RED}{Style.BRIGHT} {{rate_fmt}}"
                             f"{Fore.YELLOW}{Style.BRIGHT} | ETA: {{remaining}} | "
                             f"{Fore.RED}{Style.BRIGHT}{{n_fmt}}/{{total_fmt}} files") as pbar:
            for future in as_completed(futures):
                pbar.update(1)
                filepath = futures[future]
                try:
                    if future.result():
                        corrupted_files.append(filepath)
                except Exception as e:
                    print(f"Unexpected exception for file {filepath}: {e}. Treating as corrupted.")
                    corrupted_files.append(filepath)  # Log unexpected issues

    # Write corrupted files to CSV
    if corrupted_files:
        with open(output_file, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Corrupted File Path"])
            for file in corrupted_files:
                writer.writerow([file])
    return corrupted_files


def main():

    start_time = time.time()
    total_corrupted = {"TV Shows": 0, "Anime": 0, "Movies": 0}

    # Green text for starting the scan message
    print(f"{Fore.GREEN}Starting corruption scan for video files...\n{Style.RESET_ALL}")
    for section, directories in DIRECTORIES.items():
        output_file = OUTPUT_FILES[section]
        print(f"--- {Fore.BLUE}{Style.BRIGHT}Scanning Section: {section} {Style.RESET_ALL}---")
        corrupted_files = process_section(section, directories, output_file)
        total_corrupted[section] = len(corrupted_files)
        print(f"\nCorrupted files in {section}: {len(corrupted_files)}")
        print(f"Saved to: {output_file}\n")

    # End of processing
    end_time = time.time()
    elapsed_time = end_time - start_time
    hours = int(elapsed_time // 3600)
    minutes = int((elapsed_time % 3600) // 60)
    seconds = int(elapsed_time % 60)

    print(f"{Fore.GREEN}Summary:{Style.RESET_ALL}")
    for section, count in total_corrupted.items():
        print(f"{section}: {count} corrupted files")
    print(f"\nTime elapsed: {hours} hours, {minutes} minutes, {seconds} seconds\n")


if __name__ == "__main__":
    check_python_version()
    main()
