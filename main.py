import sys
import subprocess
import os


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
        scan_type (str): Type of scan, either 'video' or 'audio'.
        script_folder (str): The folder where the scripts are located.
        venv_path (str): Path to the virtual environment.
    """
    # Clear the screen before starting the scan
    clear_screen()

    scanner_script = os.path.join(
        script_folder, "Video/Corrupt_Video_Scanner.py" if scan_type == "video" else "Audio/Corrupt_Audio_Scanner.py"
    )

    if not os.path.isfile(scanner_script):
        print(f"Error: The scanner script '{scanner_script}' does not exist.")
        return

    print(f"Running {scan_type} corruption scan...")

    python_exec = get_python_from_venv(venv_path)
    if python_exec:
        try:
            subprocess.check_call([python_exec, scanner_script])
        except subprocess.CalledProcessError as e:
            print(f"Error while running {scan_type} corruption scan: {e}")


def edit_config(file_path):
    """
    Open the config file in a text editor.
    - On Windows, tries Notepad++ first, then falls back to Notepad.
    - On Unix-like systems, uses the default editor specified in the EDITOR environment variable or defaults to nano.
    """
    if sys.platform == "win32":
        try:
            subprocess.run(["notepad++.exe", file_path], check=True)
        except FileNotFoundError:
            print("Notepad++ not found, falling back to Notepad.")
            try:
                subprocess.run(["notepad.exe", file_path], check=True)
            except FileNotFoundError:
                print("Notepad not found. Please install a text editor.")
        except Exception as e:
            print(f"An error occurred while trying to edit the file: {e}")
    else:
        editor = os.environ.get("EDITOR", "nano")
        try:
            subprocess.run([editor, file_path], check=True)
        except FileNotFoundError:
            print(f"Editor '{editor}' not found. Please install it or set the EDITOR environment variable.")
        except Exception as e:
            print(f"An error occurred while trying to edit the file: {e}")


def validate_choice(choice, valid_choices):
    """
    Validate the user's menu choice.
    Args:
        choice (str): The user's input.
        valid_choices (list): A list of valid choices.
    Returns:
        bool: True if valid, False otherwise.
    """
    return choice in valid_choices


def show_options_menu():
    """
    Display the submenu for editing configuration files and handle user selection.
    """
    while True:
        clear_screen()
        print("Options Menu:")
        print("1. Edit config for Video")
        print("2. Edit config for Audio")
        print("3. Update pip and installed packages")
        print("4. Return to Main Menu")

        choice = input("Please enter your choice (1-4): ").strip()

        if not validate_choice(choice, ["1", "2", "3", "4"]):
            print("Invalid choice. Please try again.")
            continue

        if choice == "1":
            edit_config("Video/Config/config.yaml")
        elif choice == "2":
            edit_config("Audio/Config/config.yaml")
        elif choice == "3":
            update_pip_and_packages()
        elif choice == "4":
            print("Returning to main menu...")
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
        print("1. Run corruption scan on Audio")
        print("2. Run corruption scan on Video")
        print("3. Run corruption scan on Video then Audio")
        print("4. Options")
        print("5. Exit")

        choice = input("Please enter your choice (1-5): ")

        if not validate_choice(choice, ["1", "2", "3", "4", "5"]):
            print("Invalid choice. Please try again.")
            continue

        if choice == "1":
            run_scan("audio", script_folder, venv_path)
        elif choice == "2":
            run_scan("video", script_folder, venv_path)
        elif choice == "3":
            run_scan("video", script_folder, venv_path)
            run_scan("audio", script_folder, venv_path)
        elif choice == "4":
            show_options_menu()
        elif choice == "5":
            print("Exiting the program. Goodbye!")
            break


if __name__ == "__main__":
    main()
