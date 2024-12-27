import os
import sys
import time
import psutil
import subprocess


def clear_screen():
    """
    Clears the terminal screen.
    """
    if sys.platform == "win32":
        os.system("cls")
    else:
        os.system("clear")


def get_python_from_venv(venv_path):
    """
    Get the Python executable from the virtual environment's bin or Scripts folder.
    Args:
        venv_path (str): The path to the virtual environment.
    """
    if sys.platform == "win32":
        python_executable = os.path.join(venv_path, "Scripts", "python.exe")
    else:
        python_executable = os.path.join(venv_path, "bin", "python")

    if os.path.isfile(python_executable):
        return python_executable
    else:
        print(f"Python executable not found in virtual environment: {python_executable}")
        return None


def run_scan(scan_type, script_folder, venv_path):
    """
    Run a corruption scan based on the type (video or audio) using the Python from the virtual environment.

    Args:
        scan_type (str): Type of scan, e.g., 'video_meta', 'video_play_hardware', etc.
        script_folder (str): The folder where the scripts are located.
        venv_path (str): Path to the virtual environment.
    """
    # Clear the screen before starting the scan
    clear_screen()

    # Determine the script path based on the scan type
    script_mapping = {
        "audio": "Audio/Corrupt_Audio_Scanner.py",
        "video_meta": "Video/Corrupt_Video_Scanner_MetaData.py",
        "video_play_hardware": "Video/Corrupt_Video_Scanner_Playback_hardware.py",
        "video_play_software": "Video/Corrupt_Video_Scanner_Playback_software.py",
        "video_play_indepth_hardware": "Video/Corrupt_Video_Scanner_InDepth_hardware.py",
        "video_play_indepth_software": "Video/Corrupt_Video_Scanner_InDepth_software.py"
    }

    script_name = script_mapping.get(scan_type)
    if not script_name:
        print(f"Error: Invalid scan type '{scan_type}'.")
        time.sleep(0.25)  # Pause
        return

    scanner_script = os.path.join(script_folder, script_name)

    if not os.path.isfile(scanner_script):
        print(f"Error: The scanner script '{scanner_script}' does not exist.")
        return

    print(f"Running corruption scan...")

    python_exec = get_python_from_venv(venv_path)
    if python_exec:
        process = None  # Initialize process to None
        try:
            # Run the script as a standalone process (no output redirection)
            process = subprocess.Popen([python_exec, "-u", scanner_script],
                                       text=True,  # Ensure text output (no buffering issues)
                                       pass_fds=(),  # Make sure file descriptors are not passed
                                       close_fds=True)  # Ensure no file descriptors are shared

            process.wait()  # Wait for the process to finish before continuing

            # After the scan finishes, check for any zombie processes related to ffmpeg, ffprobe, or python
            terminate_zombies()

        except subprocess.CalledProcessError as e:
            print(f"Error while running corruption scan: {e}")
        finally:
            if process:  # Ensure process is not None before calling terminate
                process.wait()  # Reap the process to prevent zombies
                process.terminate()  # Ensure process is terminated
            subprocess.run(["stty", "sane"])   # Reset the terminal to a sane state
            # Hold the screen until the user presses Enter
            input("\nScan complete. Press Enter to return to the menu...")


def terminate_zombies():
    """
    Checks for any lingering zombie processes (ffmpeg, ffprobe, python) and terminates them.
    """
    # Check all running processes
    for proc in psutil.process_iter(attrs=['pid', 'name', 'status']):
        try:
            # Access attributes using getattr to avoid potential attribute errors
            pid = getattr(proc, 'pid', None)
            name = getattr(proc, 'name', 'Unknown')
            status = getattr(proc, 'status', 'unknown')

            # For Linux/macOS, check for zombie processes
            if sys.platform in ["linux", "darwin"]:  # Check for zombie processes on Linux/macOS
                if status == psutil.STATUS_ZOMBIE and name in ['ffmpeg', 'ffprobe', 'python']:
                    print(f"Terminating zombie process: {name} (PID: {pid})")
                    proc.terminate()  # Kill the zombie process
            else:  # Windows does not have STATUS_ZOMBIE, so check for other conditions
                if name in ['ffmpeg', 'ffprobe', 'python']:
                    print(f"Terminating process: {name} (PID: {pid})")
                    proc.terminate()  # Terminate the process on Windows

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass  # Ignore errors, such as process disappearing or permission issues


def edit_config(file_path):
    """
    Open the config file in nano on Windows.
    - On Windows, only uses nano (if available).
    - On Unix-like systems (Linux/macOS), uses nano if available, falls back to the default editor.
    """
    if sys.platform == "win32":
        try:
            # Try using nano on Windows (e.g., if installed via Chocolatey or another package manager)
            subprocess.run(["nano", file_path], check=True)
        except FileNotFoundError:
            print("Nano not found. Please install nano.")
        except Exception as e:
            print(f"An error occurred while trying to edit the file: {e}")
    else:
        # On Linux/macOS, try using nano first, otherwise use the default system editor
        editor = "nano"  # Default to nano
        try:
            subprocess.run([editor, file_path], check=True)
        except FileNotFoundError:
            print(f"{editor} not found. Falling back to the default editor.")
            editor = os.environ.get("EDITOR", "vi")  # Use $EDITOR environment variable, defaulting to vi
            try:
                subprocess.run([editor, file_path], check=True)
            except FileNotFoundError:
                print(f"{editor} not found. Please install an editor.")
            except Exception as e:
                print(f"An error occurred while trying to edit the file: {e}")


