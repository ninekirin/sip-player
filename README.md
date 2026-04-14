# SIP Player

A SIP-based music player with DTMF IVR control. Answer incoming calls automatically and play audio tracks to the caller. Control playback via DTMF tones or GUI.

## Features

- **SIP Registration**: Register to any SIP server
- **Auto-Answer**: Automatically answer incoming calls
- **Audio Playback**: Play WAV audio files to SIP calls
- **DTMF Control**: Control playback with DTMF tones (1/2/3/4)
- **Multi-Session**: Support multiple concurrent calls
- **Bilingual UI**: English and Chinese (Simplified) interface
- **Import**: Convert MP3/M4A/FLAC to WAV via ffmpeg

## Requirements

- **Python**: 3.12 or higher
- **PJSIP**: 2.16+ (with pjsua2 Python bindings)
- **tkinter**: GUI framework
- **ffmpeg**: For audio format conversion (optional, for import feature)

## Platform Setup

Choose your platform below for detailed setup instructions:

- [Windows](#windows-setup)
- [macOS](#macos-setup)
- [Linux](#linux-setup)

---

## Windows Setup

### Step 1: Install Python

1. Download Python 3.12+ from [python.org](https://www.python.org/downloads/)
2. During installation, **check "Add Python to PATH"**
3. Verify installation:
   ```cmd
   python --version
   ```

### Step 2: Install tkinter

tkinter is included with Python on Windows. Verify it works:
```cmd
python -c "import tkinter; print('tkinter OK')"
```

If you get an error, reinstall Python and ensure tcl/tk is selected.

### Step 3: Install Build Tools

Download and install [Visual Studio Community](https://visualstudio.microsoft.com/downloads/):
- During installation, select **"Desktop development with C++"**
- Or install [Build Tools for Visual Studio](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022)

### Step 4: Install SWIG

1. Download SWIG from [swig.org](http://www.swig.org/download.html)
2. Extract to a path without spaces (e.g., `C:\swigwin`)
3. Add SWIG to PATH:
   - Press Win+R, type `sysdm.cpl`
   - Go to **Advanced** → **Environment Variables**
   - Add `C:\swigwin` to `Path`

Verify:
```cmd
swig -version
```

### Step 5: Compile PJSIP

1. Download PJSIP from [pjsip.org](https://pjsip.org/download.htm) or GitHub:
   ```cmd
   git clone https://github.com/pjsip/pjproject.git
   cd pjproject
   ```

2. Configure and build:
   ```cmd
   cd pjproject
   python ./configure.py
   ```

3. Open the generated solution in Visual Studio:
   - **For Visual Studio 2022**: `pjsip-apps\build\vs2022\pjsua_vc2022.sln`
   - Build the entire solution in **Release** mode

4. Build SWIG Python bindings:
   ```cmd
   cd pjsip-apps\src\swig
   python setup.py build
   python setup.py install
   ```

### Step 6: Install ffmpeg (Optional)

For audio import feature:
1. Download from [ffmpeg.org](https://ffmpeg.org/download.html#build-windows)
2. Extract and add `bin` folder to PATH

### Step 7: Install sip-player

```cmd
cd sip-player
pip install -e .
```

---

## macOS Setup

### Step 1: Install Python

Using Homebrew:
```bash
brew install python@3.12
```

Or download from [python.org](https://www.python.org/downloads/).

Verify:
```bash
python3 --version
```

### Step 2: Install tkinter

**For Homebrew Python:**
```bash
brew install python-tk@3.12
```

**For official Python installer:**
tkinter is included. Verify:
```bash
python3 -c "import tkinter; print('tkinter OK')"
```

If using pyenv, reinstall with tcl-tk support:
```bash
brew install tcl-tk
export LDFLAGS="-L$(brew --prefix tcl-tk)/lib"
export CPPFLAGS="-I$(brew --prefix tcl-tk)/include"
export PKG_CONFIG_PATH="$(brew --prefix tcl-tk)/lib/pkgconfig"
pyenv install 3.12.0
```

### Step 3: Install Dependencies

```bash
brew install swig ffmpeg
```

### Step 4: Compile PJSIP

```bash
# Clone PJSIP
git clone https://github.com/pjsip/pjproject.git
cd pjproject

# Configure with -fPIC for shared library
./configure CFLAGS="-fPIC"

# Build (5-10 minutes)
make dep && make

# Build SWIG Python bindings
cd pjsip-apps/src/swig
make

# Install pjsua2 module
cd python
python3 setup.py install
```

Verify installation:
```bash
python3 -c "import pjsua2; print('pjsua2 OK')"
```

### Step 5: Install sip-player

```bash
cd sip-player
pip3 install -e .
```

---

## Linux Setup

Tested on Ubuntu/Debian and Fedora/RHEL.

### Ubuntu/Debian

```bash
# Install Python, tkinter, and build tools
sudo apt update
sudo apt install -y python3 python3-tk python3-dev build-essential swig ffmpeg

# Install PJSIP dependencies
sudo apt install -y libssl-dev libsrtp2-dev libopus-dev libspeex-dev libgsm1-dev

# Clone and build PJSIP
git clone https://github.com/pjsip/pjproject.git
cd pjproject
./configure CFLAGS="-fPIC"
make dep && make

# Build SWIG Python bindings
cd pjsip-apps/src/swig
make
cd python
python3 setup.py install --user

# Verify
python3 -c "import pjsua2; print('pjsua2 OK')"
```

### Fedora/RHEL

```bash
# Install dependencies
sudo dnf install -y python3 python3-tkinter python3-devel gcc gcc-c++ make swig ffmpeg openssl-devel opus-devel speex-devel gsm-devel

# Clone and build PJSIP
git clone https://github.com/pjsip/pjproject.git
cd pjproject
./configure CFLAGS="-fPIC"
make dep && make

# Build SWIG Python bindings
cd pjsip-apps/src/swig
make
cd python
python3 setup.py install --user
```

### Install sip-player

```bash
cd sip-player
pip3 install -e .
```

---

## Running the Application

### GUI Mode

```bash
# Windows
python -m src

# macOS/Linux
python3 -m src
```

Or use the installed command:
```bash
sip-player
```

### DTMF Controls

During a call, use DTMF tones to control playback:

| Key | Action |
|-----|--------|
| 1 | Next track |
| 2 | Play/Pause |
| 3 | Cycle play mode |
| 4 | Previous track |

### Play Modes

1. **Sequential** - Play tracks in order, stop at end
2. **List Loop** - Loop through all tracks
3. **Single Loop** - Repeat current track
4. **Random** - Shuffle playback

---

## Configuration

Settings are automatically saved to:
- **Windows**: `%APPDATA%\sip_player\settings.json`
- **macOS**: `~/Library/Application Support/sip_player/settings.json`
- **Linux**: `~/.config/sip_player/settings.json`

Imported audio files are stored in:
- **Windows**: `%LOCALAPPDATA%\sip_player\imported_tracks\`
- **macOS**: `~/Library/Application Support/sip_player/imported_tracks/`
- **Linux**: `~/.local/share/sip_player/imported_tracks/`

---

## Troubleshooting

### PJSIP Installation Issues

**"build.mak: No such file or directory"**
- Ensure you ran `./configure` and `make dep && make` in pjproject root

**"pjsua2_wrap.cpp: No such file or directory"**
- Run `make` in `pjsip-apps/src/swig` directory

**"Cannot determine JDK include path"**
- Safe to ignore if you only need Python bindings

### macOS: "tkinter not found"

If using pyenv, reinstall Python with tcl-tk support (see Step 2 above).

### Windows: Build Errors

- Ensure Visual Studio with C++ tools is installed
- Run commands from **x64 Native Tools Command Prompt**
- Verify SWIG is in PATH

---

## License

MIT License

## References

- [PJSIP Documentation](https://docs.pjsip.org/)
- [PJSIP GitHub](https://github.com/pjsip/pjproject)
- [SWIG Documentation](https://www.swig.org/doc.html)
