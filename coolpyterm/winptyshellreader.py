"""
Windows Terminal Backend Implementation for CoolPyTerm
Integrates WinPTY with your existing SSH backend pattern
"""

import threading
import time
from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot, QTimer
from PyQt6.QtWidgets import QMessageBox


class WinPtyReaderThread(QThread):
    """
    Windows PTY Reader Thread - mirrors your ShellReaderThread pattern
    Reads from WinPTY process and emits data for Pyte processing
    """
    data_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, pty_process, parent_widget=None):
        super().__init__()
        self.pty_process = pty_process
        self.parent_widget = parent_widget
        self.running = True
        self.buffer_size = 1024

    def run(self):
        """Main thread loop - reads from WinPTY process"""
        print("🔥 WinPtyReaderThread started")

        while self.running and self.pty_process and self.pty_process.isalive():
            try:
                # Read data from WinPTY process
                if self.pty_process.isalive():
                    # Non-blocking read with timeout
                    data = self.pty_process.read(self.buffer_size)

                    if data:
                        # Convert bytes to string if needed
                        if isinstance(data, bytes):
                            try:
                                text_data = data.decode('utf-8', errors='replace')
                            except UnicodeDecodeError:
                                text_data = data.decode('latin-1', errors='replace')
                        else:
                            text_data = data

                        if text_data:
                            print(f"🔥 WinPtyReaderThread emitting {len(text_data)} chars")
                            self.data_ready.emit(text_data)
                    else:
                        # No data available, small sleep to prevent CPU spinning
                        time.sleep(0.01)
                else:
                    print("WinPTY process is no longer alive")
                    break

            except Exception as e:
                print(f"Error in WinPtyReaderThread: {e}")
                self.error_occurred.emit(str(e))
                break

        print("🔥 WinPtyReaderThread stopped")

    def stop(self):
        """Stop the reader thread"""
        self.running = False
        self.quit()
        self.wait(2000)  # Wait up to 2 seconds for thread to finish