def get_user_choice(prompt, valid_choices):
    """
    Display a prompt and validate user input until a valid choice is made.

    Args:
        prompt (str): The message to display to the user.
        valid_choices (list): A list of valid choices to validate user input against.

    Returns:
        str: The valid user input choice.
    """
    while True:
        choice = input(prompt).strip()
        if choice in valid_choices:
            return choice
        else:
            print("Invalid choice. Please try again.")
            time.sleep(0.25)  # Pause for a moment before showing the prompt again


def show_video_menu():
    script_folder = os.path.dirname(os.path.realpath(__file__))
    venv_path = os.path.join(script_folder, "venv")

    while True:
        clear_screen()
        print("Video Menu:")
        print("1. Scan Video for Metadata (Fast)")
        print("2. Scan Video for Playback (Slower)")
        print("3. Scan Video for Playback at Multiple Points (Slowest)")
        print("0. Return to Main Menu")

        choice = get_user_choice("Please enter your choice (0-3): ", ["1", "2", "3", "0"])

        match choice:
            case "1":
                run_scan("video_meta", script_folder, venv_path)
            case "2" | "3":
                decoding_choice = get_decoding_choice()
                if decoding_choice:  # Only proceed if user did not cancel
                    scan_type = (
                        "video_play" if choice == "2" else "video_play_indepth"
                    )
                    script_name = f"{scan_type}_{decoding_choice}"
                    run_scan(script_name, script_folder, venv_path)
            case "0":
                print("Returning to Main Menu...")
                time.sleep(0.2)  # Pause
                break


def get_decoding_choice():
    """
    Display a submenu to choose between hardware or software decoding.

    Returns:
        str: 'hardware' or 'software' based on user selection.
    """
    decoding_choices = {
        "1": "hardware",
        "2": "software",
        "0": None  # None represents cancel
    }

    while True:
        clear_screen()
        print("Select Decoding Method:")
        print("1. Hardware Decoding (Faster)")
        print("2. Software Decoding (Slower)")
        print("0. Cancel and Return to Previous Menu")

        choice = get_user_choice("Please enter your choice (0-2): ", ["1", "2", "0"])

        if choice == "0":
            print("Returning to Video Menu...")
            time.sleep(0.2)  # Pause
            return None  # Return None if the user cancels

        return decoding_choices[choice]  # Return 'hardware' or 'software'


def show_options_menu():
    while True:
        clear_screen()
        print("Options Menu:")
        print("1. Edit Config for Audio")
        print("2. Edit Config for Video")
        print("3. Update pip and Installed Packages")
        print("0. Return to Main Menu")

        choice = get_user_choice("Please enter your choice (0-3): ", ["1", "2", "3", "0"])

        match choice:
            case "1":
                edit_config("Audio/Config/config.yaml")
            case "2":
                edit_config("Video/Config/config.yaml")
            case "3":
                update_pip_and_packages()
            case "0":
                print("Returning to Main Menu...")
                time.sleep(0.2)  # Pause
                break


def update_pip_and_packages():
    """
    Updates pip and the installed packages in the virtual environment.
    """
    # Clear the screen before starting the update process
    clear_screen()

    venv_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "venv")
    python_exec = get_python_from_venv(venv_path)

    if not python_exec:
        print("Python executable not found in virtual environment. Exiting update process.")
        return

    # Update pip to the latest version
    try:
        print("Updating pip to the latest version...")
        result = subprocess.check_output([python_exec, "-m", "pip", "install", "--upgrade", "pip"],
                                         stderr=subprocess.STDOUT).decode('utf-8')

        # Check if 'Requirement already satisfied' is in the output
        if "Requirement already satisfied" in result:
            print("pip is already up to date.")
        else:
            print("pip updated successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to update pip: {e}")

    # List outdated packages
    try:
        print("\nListing outdated packages...")
        outdated_packages = subprocess.check_output([python_exec, "-m", "pip", "list", "--outdated"]).decode('utf-8')

        # Extract package names and versions from the output
        outdated_packages_lines = outdated_packages.splitlines()
        packages_to_update = []

        for line in outdated_packages_lines[2:]:  # Skip the first two header lines
            parts = line.split()
            if len(parts) >= 3:
                package_name = parts[0]
                packages_to_update.append(package_name)

        if packages_to_update:
            print(f"Updating the following outdated packages: {', '.join(packages_to_update)}")
            # Upgrade outdated packages
            subprocess.check_call([python_exec, "-m", "pip", "install", "--upgrade"] + packages_to_update)
            print("Packages updated successfully.")
        else:
            print("No outdated packages found.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to list or update packages: {e}")

    # Hold until the user presses Enter to return to options menu
    input("\nPress Enter to return to the options menu...")


def main():
    script_folder = os.path.dirname(os.path.realpath(__file__))
    venv_path = os.path.join(script_folder, "venv")

    while True:
        clear_screen()
        print("What do you want to do?")
        print("1. Run Corruption Scan on Audio")
        print("2. Run Corruption Scan on Video")
        print("3. Options")
        print("0. Exit")

        choice = get_user_choice("Please enter your choice (0-3): ", ["1", "2", "3", "0"])

        match choice:
            case "1":
                run_scan("audio", script_folder, venv_path)
            case "2":
                show_video_menu()
            case "3":
                show_options_menu()
            case "0":
                clear_screen()  # Clear the screen before exiting
                print("Exiting the program...")
                time.sleep(0.2)  # Pause
                clear_screen()
                break


if __name__ == "__main__":
    main()
