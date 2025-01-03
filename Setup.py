import os
import sys
import platform
import stat
import shutil
import subprocess
from subprocess import CalledProcessError

# Handle colorama mock for unsupported environments
try:
    from colorama import init, Fore, Style
except ModuleNotFoundError:
    from collections import UserString


    class ColorMock(UserString):
        def __call__(self, *args, **kwargs):
            return self

        def __getattr__(self, key):
            return self


    init = ColorMock("")
    Fore = Style = ColorMock("")

# Initialize colorama
init(autoreset=True)


def handle_error_and_exit(message):
    """Display an error message and hold until the user exits the script."""
    sys.stdout.write(f"Error: {message}\nPress Enter to exit the script.")
    sys.stdout.flush()
    input()
    sys.exit(1)


class System:
    """Class to handle system detection and management (OS and packages)."""

    detected_distro_type = None

    @staticmethod
    def detect_OS():
        """Detect OS and store distribution type for reuse."""
        try:
            os_name = platform.system().lower()

            match os_name:
                case "linux":
                    distro_info = platform.freedesktop_os_release()
                    distro_id = distro_info.get("ID", "unknown").lower()

                    match distro_id:
                        case "arch" | "manjaro" | "endeavouros":
                            System.detected_distro_type = "Arch-based"
                        case "debian" | "ubuntu" | "pop" | "linuxmint":
                            System.detected_distro_type = "Debian/Ubuntu-based"
                        case "fedora" | "rhel" | "centos" | "rocky" | "almalinux":
                            System.detected_distro_type = "Fedora-based"
                        case "opensuse" | "suse":
                            System.detected_distro_type = "openSUSE-based"
                        case _:
                            System.detected_distro_type = "Unsupported Linux Distribution"
                    return System.detected_distro_type

                case "darwin":
                    return "macOS"

                case "windows":
                    return "Windows"

                case _:
                    return "Unsupported OS"
        except Exception as e:
            handle_error_and_exit(f"{Fore.RED}Error detecting OS: {e} {Style.RESET_ALL}")

    @staticmethod
    def check_python_version():
        """Ensure the script is running on a compatible Python version."""
        current_version = sys.version_info

        if current_version < (3, 10) or current_version >= (3, 14):
            handle_error_and_exit(
                f"{Fore.RED}This script requires Python version between 3.10 and 3.13.{Style.RESET_ALL}\n"
                f"You are using Python {current_version.major}.{current_version.minor}."
            )
        print(f"{Fore.YELLOW}Python version is compatible. Proceeding with the script...{Style.RESET_ALL}")