class WindowsTerminalBackend(QObject):
    """
    Windows Terminal Backend - mirrors your SSHBackend exactly
    Uses WinPTY instead of SSH channel
    """
    send_output = pyqtSignal(str)
    connection_failed = pyqtSignal(str)
    connection_established = pyqtSignal()

    def __init__(self, shell_path="cmd.exe", working_dir=None, env_vars=None,
                 startup_command=None, parent_widget=None, parent=None):
        super().__init__(parent)
        self.parent_widget = parent_widget
        self.shell_path = shell_path
        self.working_dir = working_dir or "C:\\"
        self.env_vars = env_vars or {}
        self.startup_command = startup_command

        # WinPTY components
        self.pty_process = None
        self.reader_thread = None
        self.is_connected = False

        print(f"Initializing Windows Terminal Backend: {shell_path}")

        # Connect immediately like your SSH backend
        try:
            self._attempt_connection()
        except Exception as e:
            error_msg = f"Windows Terminal Connection Error: {str(e)}"
            print(error_msg)
            QTimer.singleShot(10, lambda: self.connection_failed.emit(error_msg))

    def _attempt_connection(self):
        """Attempt Windows terminal connection using WinPTY"""
        print("Starting Windows terminal connection...")

        try:
            # Import WinPTY - handle if not available
            try:
                from winpty import PtyProcess
            except ImportError:
                raise Exception("WinPTY not available. Please install: pip install pywinpty")

            # Determine shell command and arguments
            shell_cmd = self._get_shell_command()

            print(f"Starting: {shell_cmd}")
            print(f"Working directory: {self.working_dir}")

            # Create WinPTY process
            self.pty_process = PtyProcess.spawn(
                shell_cmd,
                cwd=self.working_dir,
                env=self._prepare_environment()
            )

            print("WinPTY process started successfully")
            self.is_connected = True

            # Signal connection ready - same pattern as SSH backend
            QTimer.singleShot(50, self._signal_connection_ready)

        except Exception as e:
            print(f"Failed to start Windows terminal: {e}")
            raise

    def _get_shell_command(self):
        """Get the appropriate shell command"""
        shell_commands = {
            "cmd.exe": "cmd.exe",
            "cmd": "cmd.exe",
            "powershell.exe": "powershell.exe",
            "powershell": "powershell.exe",
            "pwsh.exe": "pwsh.exe",
            "pwsh": "pwsh.exe",
            "wsl.exe": "wsl.exe",
            "wsl": "wsl.exe"
        }

        # Normalize shell path
        shell_key = self.shell_path.lower().strip()
        return shell_commands.get(shell_key, self.shell_path)

    def _prepare_environment(self):
        """Prepare environment variables"""
        import os
        env = os.environ.copy()

        # Add custom environment variables
        env.update(self.env_vars)

        # Set terminal-specific variables
        env['TERM'] = 'xterm'
        env['COLUMNS'] = '80'
        env['LINES'] = '24'
        env['TERMINFO'] = ''
        return env

    def _signal_connection_ready(self):
        """Signal connection ready - exactly like SSH backend"""
        print("Emitting connection_established signal...")
        self.connection_established.emit()

        # Start reader thread after signals are connected
        QTimer.singleShot(100, self._start_reader_thread)

    def _start_reader_thread(self):
        """Start the reader thread - mirrors SSH backend pattern"""
        if self.pty_process is not None:
            print("=== STARTING WINPTY READER THREAD ===")
            print("Signals should be connected by now...")

            # Create reader thread using WinPTY process
            self.reader_thread = WinPtyReaderThread(self.pty_process, self.parent_widget)

            print("Connecting WinPtyReaderThread.data_ready to WindowsTerminalBackend.send_output...")
            self.reader_thread.data_ready.connect(self._on_data_received)
            self.reader_thread.error_occurred.connect(self._on_error)

            print("Starting WinPtyReaderThread...")
            self.reader_thread.start()
            print("✅ WinPtyReaderThread started successfully")

            # Send startup command if specified
            if self.startup_command:
                QTimer.singleShot(500, lambda: self.write_data(self.startup_command + "\n"))
        else:
            print("❌ No WinPTY process available for reader thread")

    def _on_data_received(self, data):
        """Handle data from WinPtyReaderThread - exactly like SSH backend"""
        print(f"🔥 Windows Terminal Backend received data: {len(data)} chars")
        print(f"First 50 chars: {repr(data[:50])}")

        # Forward to UI via signal
        self.send_output.emit(data)
        print("✅ Data forwarded to UI via send_output signal")

    def _on_error(self, error_msg):
        """Handle errors from reader thread"""
        print(f"Error from WinPtyReaderThread: {error_msg}")
        self.connection_failed.emit(error_msg)

    @pyqtSlot(str)
    def write_data(self, data):
        """Write data to WinPTY process - matches SSH backend API exactly"""
        if not self.is_connected:
            print("Error: Not connected to terminal")
            return

        if self.pty_process and self.pty_process.isalive():
            try:
                # Convert string to bytes if needed
                if isinstance(data, str):
                    data_bytes = data.encode('utf-8')
                else:
                    data_bytes = data

                self.pty_process.write(data_bytes)
                print(f"✅ Sent data to terminal: {repr(data[:50])}")
            except Exception as e:
                print(f"Error writing to terminal: {e}")
                self.is_connected = False
        else:
            print("Error: Terminal process is not alive")



    @pyqtSlot(str)
    def set_pty_size(self, data):
        """Set PTY size - matches SSH backend API exactly"""
        if not self.is_connected:
            return

        if self.pty_process and self.pty_process.isalive():
            try:
                # Parse your format: "cols:80::rows:24"
                cols = data.split("::")[0]
                cols = int(cols.split(":")[1])
                rows = data.split("::")[1]
                rows = int(rows.split(":")[1])

                self.pty_process.setwinsize(rows, cols)
                print(f"Windows terminal pty resize -> cols:{cols} rows:{rows}")
            except Exception as e:
                print(f"Error setting terminal pty size: {e}")

    def close(self):
        """Clean up resources - matches SSH backend pattern"""
        self.is_connected = False
        print("Closing Windows terminal backend...")

        try:
            if self.reader_thread and self.reader_thread.isRunning():
                print("Stopping reader thread...")
                self.reader_thread.stop()
                print("Reader thread stopped")
        except Exception as e:
            print(f"Error stopping reader thread: {e}")

        try:
            if self.pty_process and self.pty_process.isalive():
                print("Terminating WinPTY process...")
                self.pty_process.terminate()
                print("WinPTY process terminated")
        except Exception as e:
            print(f"Error terminating WinPTY process: {e}")

    # Add this method to your WindowsTerminalBackend class in winptyshellreader.py
    # (Just add this one method - don't replace the whole class)

    def send_command(self, data):
        """Compatibility method for KeyHandler - matches SSH backend exactly"""
        print(f"🔑 WindowsTerminalBackend.send_command called with: {repr(data)}")

        if isinstance(data, bytes):
            data_str = data.decode('utf-8')
        else:
            data_str = data

        self.write_data(data_str)

    # Also, let's enhance the write_data method to be more robust:
    # Replace your existing write_data method in WindowsTerminalBackend with this:


