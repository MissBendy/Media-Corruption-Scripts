## Media-Corruption-Scripts

Python scripts to scan Audio and Video files to detect corruption on media. <br />
Corrupted file details are saved to a CSV file for easy review.

Run Setup to download dependencies, create virtual python environment and required terminal script to run the program.

Scripts only support Python 3.10 through 3.13. 

<ins>**Configuration:**</ins> $~$ Each scanner has configurable options from the run_script file created by setup.py <br />
MUST BE CHANGED TO WORK WITH YOUR SYSTEM

**EXAMPLE USAGE UNIX --> $~$ python3.12 Setup.py** <br />
**EXAMPLE USAGE WIN --> $~$ py -3.12 Setup.py** <br />

-----------------------------------------------------------------------------------------------------------------------

Python modules needed to run script include the following

* colorama $~~$ # For colored terminal output
* tqdm $~~~~~~~~~~$ # For progress bar display
* pyyaml $~~~~~~$ # For YAML file support
* psutil $~~~~~~$ # For retrieving information on running processes

**Video Scanner:**
* validates metadata: Uses ffprobe to check if the video metadata is valid. If not, returns an error.
* validates playback: Uses ffmpeg to check if the video plays correctly with options for scanning.

**Audio Scanner**
* Uses the same methods above, but no options to choose from. Will scan beginning, middle and end of files along with metadata.

-----------------------------------------------------------------------------------------------------------------------

<ins>**Other Required Software That Installs Automatically:**</ins> $~$ FFmpeg on all platforms, Chocolately and Nano (on Windows)

FFmpeg is a multimedia framework that can check video integrity without errors spilling into the terminal. <br />
It works reliably across video/audio codecs and containers. If FFmpeg cannot decode the file, the file is considered corrupt.<br />

Chocolatey is software management automation for Windows that wraps installers, executables, zips, and scripts into compiled packages.

<ins>**Cross-Platform Dependency Check:**</ins> $~$ Setup script will look for required installations across Windows, macOS and Linux.

<ins>**Platform-Specific Installations:**</ins> $~$ Based on the platform (Windows, macOS or Linux) <br />

-----------------------------------------------------------------------------------------------------------------------

> [!IMPORTANT]
> Windows will prompt for admin rights to install Nano via Chocolatey

> [!NOTE]
> When using hardware decoding the CSV output pay report timeouts for incompatible codecs. <br />
> Such files will need to be checked manually until I figure out a fallback to software.
