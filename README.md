# SpeakNotes

"SpeakNotes" is a experimental project based on a simple application idea, where users can quickly create new notes by speaking, and the application converts them into text.

The primary purpose of this project was to test the [Kivy Python App Development Framework](https://kivy.org/) and explore how [OpenAI's Whisper](https://github.com/openai/whisper) speech recognition model performs. I got the idea for real-time recognition implementation from [this GitHub project](https://github.com/davabase/whisper_real_time).

Here is an example video demonstrating how the application works:

[![SpeakNotes Demo Video](https://i.imgur.com/UVXAqOi.jpg)](https://www.youtube.com/watch?v=6wHmWoP4QPg)

This project is purely experimental, and my intention was not to make it a finished product. However, perhaps someone can benefit from this version and continue its development further.

## Setup WSL: Ubuntu & Anaconda

### Test Setup Versions

* Windows 11 Pro
* WSL2 1.2.5.0
* Ubuntu 22.04
* Python 3.10
* Kivy 2.2.0
* PyTorch 2.0.1

### Install Commands

* Here are notes on the commands I use to install the application in my test environment.

```
# Update distro (optional)
sudo apt-get update
sudo apt-get dist-upgrade

# Install build-essentials and portaudio. These needed to get PyAudio installed properly.
sudo apt-get install build-essential
sudo apt install portaudio19-dev

# Install PulseAudio because we need this to make audio to work in WSL
sudo apt-get install pulseaudio pulseaudio-utils

# Install ALSA
sudo apt-get install alsa-base alsa-utils

# Install ffmpeg
sudo apt update && sudo apt install ffmpeg

# Install & update Anaconda (Miniconda)
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# Restart WSL
exit

# Update Anaconda (optional)
conda update conda
conda update anaconda

# Create conda environment and activate it
conda create --name sn python=3.10 pip
conda activate sn

# Update pip and setuptools
pip install --upgrade pip setuptools

# Install Kivy
pip install Kivy

# Install whisper. It's automatically install torch also.
pip install git+https://github.com/openai/whisper.git

# Install SpeechRecognition
pip install SpeechRecognition

# Install PyAudio
pip install PyAudio

# Install ffmpeg-python. We still need this even we installed ffmpeg on distro.
pip install ffmpeg-python

# Fix error: Input: MTDev is not supported by your version of linux
sudo apt-get install libmtdev-dev

# Fix error: Could not load library libcudnn_cnn_infer.so.8
echo 'export LD_LIBRARY_PATH=/usr/lib/wsl/lib:$LD_LIBRARY_PATH' >> ~/.bashrc

# Fix error: libGL error: MESA-LOADER: failed to open swrast: /usr/lib/dri/swrast_dri.so
conda install -c conda-forge libstdcxx-ng

# Fix error: No such file or directory: xclip
sudo apt-get install xclip xsel

# Clone this repository to current directory and cd into it
git clone https://github.com/Creatide/SpeakNotes.git && cd "$(basename "$_" .git)"

# Start SpeakNotes app
python main.py
```

# Setup: Windows VM (Hyper-V)

* I also tried to get the application to work on a mobile device using a virtual machine. However, I was not successful in this attempt, and this stage remained incomplete. Nevertheless, here are notes on the commands.
* It is best to download python from python.org and install as Administrator
* Install python to custom location with a known path (for all users) e.g. "C:\Program Files\Python310"
* Run CMD or PowerShell with Administrator rights to make sure that libraries are installed under that custom Python site-packages folder.

## System-Wide (Without Virtual Environment)

```
# Clone this repository to current directory
git clone https://github.com/Creatide/SpeakNotes.git

# Install the Visual C++ Redistributables (PowerShell admin rights)
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://vcredist.com/install.ps1'))

# Make sure that "C:\Windows\system32" is in PATH. 
# Otherwise there could be errors with attrib.exe with FFmpeg installation.
# Open Environment Variables window:
rundll32 sysdm.cpl,EditEnvironmentVariables

# Install Scoop https://scoop.sh using PowerShell
# Scoop could be installed without admin rights
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
irm get.scoop.sh | iex

# Install FFmpeg with scoop
scoop install ffmpeg

# Update pip and setuptools
python -m pip install --upgrade pip wheel setuptools

# Install Kivy
python -m pip install -U kivy

# Install PyAudio
python -m pip install -U PyAudio

# Install ffmpeg-python
python -m pip install -U ffmpeg-python

# Install SpeechRecognition
python -m pip install -U SpeechRecognition

# Install OpenAI Whisper and dependencies
python -m pip install -U openai-whisper

# Run SpeakNotes with PowerShell or CMD
python .\main.py
```

## Fix Possible Errors

* Fix: sdl2 - RuntimeError: b'Could not initialize OpenGL / GLES library' (Source: https://stackoverflow.com/a/51241411)
  * `python -m pip install docutils pygments pypiwin32 kivy.deps.sdl2 kivy.deps.glew`
  * `python -m pip install kivy.deps.gstreamer`
  * `python -m pip install kivy.deps.angle`