# Replace your write_data method in WindowsTerminalBackend (winptyshellreader.py) with this:

    @pyqtSlot(str)
    def write_data(self, data):
        """Write data to WinPTY process - matches SSH backend API exactly"""
        if not self.is_connected:
            print("Error: Not connected to terminal")
            return

        if self.pty_process and self.pty_process.isalive():
            try:
                # WinPTY expects STRING, not bytes!
                if isinstance(data, bytes):
                    data_str = data.decode('utf-8')
                else:
                    data_str = data

                print(f"✅ Writing to WinPTY (as string): {repr(data_str[:50])}")
                self.pty_process.write(data_str)  # Send string, not bytes
                print(f"✅ Successfully sent to terminal: {repr(data_str[:50])}")
            except Exception as e:
                print(f"Error writing to terminal: {e}")
                import traceback
                traceback.print_exc()
                self.is_connected = False
        else:
            print("Error: Terminal process is not alive")
            if self.pty_process:
                print(f"Process alive status: {self.pty_process.isalive()}")
            else:
                print("No pty_process available")


# Also update your send_command method to be consistent:

    def send_command(self, data):
        """Compatibility method for KeyHandler - matches SSH backend exactly"""
        print(f"🔑 WindowsTerminalBackend.send_command called with: {repr(data)}")

        # Convert bytes to string if needed, then call write_data
        if isinstance(data, bytes):
            data_str = data.decode('utf-8')
        else:
            data_str = data

        print(f"🔑 Converted to string: {repr(data_str)}")
        self.write_data(data_str)  # Always pass string to write_data
def get_available_windows_shells():
    """
    Detect available Windows shells for connection dialog
    """
    import shutil
    import subprocess
    import os

    shells = []

    # Command Prompt (always available on Windows)
    cmd_path = shutil.which("cmd.exe") or r"C:\Windows\System32\cmd.exe"
    if os.path.exists(cmd_path):
        shells.append({
            "name": "Command Prompt",
            "description": "Windows Command Prompt",
            "shell_path": "cmd.exe",
            "type": "cmd"
        })

    # PowerShell (multiple versions)
    powershell_variants = [
        ("powershell.exe", "Windows PowerShell 5.x"),
        ("pwsh.exe", "PowerShell Core 7.x")
    ]

    for ps_exe, ps_desc in powershell_variants:
        if shutil.which(ps_exe):
            shells.append({
                "name": f"PowerShell ({ps_exe})",
                "description": ps_desc,
                "shell_path": ps_exe,
                "type": "powershell"
            })

    # Windows Subsystem for Linux
    try:
        # Check if WSL is available
        result = subprocess.run(
            ["wsl", "--list", "--quiet"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0 and result.stdout.strip():
            # WSL is available
            shells.append({
                "name": "WSL (Default Distribution)",
                "description": "Windows Subsystem for Linux",
                "shell_path": "wsl.exe",
                "type": "wsl"
            })

            # List specific distributions
            distributions = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            for distro in distributions:
                if distro and not distro.startswith('*'):  # Skip default marker
                    shells.append({
                        "name": f"WSL ({distro})",
                        "description": f"WSL Distribution: {distro}",
                        "shell_path": f"wsl.exe -d {distro}",
                        "type": "wsl"
                    })

    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        print("WSL not available or not accessible")

    return shells


# Backend factory function for integration with existing code
def create_windows_terminal_backend(connection_config, parent_widget):
    """
    Factory function to create Windows terminal backend
    Integrates with your existing backend creation pattern
    """
    return WindowsTerminalBackend(
        shell_path=connection_config.get('shell_path', 'cmd.exe'),
        working_dir=connection_config.get('working_dir'),
        env_vars=connection_config.get('env_vars', {}),
        startup_command=connection_config.get('startup_command'),
        parent_widget=parent_widget
    )

