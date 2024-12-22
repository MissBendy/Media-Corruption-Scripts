import subprocess
import sys
import platform
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)


def handle_error_and_exit(message):
    """Display an error message and hold until the user exits the script."""
    sys.stdout.write(f"Error: {message}\nPress Enter to exit the script.")
    sys.stdout.flush()  # Ensure the message is displayed immediately
    input()
    sys.exit(f"Exiting due to error: {message}")


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


class System:
    """Class to handle system detection and management (OS and packages)."""

    @staticmethod
    def detect_OS():
        """Detect macOS."""
        try:
            system = platform.system()

            if system == "Darwin":
                return "macOS"

            return "Unsupported OS"
        except Exception as e:
            handle_error_and_exit(f"Error detecting OS: {e}")

    @staticmethod
    def check_ffmpeg_installed():
        """Check if FFmpeg is installed and in PATH."""
        try:
            subprocess.check_call(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except FileNotFoundError:
            return False

    @staticmethod
    def check_homebrew_installed():
        """Check if Homebrew is installed on macOS."""
        try:
            subprocess.check_call(["which", "brew"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False


class PipManager:
    """Class to handle pip installation and related tasks."""

    @staticmethod
    def check_pip_installed():
        """Check if pip is installed."""
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "--version"], stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False

    @staticmethod
    def install_pip():
        """Prompt the user to install python3-pip if it is missing."""
        print("pip is not installed. Attempting to install pip...")
        OS = System.detect_OS()

        if OS == "macOS":
            print("You can install pip with: ensurepip")
            try:
                subprocess.check_call([sys.executable, "-m", "ensurepip", "--upgrade"])
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
                print("pip has been installed and upgraded.")
                return
            except subprocess.CalledProcessError:
                handle_error_and_exit("Failed to install pip with ensurepip. Please install pip manually.")
        else:
            handle_error_and_exit("Unsupported OS or Linux distribution. Please install pip manually.")


class PackageInstaller:
    """Class to handle package installation and system-specific installation logic."""

    def __init__(self):
        self.OS = System.detect_OS()

    @staticmethod
    def is_package_installed(package):
        """Check if a Python package is installed in the current environment."""
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "show", package], stdout=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False

    def check_missing_packages(self):
        """Check which Python packages are missing."""
        missing_packages = []
        for package in self.required_packages:
            if not self.is_package_installed(package):
                missing_packages.append(package)
        return missing_packages

    required_packages = [
        "mutagen",  # For handling audio metadata
        "soundfile",  # For validating .wav and .flac files
        "pydub",  # For handling and validating audio files
        "tqdm",  # For progress bar display
        "pyyaml",  # For YAML file support
        "colorama",  # For colored terminal output
    ]

    def install_packages(self, packages):
        """Install missing packages based on the detected OS."""
        if packages:
            print(f"The following Python packages are missing: {', '.join(packages)}")
            try:
                self.install_with_pip(packages)
            except Exception as e:
                handle_error_and_exit(f"Failed to install packages: {e}")
        else:
            print("All required Python packages are already installed.")

    @staticmethod
    def install_with_pip(packages):
        """Install Python packages using pip."""
        print("Installing Python packages using pip...")
        for package in packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"{package} has been installed using pip.")
            except subprocess.CalledProcessError:
                handle_error_and_exit(f"Failed to install {package} using pip. Please install it manually.")

    def main(self):
        missing_packages = self.check_missing_packages()
        self.install_packages(missing_packages)


class FFmpegInstaller:
    """Class to handle FFmpeg installation and management."""

    @staticmethod
    def check_ffmpeg_in_path():
        """Check if FFmpeg is installed and in the PATH."""
        try:
            subprocess.check_call(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except FileNotFoundError:
            return False

    @staticmethod
    def install_ffmpeg():
        """Install FFmpeg based on the system's OS."""
        if FFmpegInstaller.check_ffmpeg_in_path():
            print("FFmpeg is available in the PATH.")
            return

        print("FFmpeg is not found in the PATH.")

        os_name = platform.system().lower()

        if os_name == "darwin":
            if not System.check_homebrew_installed():
                try:
                    subprocess.check_call(["/bin/bash", "-c",
                                           "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"])
                except subprocess.CalledProcessError:
                    handle_error_and_exit("Failed to install Homebrew. Please install it manually.")
            try:
                subprocess.check_call(["brew", "install", "ffmpeg"])
            except subprocess.CalledProcessError:
                handle_error_and_exit("Failed to install FFmpeg using Homebrew. Please install it manually.")


if __name__ == "__main__":
    # Ensure Python version is compatible
    check_python_version()

    # Print Operating System
    detected_os = System.detect_OS()

    # Exit if the OS is unsupported
    if detected_os == "Unsupported OS":
        handle_error_and_exit(f"{Fore.RED}Unsupported OS detected.{Style.RESET_ALL}")

    # Print the detected OS
    print(f"Detected OS: {detected_os}")

    # Check FFmpeg availability and install if needed
    FFmpegInstaller.install_ffmpeg()

    # Check if pip is installed, install it if not
    if not PipManager.check_pip_installed():
        PipManager.install_pip()

    # Check and install missing packages
    installer = PackageInstaller()
    installer.main()