class FFmpegInstaller:
    ffmpeg_in_path = None

    @staticmethod
    def check_ffmpeg_in_path():
        """Check if FFmpeg is installed and in the PATH."""
        if FFmpegInstaller.ffmpeg_in_path is None:
            FFmpegInstaller.ffmpeg_in_path = shutil.which("ffmpeg") is not None
        return FFmpegInstaller.ffmpeg_in_path

    @staticmethod
    def check_homebrew_installed():
        """Check if Homebrew is installed on macOS."""
        return shutil.which("brew") is not None

    @staticmethod
    def install_homebrew():
        """Install Homebrew on macOS."""
        try:
            print("Downloading Homebrew install script...")
            script = subprocess.check_output(
                ["curl", "-fsSL", "https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh"]
            )
            print("Running install script with bash...")
            subprocess.check_call(["/bin/bash", "-c", script.decode('utf-8')])
            print(f"{Fore.GREEN}Homebrew installed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"{Fore.RED}Failed to install Homebrew: {e}")

    @staticmethod
    def install_ffmpeg():
        """Install FFmpeg based on the detected OS."""
        os_type = platform.system().lower()

        if FFmpegInstaller.check_ffmpeg_in_path():
            print(f"{Fore.GREEN}FFmpeg is already installed and available in the PATH.")
            return

        try:
            match os_type:
                case "darwin":  # macOS
                    print("FFmpeg not found. Checking for Homebrew...")
                    if not FFmpegInstaller.check_homebrew_installed():
                        FFmpegInstaller.install_homebrew()

                    print("Installing FFmpeg using Homebrew...")
                    try:
                        # Using subprocess.check_call to install FFmpeg with Homebrew
                        subprocess.check_call(["brew", "install", "ffmpeg"])
                    except subprocess.CalledProcessError:
                        pass  # Ignore any errors that occur during installation

                    # After attempting installation, check if FFmpeg is listed by Homebrew
                    try:
                        # Run `brew list ffmpeg` to verify if FFmpeg was successfully installed
                        subprocess.check_call(["brew", "list", "ffmpeg"])
                        print(f"{Fore.GREEN}FFmpeg has been installed via Homebrew.")
                    except subprocess.CalledProcessError:
                        print(f"{Fore.RED}FFmpeg installation failed using Homebrew")

                case "windows":
                    try:
                        # Check if FFmpeg is already installed
                        subprocess.check_call(["where", "ffmpeg"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        print(f"{Fore.GREEN}FFmpeg is already installed.{Fore.RESET}")
                        return
                    except subprocess.CalledProcessError:
                        print(f"{Fore.YELLOW}{Style.BRIGHT}FFmpeg not found. Proceeding with installation.{Fore.RESET}")

                    print(f"{Fore.BLUE}{Style.BRIGHT}Installing FFmpeg with winget...{Fore.RESET}")
                    subprocess.check_call(["winget", "install", "ffmpeg"])
                    print(f"{Fore.GREEN}FFmpeg has been installed using winget.{Fore.RESET}")

                case "linux":
                    distro_type = System.detected_distro_type or System.detect_OS()

                    match distro_type:
                        case "Arch-based":
                            subprocess.check_call(["sudo", "pacman", "-S", "ffmpeg", "--noconfirm"])
                        case "Debian/Ubuntu-based":
                            subprocess.check_call(["sudo", "apt", "update"])
                            subprocess.check_call(["sudo", "apt", "install", "ffmpeg", "-y"])
                        case "Fedora-based":
                            subprocess.check_call(["sudo", "dnf", "install", "ffmpeg", "-y"])
                        case "openSUSE-based":
                            subprocess.check_call(["sudo", "zypper", "install", "ffmpeg", "-y"])
                        case _:
                            print(f"Unsupported Linux distribution: {distro_type}")
                case _:
                    print(f"Unsupported OS for FFmpeg installation: {os_type}")

        except CalledProcessError as e:
            print(f"{Fore.RED}Failed to install FFmpeg: {e}")


class DarwinNanoInstaller:
    @staticmethod
    def install_nano_and_update_nanorc():
        """Install nano using Homebrew on macOS and update ~/.nanorc if nano is not installed."""

        def is_nano_installed():
            """Check if nano is installed via Homebrew on macOS."""
            try:
                # Check if nano is installed via Homebrew
                subprocess.run(["brew", "list", "nano"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return True
            except subprocess.CalledProcessError:
                return False  # nano is not installed via Homebrew

        # Ensure this script runs only on macOS
        if platform.system() != "Darwin":
            return  # Skip quietly if not macOS

        # Check if nano is installed via Homebrew on macOS
        if not is_nano_installed():
            print(f"{Fore.YELLOW}{Style.BRIGHT}nano not found. Proceeding with installation...{Style.RESET_ALL}")
            try:
                subprocess.run(["brew", "install", "nano"], check=True)
                print(f"{Fore.GREEN}Installed nano using Homebrew{Style.RESET_ALL}")
            except subprocess.CalledProcessError:
                print(f"{Fore.RED}Failed to install nano using Homebrew.{Style.RESET_ALL}")
                return
        else:
            print(f"{Fore.GREEN}nano is already installed via Homebrew.{Style.RESET_ALL}")

        # Update ~/.nanorc
        nanorc_path = os.path.expanduser("~/.nanorc")
        nanorc_include = 'include "/usr/local/share/nano/*.nanorc"'

        # Check if the line is already in ~/.nanorc
        try:
            with open(nanorc_path, "r") as f:
                if nanorc_include in f.read():
                    print(f"{Fore.GREEN}~/.nanorc already includes the nano configurations.{Style.RESET_ALL}")
                    return
        except FileNotFoundError:
            pass  # ~/.nanorc doesn't exist yet

        # Append the include line
        try:
            with open(nanorc_path, "a") as f:
                f.write(f"{nanorc_include}\n")
            print(f"{Fore.GREEN}Updated ~/.nanorc with nano configurations.{Style.RESET_ALL}")
        except IOError:
            print(f"{Fore.RED}Failed to update ~/.nanorc.{Style.RESET_ALL}")


class ProgramSetup:
    """Class to set up virtual environment, main script, and terminal scripts."""

    def __init__(self):
        self.script_folder = os.path.dirname(os.path.realpath(__file__))
        self.venv_path = os.path.join(self.script_folder, 'venv')
        self.main_script_path = os.path.join(self.script_folder, "main.py")

    def setup_program(self):
        """Run all setup tasks: first install FFmpeg/Homebrew, then create virtualenv, main script, and terminal scripts."""
        # First, ensure FFmpeg and Homebrew are installed
        ffmpeg_installer = FFmpegInstaller()
        ffmpeg_installer.install_ffmpeg()  # This will use the match/case to install FFmpeg based on the OS

        # Install nano and update ~/.nanorc on macOS
        DarwinNanoInstaller.install_nano_and_update_nanorc()

        # Continue with the rest of the program setup
        venv_path = self.create_virtualenv()
        self.install_dependencies(venv_path)
        self.generate_terminal_script(venv_path)

    def create_virtualenv(self):
        """Create a virtual environment inside the script folder."""
        if not os.path.exists(self.venv_path):
            subprocess.check_call([sys.executable, "-m", "venv", self.venv_path])
            print(f"{Fore.GREEN}Virtual environment created at:{Style.RESET_ALL} {self.venv_path}")

            # Upgrade pip immediately after creating the virtual environment
            pip_path = os.path.join(self.venv_path, 'bin', 'pip') if sys.platform != 'win32' else os.path.join(
                self.venv_path, 'Scripts', 'pip')
            subprocess.check_call([pip_path, "install", "--upgrade", "pip"])
            print(f"{Fore.GREEN}pip has been upgraded to the latest version.")
        else:
            print(f"{Fore.GREEN}Virtual environment already exists.")
        return self.venv_path

    @staticmethod
    def check_and_install_pip(venv_path):
        """Ensure pip is installed in the virtual environment."""

        # Determine the path to the pip executable based on the platform
        match sys.platform:
            case 'win32':  # Windows
                pip_path = os.path.join(venv_path, 'Scripts', 'pip.exe')
            case _ if sys.platform.startswith(("linux", "darwin")):  # Linux and macOS
                pip_path = os.path.join(venv_path, 'bin', 'pip')
            case _:
                pip_path = None

        # Check if pip exists in the virtual environment
        if pip_path and not os.path.exists(pip_path):
            print(f"{Fore.RED}pip not found in the virtual environment. Installing pip...{Style.RESET_ALL}")

            try:
                match sys.platform:
                    case "win32" | _ if sys.platform.startswith("linux"):  # Windows and Linux
                        # Use get-pip.py to install pip
                        print(f"{Fore.RED}Using get-pip.py to install pip...{Style.RESET_ALL}")
                        url = "https://bootstrap.pypa.io/get-pip.py"
                        subprocess.check_call([sys.executable, url])  # Download and run get-pip.py
                        print(f"{Fore.GREEN}pip has been successfully installed using get-pip.py.{Style.RESET_ALL}")

                    case "darwin":  # macOS
                        # Use ensurepip to install pip (without importing ensurepip)
                        print(f"{Fore.RED}Using ensurepip to install pip...{Style.RESET_ALL}")
                        subprocess.check_call([sys.executable, "-m", "ensurepip", "--upgrade"])
                        print(f"{Fore.GREEN}pip has been successfully installed using ensurepip.{Style.RESET_ALL}")

                    case _:  # Unsupported platform
                        print(f"{Fore.RED}Unsupported platform for pip installation.{Style.RESET_ALL}")
                        return  # Exit early for unsupported platforms

            except Exception as e:
                # Handle general exceptions that might occur during pip installation
                handle_error_and_exit(f"Error installing pip: {e}")

    @staticmethod
    def install_dependencies(venv_path):
        if sys.platform == 'win32':
            # Ensure Chocolatey is installed
            try:
                subprocess.check_call(["choco", "-v"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"{Fore.GREEN}Chocolatey is already installed.")
            except subprocess.CalledProcessError:
                print(f"{Fore.YELLOW}{Style.BRIGHT}Chocolatey not found. Proceeding with installation.")
                try:
                    print(f"{Fore.BLUE}{Style.BRIGHT}Installing Chocolatey with winget...")
                    subprocess.check_call(["winget", "install", "Chocolatey.Chocolatey"])
                    print(f"{Fore.GREEN}Chocolatey has been installed using winget.")
                except subprocess.CalledProcessError as e:
                    print(f"{Fore.RED}Failed to install Chocolatey: {e}")
                    return

            # Check if Nano is installed
            try:
                subprocess.check_call(["nano", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"{Fore.GREEN}Nano is already installed.")
                return
            except FileNotFoundError:
                print(f"{Fore.YELLOW}{Style.BRIGHT}Nano is not installed. Proceeding with installation.")
            except subprocess.CalledProcessError as e:
                print(f"{Fore.RED}An error occurred while checking Nano: {e}. Proceeding with installation.")

            # Install Nano using Chocolatey
            try:
                print(f"{Fore.BLUE}{Style.BRIGHT}Installing Nano using Chocolatey...")
                subprocess.check_call(
                    [
                        "powershell",
                        "-Command",
                        "Start-Process powershell -Verb runAs -ArgumentList 'choco install nano -y'"
                    ]
                )
                print(f"{Fore.GREEN}Nano has been installed successfully.")
            except subprocess.CalledProcessError as e:
                print(f"{Fore.RED}Failed to install Nano: {e}")

        """Install required packages into the virtual environment."""
        # Ensure pip is installed first
        ProgramSetup.check_and_install_pip(venv_path)

        # Path to pip in the virtual environment
        pip_path = os.path.join(venv_path, 'bin', 'pip') if sys.platform != 'win32' else os.path.join(venv_path,
                                                                                                      'Scripts', 'pip')

        # List of required packages
        packages = ["tqdm", "pyyaml", "colorama", "psutil"]

        # Get the list of installed packages in the virtual environment using pip
        installed_packages = subprocess.check_output([pip_path, 'list', '--format=freeze'], text=True)

        # Parse the installed packages output into a set of package names (lowercased)
        installed_package_names = {pkg.split('==')[0].lower() for pkg in installed_packages.splitlines()}

        # Check which required packages are missing
        missing_packages = [pkg for pkg in packages if pkg.lower() not in installed_package_names]

        if missing_packages:
            print(f"Installing missing python packages: {', '.join(missing_packages)}...")
            subprocess.check_call([pip_path, "install"] + missing_packages)
            print(f"{Fore.GREEN}Missing dependencies installed successfully.{Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}All dependencies are installed.{Style.RESET_ALL}")

    @staticmethod
    def generate_terminal_script(venv_path):
        """Generate the appropriate terminal script based on OS and terminal."""
        script_folder = os.path.dirname(os.path.realpath(__file__))
        os_name = sys.platform
        terminal_script = None

        match os_name:
            case "win32":  # Windows
                terminal_script = os.path.join(script_folder, "run_script.ps1")
                with open(terminal_script, "w") as file:
                    file.write(f"""
            $env:VIRTUAL_ENV="{venv_path}"
            $env:PATH="$env:VIRTUAL_ENV\\Scripts;$env:PATH"
            python main.py
            """)
                print(f"PowerShell script created at: {terminal_script}")

            case _ if os_name in ("darwin", "linux"):  # macOS or Linux
                shell = os.environ.get("SHELL", "")
                match True:
                    case True if "zsh" in shell:  # Zsh
                        terminal_script = os.path.join(script_folder, "run_script.zsh")
                        with open(terminal_script, "w") as file:
                            file.write(f"""#!/bin/zsh
            export VIRTUAL_ENV="{venv_path}"
            export PATH="$VIRTUAL_ENV/bin:$PATH"
            python main.py
            """)
                        print(f"Zsh script created at: {terminal_script}")

                    case _:  # Bash (or other shells)
                        terminal_script = os.path.join(script_folder, "run_script.sh")
                        with open(terminal_script, "w") as file:
                            file.write(f"""#!/bin/bash
            export VIRTUAL_ENV="{venv_path}"
            export PATH="$VIRTUAL_ENV/bin:$PATH"
            python main.py
            """)
                        print(f"Bash script created at: {terminal_script}")

                # Ensure Unix-based scripts are executable
                if terminal_script:
                    st = os.stat(terminal_script)
                    os.chmod(terminal_script, st.st_mode | stat.S_IEXEC)

            case _:  # Unsupported OS
                print(f"Unsupported OS: {os_name}")

        return terminal_script


class Cleanup:
    """Class to clean up installation files left by pip, Homebrew, and Chocolatey."""

    @staticmethod
    def run_cleanup():
        """Run the cleanup process."""
        print("Cleaning Up...")  # Print message before cleanup starts

    @staticmethod
    def clean_pip():
        """Remove the get-pip.py script if it's been used."""
        pip_script = os.path.join(os.path.dirname(os.path.realpath(__file__)), "get-pip.py")
        if os.path.exists(pip_script):
            print(f"Cleaning up pip installation script at: {pip_script}")
            os.remove(pip_script)

    @staticmethod
    def prompt_delete_setup():
        """Ask the user if they want to delete setup.py after the script completes."""
        response = input(
            f"{Fore.RED}{Style.BRIGHT}Do you want to delete setup.py?{Style.RESET_ALL} (y/n): ").strip().lower()
        if response == 'y':
            try:
                script_path = os.path.realpath(__file__)
                os.remove(script_path)
                print(f"{Fore.GREEN}setup.py has been deleted successfully.{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}Failed to delete setup.py: {e}{Style.RESET_ALL}")


def main():
    if __name__ == "__main__":
        System.check_python_version()

        detected_os = System.detect_OS()
        if detected_os == "Unsupported OS":
            handle_error_and_exit(f"{Fore.RED}Unsupported OS detected.{Style.RESET_ALL}")

        print(f"Detected OS: {detected_os}")

        setup = ProgramSetup()
        setup.setup_program()

        Cleanup.run_cleanup()
        cleanup = Cleanup()
        cleanup.clean_pip()
        cleanup.prompt_delete_setup()


if __name__ == "__main__":
    main()
