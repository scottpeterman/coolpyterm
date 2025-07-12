# CoolPyTerm

A hardware-accelerated SSH terminal emulator with authentic retro CRT effects, built with PyQt6 and OpenGL.  Inspired by the Cool Retro Terminal project.

![CoolPyTerm Screenshot](https://raw.githubusercontent.com/scottpeterman/coolpyterm/refs/heads/main/screenshots/slides1.gif)

## Features

### Advanced Connection Management

* **Connection Profiles**: Save, organize, and manage multiple connection profiles (SSH and Local).
* **Recent Connections**: Quick access to recently used connections.
* **Authentication Support**: Password and SSH key authentication for SSH connections.
* **Connection Dialog**: Enhanced UI with password fields, key file browser, and shell selection.
* **Profile Management**: Create, edit, and delete connection profiles.

### Local Terminal Support (Windows Only)

* **CMD, PowerShell, WSL**: Seamlessly connect to Command Prompt, PowerShell, or Windows Subsystem for Linux.
* **Shell Detection**: Automatic detection of available shells and WSL distributions.
* **Working Directory**: Specify the starting directory for local sessions.
* **Startup Command**: Execute a command automatically when a local terminal session begins.

### Hardware-Accelerated Terminal

* **OpenGL Rendering**: Smooth, hardware-accelerated text rendering.
* **Full Screen Support**: Immersive full-screen terminal experience.
* **Dynamic Resizing**: Automatic terminal resizing with proper PTY handling.
* **Character Grid**: Efficient grid-based text rendering system.

### Authentic CRT Effects

* **Phosphor Glow**: Realistic phosphor afterglow effects.
* **Scanlines**: Adjustable CRT scanline simulation.
* **Screen Curvature**: Subtle barrel distortion for authenticity.
* **Ambient Background Glow**: Subtle phosphor illumination across the screen.
* **Brightness & Contrast**: Adjustable CRT-style image controls.
* **Auto-DPI Scaling**: Automatic effect adjustment based on screen resolution.

### Retro Themes

* **Green Phosphor**: Classic green monochrome CRT terminal.
* **Amber Phosphor**: Warm amber terminal with enhanced glow.
* **DOS Terminal**: Retro blue DOS-style terminal.

### Terminal Features

* **Full ANSI Support**: Complete terminal emulation with color support.
* **Scrollback Buffer**: History navigation and scrolling.
* **Cursor Control**: Blinking cursor with adjustable rate.
* **Key Mapping**: Comprehensive SSH key handling and local terminal input.
* **Clipboard Support**: Copy/paste functionality.

## Installation

### Prerequisites

* Python 3.10+
* PyQt6
* PyOpenGL (for hardware acceleration)
* Paramiko (for SSH connections)
* Pywinpty (for local Windows terminals)

### Install Dependencies

```bash
pip install -r requirements.txt
````

### Required Packages

```
PyQt6
PyOpenGL
PyOpenGL_accelerate
paramiko
pyte
numpy
pywinpty  # New dependency for Windows local terminal support
```

## Usage

### Starting the Application

```bash
python -m coolpyterm.cpt
```

### First Run

1.  **Connection Dialog**: The application starts with a connection dialog.
2.  **Select Connection Type**: Choose "SSH" for remote connections or "Local Shell" for a local Windows terminal.
3.  **Enter Details**:
      * **SSH**: Hostname, username, password/key file.
      * **Local Shell**: Select an available shell (CMD, PowerShell, WSL), optionally specify a working directory or startup command.
4.  **Save Profile**: Optionally save connection details for future use.
5.  **Connect**: Click "Connect" to establish the session.

### Connection Management

  * **Ctrl+M**: Open connection manager.
  * **Ctrl+N**: Create new connection.
  * **Double-click**: Connect to saved profile instantly.

## Keyboard Shortcuts

### Application Controls

  * **Ctrl+Alt+F11**: Toggle full screen mode.
  * **Ctrl+Q**: Quit application.
  * **Ctrl+V**: Paste from clipboard.
  * **Escape**: Exit full screen (in full screen mode).

### Visual Effects

  * **Ctrl+G**: Toggle phosphor glow.
  * **Ctrl+S**: Toggle scanlines.
  * **Ctrl+Shift+A**: Toggle ambient background glow.
  * **Ctrl+Alt+I**: Increase ambient glow intensity.
  * **Ctrl+Alt+O**: Decrease ambient glow intensity.

### Terminal Controls

  * **Standard SSH keys**: All standard terminal key combinations work.
  * **Function keys**: F1-F12 support.
  * **Arrow keys**: Navigation support.
  * **Ctrl+C**: Send SIGINT.
  * **Ctrl+D**: Send EOF.
  * **Ctrl+Z**: Send SIGTSTP.

## Themes

### Green Phosphor (Default)

Classic green monochrome CRT appearance with moderate phosphor persistence and subtle background glow.

### Amber Phosphor

Warm amber coloring reminiscent of early computer terminals, with enhanced background glow for that cozy retro feel.

### DOS Terminal

Blue-tinted terminal mimicking classic DOS and early PC interfaces with crisp, high-contrast appearance.

## Configuration

### Settings

  * Connection profiles are automatically saved.
  * Window geometry and state persistence.
  * Theme preferences.
  * Effect intensity settings.

### Auto-Adjustment Features

  * **Scanline DPI Scaling**: Automatically adjusts scanline intensity based on screen DPI.
  * **Font Scaling**: Responsive font sizing.
  * **Effect Optimization**: Performance-optimized rendering.

## Advanced Features

### Full Screen Mode

  * **Borderless Display**: True full screen experience.
  * **Menu-Free Interface**: Clean, distraction-free terminal.
  * **Proper Geometry**: Exact screen coverage.
  * **Easy Exit**: Escape key or Ctrl+Alt+F11.

### CRT Authenticity

  * **Phosphor Persistence**: Realistic afterglow simulation.
  * **Variable Intensity**: Adjustable effect levels.
  * **Theme Integration**: Effects tailored to each theme.
  * **Hardware Acceleration**: Smooth 60fps rendering.

### Connection Features

  * **Recent History**: Track and prioritize recent connections.
  * **Profile Export/Import**: (Planned feature)
  * **Connection Validation**: Pre-connection testing.
  * **Error Handling**: Graceful connection failure management.

## Development

### Project Structure

```
coolpyterm/
├── cpt.py                    # Main application entry point
├── connection_manager.py     # SSH and Local connection management
├── opengl_grid_widget.py    # Hardware-accelerated rendering
├── retro_theme_manager.py   # Theme system
├── ssh_backend.py           # SSH connection handling
├── winptyshellreader.py     # Windows local terminal backend
├── key_handler_ssh.py       # Keyboard input processing
├── settings_manager.py      # Configuration management
└── logs/                    # Application logs
```

### Key Components

  * **OpenGL Shaders**: Custom fragment shaders for CRT effects.
  * **SSH Backend**: Paramiko-based SSH client.
  * **Windows Terminal Backend**: `pywinpty`-based local shell integration for Windows.
  * **Grid Rendering**: Efficient character grid system.
  * **Theme Engine**: Extensible color scheme system.

## System Requirements

### Minimum Requirements

  * **OS**: Windows 10, macOS 10.14, or Linux.
  * **Python**: 3.10 or higher.
  * **Graphics**: OpenGL 3.3 support.

### Recommended

  * **Graphics**: Dedicated GPU for best performance.
  * **Display**: High DPI display for optimal scanline effects.
  * **Memory**: 1GB+ RAM for large scrollback buffers.

## Troubleshooting

### OpenGL Issues

```bash
# Check OpenGL support
python -m coolpyterm.checkogl
```

### Connection Problems

  * Verify SSH credentials.
  * Check network connectivity.
  * For local Windows terminals, ensure `pywinpty` is installed.
  * Review connection logs in `logs/` directory.

### Performance Issues

  * Disable effects on slower systems.
  * Reduce font size for better performance.
  * Use windowed mode instead of full screen.

# Building Distributions with setup.py

## 1\. Development Installation

```bash
# Install in development/editable mode
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"

# Test the installation
coolpyterm
python -m coolpyterm
```

## 2\. Building Wheel Distribution

```bash
# Install build dependencies
pip install wheel setuptools

# Build wheel (recommended format)
python setup.py bdist_wheel

# Creates: dist/coolpyterm-1.0.0-py3-none-any.whl
```

## 3\. Building Source Distribution

```bash
# Build source distribution (tarball)
python setup.py sdist

# Creates: dist/coolpyterm-1.0.0.tar.gz
```

## 4\. Building Both Wheel and Source

```bash
# Build both wheel and source distribution
python setup.py sdist bdist_wheel

# Creates both:
# dist/coolpyterm-1.0.0.tar.gz
# dist/coolpyterm-1.0.0-py3-none-any.whl
```

## 5\. Clean Build (Recommended)

```bash
# Clean previous builds
python setup.py clean --all
rm -rf build/ dist/ *.egg-info/

# Fresh build
python setup.py sdist bdist_wheel

# Verify contents
twine check dist/*
```

## Windows Build Commands

```cmd
# Windows equivalent of clean build
python setup.py clean --all
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
for /d %%i in (*.egg-info) do rmdir /s /q "%%i"

# Build distributions
python setup.py sdist bdist_wheel

# Verify
twine check dist\*
```

## Upload to PyPI

```bash
# Install upload tools
pip install twine

# Check distributions before upload
twine check dist/*

# Upload to Test PyPI first (recommended)
twine upload --repository testpypi dist/*

# Upload to real PyPI
twine upload dist/*
```

## License
- GPLv3 - see license file

## Acknowledgments

  * **PyQt6**: For the excellent GUI framework.
  * **OpenGL**: For hardware acceleration capabilities.
  * **Paramiko**: For robust SSH connectivity.
  * **Pyte**: For terminal emulation support.
  * **Pywinpty**: For Windows pseudo-terminal support.

-----

**CoolPyTerm** - Where modern technology meets retro aesthetics. Experience the nostalgia of classic terminals with the power of contemporary hardware acceleration. https://github.com/scottpeterman/coolpyterm

