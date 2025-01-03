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
VIDEO_EXTENSIONS = (".mkv", ".avi", ".mp4", ".mov", ".wmv", ".mpg", ".mpeg", ".3gp", ".m4v")


def validate_playback(file_path):
    """Validate playback using ffmpeg."""
    process = None  # Initialize process variable
    try:
        # Attempt to open the video file with hardware acceleration
        command = ["ffmpeg", "-v", "error", "-i", file_path, "-t", "5", "-f", "null", "-"]

        # Use Popen for better control and timeout handling
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Wait for the process to complete with a timeout (e.g., 30 seconds)
        stdout, stderr = process.communicate(timeout=30)

        if process.returncode != 0:
            return False, f"Playback failed at start: {stderr.strip()}"

        return True, None

    except subprocess.TimeoutExpired:
        if process:
            process.kill()  # Ensure the process is killed if it exceeds the timeout
        return False, "Playback process timed out, Please Check Manually"
    except Exception as e:
        if process:
            process.kill()  # Ensure the process is killed in case of an unexpected error
        return False, f"Error occurred: {str(e)}"


def is_video_corrupted(filepath):
    """
    Check if a video file is corrupted using both ffprobe (metadata validation)
    and ffmpeg (partial playback validation).
    """
    try:
        # Playback validation
        playback_valid, playback_error = validate_playback(filepath)
        if not playback_valid:
            return True, f"Playback error: {playback_error}"

        return False, None  # File is valid
    except Exception as e:
        return True, str(e)  # Treat unexpected exceptions as corruption


def process_section(section_name, directories, output_file, max_workers, start_time):
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
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(is_video_corrupted, filepath): filepath for filepath in all_files}

        with tqdm(total=len(all_files),
                  desc=f"Processing {section_name}",
                  unit=" file",  # Explicitly set 'file' as the unit
                  bar_format=f"{{desc}}: {Fore.RED}{Style.BRIGHT} {{rate_fmt}}"
                             f"{Fore.YELLOW}{Style.BRIGHT} | ETA: {{remaining}} | "
                             f"{Fore.RED}{Style.BRIGHT}{{n}}/{{total}} files") as pbar:
            for future in as_completed(futures):
                pbar.update(1)  # Increment the progress bar for each completed task
                filepath = futures[future]
                try:
                    corrupted, reason = future.result()
                    if corrupted:
                        corrupted_files.append((filepath, reason))
                except Exception as e:
                    corrupted_files.append((filepath, str(e)))  # Log unexpected issues

                # Set custom rate with 'file/s' manually
                rate = pbar.n / (time.time() - start_time)  # Calculate rate manually
                pbar.set_postfix({"rate": f"{rate:.2f} file/s", "n": f"{pbar.n}", "total": f"{pbar.total}"},
                                 refresh=True)

    # Write corrupted files to CSV
    if corrupted_files:
        with open(output_file, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Corrupted File Path", "Reason"])
            for file, reason in corrupted_files:
                writer.writerow([file, reason])
    return corrupted_files


def main():
    start_time = time.time()

    # Dynamically generate the total_corrupted dictionary based on section names
    total_corrupted = {section: 0 for section in DIRECTORIES}

    # Calculate max_workers based on the number of CPU cores
    max_workers = os.cpu_count()

    # Green text for starting the scan message
    print(f"{Fore.GREEN}Starting corruption scan for video files...\n{Style.RESET_ALL}")
    print(f"Using {max_workers} threads for scanning.\n")  # Print number of threads

    for section, directories in DIRECTORIES.items():
        output_file = OUTPUT_FILES[section]
        print(f"--- {Fore.BLUE}{Style.BRIGHT}Scanning Section: {section} {Style.RESET_ALL}---")
        corrupted_files = process_section(section, directories, output_file, max_workers, start_time)
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
    main()
