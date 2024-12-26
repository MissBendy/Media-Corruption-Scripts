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

* tqdm $~~~~~~~~~~$ # For progress bar display
* pyyaml $~~~~~~$ # For YAML file support
* colorama $~~$ # For colored terminal output

-----------------------------------------------------------------------------------------------------------------------

<ins>**Other Required Software That Installs Automatically:**</ins> $~$ FFmpeg, Chocolately, Nano or Terminal Editor

FFmpeg is a multimedia framework that can check video integrity without errors spilling into the terminal. <br />
It works reliably across video/audio codecs and containers. If FFmpeg cannot decode the file, the file is considered corrupt.<br />

Chocolatey is software management automation for Windows that wraps installers, executables, zips, and scripts into compiled packages.

<ins>**Cross-Platform Dependency Check:**</ins> $~$ Setup script will look for required installations across Windows, macOS and Linux.

<ins>**Platform-Specific Installations:**</ins> $~$ Based on the platform (Windows, macOS or Linux) <br />

-----------------------------------------------------------------------------------------------------------------------
