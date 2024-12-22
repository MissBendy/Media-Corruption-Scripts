## Media-Corruption-Scripts

Python scripts to scan Audio and Video files to detect corruption on media. <br />
Corrupted file details are saved to a CSV file for easy review.

Run Setup to check for and install dependencies if needed.

Scripts only support Python 3.10 through 3.12. 

<ins>**Configuration:**</ins> $~$ Each scanner has configurable options <br />
MUST BE CHANGED TO WORK WITH YOUR SYSTEM

**EXAMPLE USAGE UNIX --> $~$ python3.12 Setup_macOS.py** <br />
**EXAMPLE USAGE WIN --> $~$ py -3.12 Setup_Windows.py**

-----------------------------------------------------------------------------------------------------------------------

Python modules needed to run script include the following

* pydub $~~~~~~~~$ # For handling and validating audio files
* soundfile $~~~$ # For validating .wav and .flac files
* wget $~~~~~~~~~~~$ # For downloading FFmpeg on Windows
* mutagen $~~~$ # For handling audio metadata
* tqdm $~~~~~~~~~~$ # For progress bar display
* pyyaml $~~~~~~$ # For YAML file support
* colorama $~~$ # For colored terminal output

-----------------------------------------------------------------------------------------------------------------------

<ins>**Other Required Software:**</ins> $~$ FFmpeg

FFmpeg is a multimedia framework that can check video integrity without errors spilling into the terminal. <br />
It works reliably across video codecs and containers. If FFmpeg cannot decode the file, the file is considered corrupt.

<ins>**Cross-Platform Dependency Check:**</ins> $~$ Setup script will look for required installations across Windows and macOS.

<ins>**Platform-Specific Installations:**</ins> $~$ Based on the platform (Windows or macOS) <br />
Setup script will prompt users to install any missing dependencies.

-----------------------------------------------------------------------------------------------------------------------

> [!IMPORTANT]
> Setup right now only supports Windows 10/11 and macOS <br />

> [!NOTE]
> Planned Support for various Linux Distros
