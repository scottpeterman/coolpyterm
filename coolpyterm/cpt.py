import os
import sys
import signal
import atexit

from PyQt6.QtWidgets import (QWidget, QApplication, QMainWindow, QVBoxLayout)
from PyQt6.QtCore import QTimer, Qt, pyqtSlot, QRect, QThread
from PyQt6.QtGui import QAction, QActionGroup, QFont, QFontMetrics, QColor, QPainter, QPen, QBrush, QImage, QKeySequence
import pyte
from pyte.screens import HistoryScreen
from coolpyterm.backend_factory import create_backend

from coolpyterm.connection_manager import ConnectionManager, ConnectionProfile, ConnectionDialog
from coolpyterm.opengl_grid_widget import OpenGLRetroGridWidget

try:
    from OpenGL.GL import *
    OPENGL_AVAILABLE = True
except ImportError:
    print("PyOpenGL not available. Install with: pip install PyOpenGL PyOpenGL_accelerate")
    OPENGL_AVAILABLE = False

# Import your existing components
from coolpyterm.ssh_backend import SSHBackend
from coolpyterm.key_handler_ssh import KeyHandler
from coolpyterm.retro_theme_manager import RetroThemeManager
from coolpyterm.settings_manager import SettingsManager, EnhancedTerminalMixin



# Enhanced Connection Dialog with password field and actual connection logic
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout,  QMessageBox
)


class TerminalWithHardwareGrid(QWidget):
    """
    Terminal widget using your grid approach with hardware acceleration
    """

    def __init__(self, parent=None, ssh_config=None, log_file=None, font_size=12, theme_manager=None, **kwargs):
        """Updated initialization mentioning background glow"""
        super().__init__(parent)
        self.grid_widget = None
        self.widget_id = None
        self._is_closing = False  # Flag to prevent operations during shutdown

        # Handle log file setup - required by SSH backend
        if log_file:
            log_dir = os.path.dirname(log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            self.log_filename = log_file
        else:
            self.log_filename = None
        self.debug_counter = 0

        # Initialize required attributes
        self.initial_buffer = ""
        self.scroll_offset = 0
        self.in_alternate_screen = False
        self.scrollback_buffer = []
        self.max_scrollback_size = 1000

        # Theme manager setup
        self.theme_manager = theme_manager or RetroThemeManager()
        self.theme_manager.set_current_theme("green")
        self.current_theme = self.theme_manager.get_current_theme()

        # Create the hardware-accelerated grid widget
        if not hasattr(self, 'grid_widget') or self.grid_widget is None:
            self.grid_widget = OpenGLRetroGridWidget(
                parent=self,
                font_size=font_size,
                theme_manager=self.theme_manager
            )
            print(f"Created OpenGL grid widget for terminal {self.widget_id}")

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.grid_widget)

        # Terminal state
        self.rows = 24
        self.cols = 80

        # Pyte components - same as your original approach
        self.screen = HistoryScreen(self.cols, self.rows)
        self.stream = self._create_safe_pyte_stream()
        self._patch_pyte_compatibility()

        # SSH backend setup - WILL BE SET LATER via connect_to_ssh
        self.ssh_backend = None

        # Focus setup
        self.grid_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Resize handling
        self.grid_widget.resizeEvent = self.on_grid_resize

        print("Terminal initialized - ready for SSH connection")

    # Add these methods to your TerminalWithHardwareGrid class in cpt.py
    # Add them after your existing connect_to_ssh method

    def connect_to_local_terminal(self, connection_config):
        """Connect to local terminal with given configuration"""
        if self._is_closing:
            return False

        try:
            print(f"Connecting to local terminal: {connection_config}")

            # Import and use the backend factory
            from coolpyterm.backend_factory import create_backend

            # Create appropriate backend (Windows terminal)
            self.ssh_backend = create_backend(connection_config, self)

            # Connect signals (same as SSH)
            self.ssh_backend.send_output.connect(self.update_ui)
            self.ssh_backend.connection_established.connect(self.on_local_terminal_connected)
            self.ssh_backend.connection_failed.connect(self.on_local_terminal_failed)

            print("Local terminal backend established successfully")
            return True

        except Exception as e:
            print(f"Failed to establish local terminal backend: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(None, "Connection Failed", f"Failed to connect to local terminal:\n{str(e)}")
            self.ssh_backend = None
            return False

    def on_local_terminal_connected(self):
        """Handle successful local terminal connection"""
        print("Local terminal connected successfully!")

    def on_local_terminal_failed(self, error_msg):
        """Handle failed local terminal connection"""
        print(f"Local terminal connection failed: {error_msg}")
        QMessageBox.critical(None, "Terminal Connection Failed", f"Failed to connect to terminal:\n{error_msg}")

    def on_ssh_connected(self):
        """Handle successful SSH connection"""
        print("SSH connected successfully!")

    def on_ssh_failed(self, error_msg):
        """Handle failed SSH connection"""
        print(f"SSH connection failed: {error_msg}")
        QMessageBox.critical(None, "SSH Connection Failed", f"Failed to connect to SSH server:\n{error_msg}")



    def connect_to_ssh(self, ssh_config):
        """Connect to SSH server with given configuration"""
        if self._is_closing:
            return False

        try:
            print(f"Connecting to SSH: {ssh_config['username']}@{ssh_config['hostname']}:{ssh_config['port']}")

            self.ssh_backend = SSHBackend(
                host=ssh_config['hostname'],
                username=ssh_config['username'],
                password=ssh_config.get('password'),
                port=ssh_config.get('port', 22),
                key_path=ssh_config.get('key_path'),
                parent_widget=self,
                parent=self
            )
            self.ssh_backend.send_output.connect(self.update_ui)
            print("SSH backend established successfully")
            return True

        except Exception as e:
            print(f"Failed to establish SSH backend: {e}")
            QMessageBox.critical(None, "Connection Failed", f"Failed to connect to SSH server:\n{str(e)}")
            self.ssh_backend = None
            return False

    def _create_safe_pyte_stream(self):
        """Create a pyte stream with improved error handling"""
        try:
            stream = pyte.ByteStream()
            stream.attach(self.screen)

            original_feed = stream.feed

            def safe_feed(data):
                if self._is_closing:
                    return
                try:
                    return original_feed(data)
                except TypeError as e:
                    if 'unexpected keyword argument' in str(e):
                        print(f"Pyte compatibility error (continuing): {e}")
                        return
                    else:
                        raise
                except Exception as e:
                    print(f"Pyte feed error (continuing): {e}")
                    return

            stream.feed = safe_feed
            return stream

        except Exception as e:
            print(f"Failed to create safe pyte stream: {e}")
            stream = pyte.ByteStream()
            stream.attach(self.screen)
            return stream

    def _patch_pyte_compatibility(self):
        """Comprehensive pyte compatibility patch"""
        try:
            original_sgr = self.screen.select_graphic_rendition

            def patched_sgr(*args, **kwargs):
                if self._is_closing:
                    return None
                kwargs.pop('private', None)
                kwargs.pop('intermediate', None)
                try:
                    return original_sgr(*args, **kwargs)
                except Exception as e:
                    print(f"SGR error (continuing): {e}")
                    return None

            self.screen.select_graphic_rendition = patched_sgr

            methods_to_patch = ['set_mode', 'reset_mode', 'set_margins', 'cursor_position']

            for method_name in methods_to_patch:
                if hasattr(self.screen, method_name):
                    original_method = getattr(self.screen, method_name)

                    def create_patched_method(orig_method, name):
                        def patched_method(*args, **kwargs):
                            if self._is_closing:
                                return None
                            kwargs.pop('private', None)
                            kwargs.pop('intermediate', None)
                            try:
                                return orig_method(*args, **kwargs)
                            except Exception as e:
                                print(f"{name} error (continuing): {e}")
                                return None
                        return patched_method

                    setattr(self.screen, method_name, create_patched_method(original_method, method_name))

            print("Applied comprehensive pyte compatibility patches")

        except Exception as e:
            print(f"Pyte patch failed: {e}")

    def on_grid_resize(self, event):
        """Handle grid widget resize - PROPERLY FIXED"""
        if self._is_closing:
            return

        print(f"Terminal {self.widget_id} resize called")

        new_cols = self.grid_widget.cols
        new_rows = self.grid_widget.rows

        # Only update if actually changed
        if new_cols == self.cols and new_rows == self.rows:
            print(f"Terminal {self.widget_id} - no size change, ignoring")
            return

        print(f"Terminal {self.widget_id} resize: {self.cols}x{self.rows} -> {new_cols}x{new_rows}")

        self.cols = new_cols
        self.rows = new_rows

        # Resize the pyte screen
        self.screen.resize(new_rows, new_cols)

        # Notify SSH backend
        if self.ssh_backend and not self._is_closing:
            pty_data = f"cols:{new_cols}::rows:{new_rows}"
            self.ssh_backend.set_pty_size(pty_data)

        self.redraw()

    @pyqtSlot(str)
    def update_ui(self, data):
        """Update UI with SSH data - uses your grid approach"""
        if self._is_closing:
            return

        print(f"Received data: {data[:50]}...")

        # Convert string to bytes for pyte
        data_bytes = data.encode('utf-8')
        self.stream.feed(data_bytes)

        # Handle escape sequences
        self.handle_escape_sequences(data)

        # Handle scrollback
        if not self.in_alternate_screen:
            while len(self.screen.dirty) > 0:
                line_index = self.screen.dirty.pop()
                if line_index < len(self.screen.buffer):
                    line = self.screen.buffer[line_index]
                    self.add_to_scrollback(line)

        # Redraw screen
        self.redraw()
        self.update_cursor()

    def handle_escape_sequences(self, data_str):
        """Handle escape sequences"""
        if self._is_closing:
            return

        if "\x1b[?1049h" in data_str:
            self.in_alternate_screen = True
            self.redraw()
        elif "\x1b[?1049l" in data_str:
            self.in_alternate_screen = False
            self.redraw()

    def add_to_scrollback(self, line):
        """Add to scrollback buffer"""
        if self._is_closing:
            return

        if len(self.scrollback_buffer) >= self.max_scrollback_size:
            self.scrollback_buffer.pop(0)
        self.scrollback_buffer.append(line)

    def redraw(self):
        """Redraw terminal using your grid approach"""
        if self._is_closing:
            return

        try:
            self.grid_widget.clear_screen()

            if self.in_alternate_screen:
                # Alternate screen mode
                for display_idx, line in enumerate(self.screen.display):
                    if display_idx >= self.grid_widget.rows:
                        break

                    line_str = ""
                    if isinstance(line, str):
                        line_str = line
                    else:
                        for char in line:
                            if hasattr(char, 'data'):
                                line_str += char.data
                            else:
                                line_str += str(char)

                    for col, char in enumerate(line_str):
                        if col >= self.grid_widget.cols:
                            break
                        self.grid_widget.set_char(display_idx, col, char)

                self._apply_colors_alternate_screen()

            else:
                # Normal mode with history
                history_lines = []
                try:
                    if hasattr(self.screen, 'history') and hasattr(self.screen.history, 'top'):
                        for line_dict in self.screen.history.top:
                            processed_line = ""
                            if isinstance(line_dict, dict):
                                for index in sorted(line_dict.keys()):
                                    char = line_dict[index]
                                    if hasattr(char, 'data'):
                                        processed_line += char.data
                                    else:
                                        processed_line += str(char)
                            history_lines.append(processed_line)
                except Exception as e:
                    print(f"Error extracting history: {e}")
                    history_lines = []

                # Combine history with current screen
                combined_lines = history_lines[:]

                for line in self.screen.display:
                    if isinstance(line, str):
                        combined_lines.append(line)
                    else:
                        line_str = ""
                        for char in line:
                            if hasattr(char, 'data'):
                                line_str += char.data
                            else:
                                line_str += str(char)
                        combined_lines.append(line_str)

                # Calculate display window
                rows = self.grid_widget.rows
                total_lines = len(combined_lines)

                if total_lines > rows:
                    start_line = total_lines - rows
                    lines_to_display = combined_lines[start_line:]
                    offset = total_lines - len(self.screen.display) - start_line
                else:
                    lines_to_display = combined_lines
                    start_line = 0
                    offset = len(history_lines)

                # Render content to grid
                for display_idx, line_text in enumerate(lines_to_display):
                    if display_idx >= rows:
                        break
                    for col, char in enumerate(line_text):
                        if col >= self.grid_widget.cols:
                            break
                        self.grid_widget.set_char(display_idx, col, char)

                # Apply colors with correct offset
                self._apply_colors_simple(max(0, offset))

        except Exception as e:
            if not self._is_closing:
                print(f"Error in redraw: {e}")
                import traceback
                traceback.print_exc()

    def _apply_colors_simple(self, offset):
        """Apply colors in normal mode"""
        if self._is_closing:
            return

        try:
            current_theme = self.theme_manager.get_current_theme()

            for y, line in enumerate(self.screen.display):
                for x, char in enumerate(line):
                    if y < len(self.screen.buffer) and x < len(self.screen.buffer[y]):
                        char_style = self.screen.buffer[y][x]

                        # Map colors using theme manager
                        fg_color = current_theme.foreground
                        bg_color = current_theme.background

                        if hasattr(char_style, 'fg') and char_style.fg:
                            fg_color = self.theme_manager.map_pyte_color(char_style.fg, current_theme)

                        if hasattr(char_style, 'bg') and char_style.bg and char_style.bg != "default":
                            bg_color = self.theme_manager.map_pyte_color(char_style.bg, current_theme)

                        char_data = char_style.data if hasattr(char_style, 'data') else ' '
                        is_bold = getattr(char_style, 'bold', False)
                        is_underline = getattr(char_style, 'underline', False)

                        adjusted_line_num = y + offset

                        if adjusted_line_num >= 0 and adjusted_line_num < self.grid_widget.rows:
                            self.grid_widget.set_char(
                                adjusted_line_num, x, char_data,
                                fg_color=fg_color,
                                bg_color=bg_color,
                                bold=is_bold,
                                underline=is_underline
                            )
        except Exception as e:
            if not self._is_closing:
                print(f"Error applying simple colors: {e}")

    def _apply_colors_alternate_screen(self):
        """Apply colors in alternate screen mode"""
        if self._is_closing:
            return

        try:
            current_theme = self.theme_manager.get_current_theme()

            for y, line in enumerate(self.screen.display):
                if y >= self.grid_widget.rows:
                    break

                for x, char in enumerate(line):
                    if x >= self.grid_widget.cols:
                        break

                    if y < len(self.screen.buffer) and x < len(self.screen.buffer[y]):
                        char_style = self.screen.buffer[y][x]

                        fg_color = current_theme.foreground
                        bg_color = current_theme.background

                        if hasattr(char_style, 'fg') and char_style.fg:
                            fg_color = self.theme_manager.map_pyte_color(char_style.fg, current_theme)

                        if hasattr(char_style, 'bg') and char_style.bg and char_style.bg != "default":
                            bg_color = self.theme_manager.map_pyte_color(char_style.bg, current_theme)

                        char_data = char_style.data if hasattr(char_style, 'data') else ' '
                        is_bold = getattr(char_style, 'bold', False)
                        is_underline = getattr(char_style, 'underline', False)

                        self.grid_widget.set_char(
                            y, x, char_data,
                            fg_color=fg_color,
                            bg_color=bg_color,
                            bold=is_bold,
                            underline=is_underline
                        )
        except Exception as e:
            if not self._is_closing:
                print(f"Error applying alternate screen colors: {e}")

    def update_cursor(self):
        """Update cursor position"""
        if self._is_closing:
            return

        try:
            if self.in_alternate_screen:
                cursor_row = self.screen.cursor.y
                cursor_col = self.screen.cursor.x
            else:
                total_lines_in_widget = self.grid_widget.rows
                lines_from_bottom = self.screen.lines - self.screen.cursor.y
                cursor_row = total_lines_in_widget - lines_from_bottom
                cursor_col = self.screen.cursor.x

            # Bounds checking
            cursor_row = max(0, min(cursor_row, self.grid_widget.rows - 1))
            cursor_col = max(0, min(cursor_col, self.grid_widget.cols - 1))

            self.grid_widget.set_cursor_position(cursor_row, cursor_col)

        except Exception as e:
            if not self._is_closing:
                print(f"Error updating cursor: {e}")

    def keyPressEvent(self, event):
        """Handle key press events - ENHANCED DEBUG VERSION"""
        if self._is_closing:
            return

        print(f"🔑 Key pressed: {event.key()}, text: '{event.text()}', modifiers: {event.modifiers()}")
        print(f"🔑 Backend type: {type(self.ssh_backend)}")
        print(
            f"🔑 Backend has send_command: {hasattr(self.ssh_backend, 'send_command') if self.ssh_backend else 'No backend'}")
        print(
            f"🔑 Backend has write_data: {hasattr(self.ssh_backend, 'write_data') if self.ssh_backend else 'No backend'}")

        if self.ssh_backend:
            handled = KeyHandler.handle_key_event(event, self.ssh_backend)
            print(f"🔑 Key handled by KeyHandler: {handled}")
            if handled:
                return
        else:
            print("🔑 No backend available for key handling")

        super().keyPressEvent(event)

    def focusInEvent(self, event):
        """Handle focus in events"""
        if self._is_closing:
            return

        super().focusInEvent(event)
        self.grid_widget.setFocus()

    def paste_from_clipboard(self):
        """Paste from clipboard"""
        if self._is_closing:
            return

        try:
            clipboard = QApplication.clipboard()
            text = clipboard.text()
            if text and self.ssh_backend:
                if hasattr(KeyHandler, 'handle_paste'):
                    KeyHandler.handle_paste(text, self.ssh_backend)
                else:
                    self.ssh_backend.write_data(text)
        except Exception as e:
            print(f"Paste error: {e}")

    def send_command(self, command):
        """Send command to SSH"""
        if self._is_closing:
            return

        if self.ssh_backend:
            self.ssh_backend.write_data(command)

    def set_theme(self, theme_name):
        """CRITICAL FIX: Don't recreate widget on theme change"""
        if self._is_closing:
            return

        print(f"Terminal {self.widget_id} setting theme to: {theme_name}")

        # Update theme manager
        self.theme_manager.set_current_theme(theme_name)
        self.current_theme = self.theme_manager.get_current_theme()

        # CRITICAL: Just update existing widget, don't recreate!
        if hasattr(self.grid_widget, 'set_theme'):
            self.grid_widget.set_theme(theme_name)

        # Force redraw without recreating
        self.redraw()

        print(f"Terminal {self.widget_id} theme applied: {theme_name}")

    def toggle_background_glow(self):
        """NEW: Toggle background glow (replaces toggle_flicker)"""
        if self._is_closing:
            return
        self.grid_widget.toggle_background_glow()

    def toggle_glow(self):
        """Toggle glow effect"""
        if self._is_closing:
            return
        self.grid_widget.toggle_glow()

    def toggle_scanlines(self):
        """Toggle scanlines effect"""
        if self._is_closing:
            return
        self.grid_widget.toggle_scanlines()

    def close(self):
        """Clean up resources"""
        print(f"Terminal {self.widget_id} starting cleanup...")
        self._is_closing = True

        try:
            # Disconnect SSH backend signals first
            if self.ssh_backend:
                try:
                    self.ssh_backend.send_output.disconnect()
                except:
                    pass

                # Close SSH connection
                self.ssh_backend.close()
                self.ssh_backend = None
                print(f"Terminal {self.widget_id} SSH backend closed")

            # Clean up grid widget
            if self.grid_widget:
                try:
                    self.grid_widget.setParent(None)
                    self.grid_widget.deleteLater()
                    self.grid_widget = None
                    print(f"Terminal {self.widget_id} grid widget cleaned up")
                except:
                    pass

        except Exception as e:
            print(f"Error during terminal cleanup: {e}")

        print(f"Terminal {self.widget_id} cleanup completed")

    def __del__(self):
        """Track widget destruction"""
        print(f"Terminal widget {self.widget_id} destroyed")


class HardwareTerminalWindow(QMainWindow):
    """
    Main window with hardware-accelerated terminal and full screen support
    NOW STARTS WITH CONNECTION DIALOG FIRST
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hardware-Accelerated SSH Terminal with Retro Effects")
        self.setGeometry(100, 100, 1200, 800)

        # Full screen state tracking
        self.is_fullscreen = False
        self.window_id = None
        self.windowed_geometry = None
        self.windowed_state = None
        self.terminal = None
        self._is_closing = False

        # Create theme manager
        self.theme_manager = RetroThemeManager()
        self.theme_manager.set_current_theme("green")

        # Create settings manager and connection manager
        self.settings_manager = SettingsManager()
        self.connection_manager = ConnectionManager(self.settings_manager)

        # Create placeholder terminal (no SSH connection yet)
        self.terminal = TerminalWithHardwareGrid(
            ssh_config=None,  # No SSH config yet
            log_file="logs/hardware_terminal.log",
            font_size=12,
            theme_manager=self.theme_manager
        )
        self.setCentralWidget(self.terminal)

        # Create menu system
        self.create_menu_system()

        # Install event filter for global shortcuts
        self.installEventFilter(self)

        # Setup signal handlers for clean shutdown
        self.setup_signal_handlers()

        # Show connection dialog immediately
        self.show_connection_dialog()

    def setup_signal_handlers(self):
        """Setup signal handlers for clean shutdown"""
        def signal_handler(signum, frame):
            print(f"Received signal {signum}, shutting down cleanly...")
            self.close_application()

        # Handle common termination signals
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Register cleanup function
        atexit.register(self.cleanup_on_exit)

    def cleanup_on_exit(self):
        """Cleanup function called on exit"""
        print("Application cleanup on exit...")
        if hasattr(self, 'terminal') and self.terminal:
            self.terminal.close()

    # Add this method to your HardwareTerminalWindow class in cpt.py
    # or replace the existing auto_adjust_scanlines method

    def auto_adjust_scanlines(self):
        """Auto-adjust scanlines for current display with error handling"""
        if not hasattr(self, 'terminal') or not self.terminal or self._is_closing:
            print("No terminal available for scanline adjustment")
            return

        try:
            # Check if the method exists
            if hasattr(self.terminal.grid_widget, 'adjust_scanlines_for_dpi'):
                intensity = self.terminal.grid_widget.adjust_scanlines_for_dpi()
                print(f"Scanlines auto-adjusted to intensity: {intensity:.3f}")
            else:
                print("adjust_scanlines_for_dpi method not found - using fallback")
                # Fallback: manually set a reasonable intensity
                if hasattr(self.terminal.grid_widget, 'set_scanline_intensity'):
                    self.terminal.grid_widget.set_scanline_intensity(0.25)
                elif hasattr(self.terminal.grid_widget, 'scanline_intensity'):
                    self.terminal.grid_widget.scanline_intensity = 0.25
                    self.terminal.grid_widget.scanlines_enabled = True
                    self.terminal.grid_widget.update()
                else:
                    print("Could not adjust scanlines - widget doesn't support this feature")

        except Exception as e:
            print(f"Error adjusting scanlines: {e}")
            import traceback
            traceback.print_exc()

            # Show user-friendly error message
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "Scanlines Adjustment",
                f"Could not auto-adjust scanlines:\n{str(e)}\n\nYou can still toggle scanlines on/off using Ctrl+S"
            )

    def increase_ambient_glow(self):
        """Increase ambient glow intensity"""
        if hasattr(self, 'terminal') and not self._is_closing:
            if hasattr(self.terminal.grid_widget, 'increase_ambient_glow'):
                success = self.terminal.grid_widget.increase_ambient_glow()
                if success:
                    level = self.terminal.grid_widget.get_ambient_glow_level()

            else:
                print("Ambient glow control not available")

    def decrease_ambient_glow(self):
        """Decrease ambient glow intensity"""
        if hasattr(self, 'terminal') and not self._is_closing:
            if hasattr(self.terminal.grid_widget, 'decrease_ambient_glow'):
                success = self.terminal.grid_widget.decrease_ambient_glow()
                if success:
                    level = self.terminal.grid_widget.get_ambient_glow_level()
            else:
                print("Ambient glow control not available")

    def reset_ambient_glow(self):
        """Reset ambient glow to theme default"""
        if hasattr(self, 'terminal') and not self._is_closing:
            if hasattr(self.terminal.grid_widget, 'reset_ambient_glow_to_theme_default'):
                self.terminal.grid_widget.reset_ambient_glow_to_theme_default()
                level = self.terminal.grid_widget.get_ambient_glow_level()

    def show_ambient_glow_status(self):
        """Show current ambient glow status"""
        if hasattr(self, 'terminal') and not self._is_closing:
            if hasattr(self.terminal.grid_widget, 'print_ambient_glow_status'):
                self.terminal.grid_widget.print_ambient_glow_status()

    def show_connection_dialog(self):
        """Show connection dialog and connect if successful"""
        if self._is_closing:
            return

        dialog = ConnectionDialog(self, self.connection_manager)
        dialog.connection_requested.connect(self.handle_connection_request)

        result = dialog.exec()

        if result != QDialog.DialogCode.Accepted:
            # User cancelled - show a message and exit
            QMessageBox.information(self, "No Connection", "No SSH connection established. Exiting application.")
            self.close_application()



    def handle_connection_request(self, connection_config):
        """Handle connection request from dialog - supports both SSH and local terminals"""
        if self._is_closing:
            return

        print(f"Connecting to: {connection_config}")

        connection_type = connection_config.get('connection_type', 'ssh')

        if connection_type == 'ssh':
            # SSH connection
            self.setWindowTitle(f"Connecting to {connection_config['username']}@{connection_config['hostname']}...")

            # Connect terminal to SSH
            success = self.connect_to_ssh(connection_config)

            if success:
                # Update window title with SSH connection info
                self.setWindowTitle(
                    f"SSH Terminal - {connection_config['username']}@{connection_config['hostname']}:{connection_config['port']}")
                print("SSH connection established successfully!")
            else:
                # SSH connection failed - show dialog again
                QMessageBox.critical(self, "Connection Failed", "Failed to establish SSH connection.")

        else:
            # Local terminal connection
            shell_name = connection_config.get('shell_path', 'Terminal')
            self.setWindowTitle(f"Connecting to {shell_name}...")

            # Connect terminal to local shell
            success = self.connect_to_local_terminal(connection_config)

            if success:
                # Update window title with local terminal info
                working_dir = connection_config.get('working_dir', '')
                if working_dir:
                    self.setWindowTitle(f"{shell_name} - {working_dir}")
                else:
                    self.setWindowTitle(f"Local Terminal - {shell_name}")
                print("Local terminal connection established successfully!")
            else:
                # Local connection failed - show dialog again
                QMessageBox.critical(self, "Connection Failed", "Failed to establish local terminal connection.")

    def connect_to_local_terminal(self, connection_config):
        """Connect to local terminal with given configuration"""
        if self._is_closing:
            return False

        try:
            print(f"Connecting to local terminal: {connection_config}")

            # Import and use the backend factory
            from coolpyterm.backend_factory import create_backend

            # Create appropriate backend (Windows terminal)
            backend = create_backend(connection_config, self.terminal)  # Pass terminal widget, not main window

            # Store backend in BOTH places for now
            self.ssh_backend = backend  # Main window (for cleanup)
            self.terminal.ssh_backend = backend  # Terminal widget (for keyboard handling)

            # Connect signals (same as SSH)
            backend.send_output.connect(self.terminal.update_ui)
            backend.connection_established.connect(self.on_local_terminal_connected)
            backend.connection_failed.connect(self.on_local_terminal_failed)

            print("Local terminal backend established successfully")
            print(f"Backend stored in main window: {type(self.ssh_backend)}")
            print(f"Backend stored in terminal widget: {type(self.terminal.ssh_backend)}")
            return True

        except Exception as e:
            print(f"Failed to establish local terminal backend: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(None, "Connection Failed", f"Failed to connect to local terminal:\n{str(e)}")
            self.ssh_backend = None
            self.terminal.ssh_backend = None
            return False
    def on_local_terminal_connected(self):
        """Handle successful local terminal connection"""
        print("Local terminal connected successfully!")

    def on_local_terminal_failed(self, error_msg):
        """Handle failed local terminal connection"""
        print(f"Local terminal connection failed: {error_msg}")
        QMessageBox.critical(None, "Terminal Connection Failed", f"Failed to connect to terminal:\n{error_msg}")

    def on_ssh_connected(self):
        """Handle successful SSH connection"""
        print("SSH connected successfully!")

    def on_ssh_failed(self, error_msg):
        """Handle failed SSH connection"""
        print(f"SSH connection failed: {error_msg}")
        QMessageBox.critical(None, "SSH Connection Failed", f"Failed to connect to SSH server:\n{error_msg}")

    def connect_to_ssh(self, ssh_config):
        """Connect to SSH server with given configuration"""
        if self._is_closing:
            return False

        try:
            print(f"Connecting to SSH: {ssh_config['username']}@{ssh_config['hostname']}:{ssh_config['port']}")

            # Use the backend factory for consistency
            from coolpyterm.backend_factory import create_backend

            backend = create_backend(ssh_config, self.terminal)  # Pass terminal widget

            # Store backend in BOTH places
            self.ssh_backend = backend  # Main window
            self.terminal.ssh_backend = backend  # Terminal widget

            # Connect signals
            backend.send_output.connect(self.terminal.update_ui)
            backend.connection_established.connect(self.on_ssh_connected)
            backend.connection_failed.connect(self.on_ssh_failed)

            print("SSH backend established successfully")
            return True

        except Exception as e:
            print(f"Failed to establish SSH backend: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(None, "Connection Failed", f"Failed to connect to SSH server:\n{str(e)}")
            self.ssh_backend = None
            self.terminal.ssh_backend = None
            return False

    def create_menu_system(self):
        """Complete menu system with disabled mnemonics to avoid DOS app conflicts"""
        menubar = self.menuBar()

        # CRITICAL: Disable menu mnemonics so Alt+F, Alt+E etc. go to terminal
        menubar.setNativeMenuBar(False)  # Important for consistent behavior

        # File Menu - REMOVE & from menu titles
        file_menu = menubar.addMenu('File')  # No '&' here

        # Connection manager menu item - REMOVE & from actions too
        connection_action = QAction('Connection Manager...', self)  # No '&'
        connection_action.setShortcut('Ctrl+M')
        connection_action.triggered.connect(self.show_connection_manager)
        file_menu.addAction(connection_action)

        # New connection action
        new_connection_action = QAction('New Connection...', self)  # No '&'
        new_connection_action.setShortcut('Ctrl+N')
        new_connection_action.triggered.connect(self.show_new_connection_dialog)
        file_menu.addAction(new_connection_action)

        file_menu.addSeparator()

        exit_action = QAction('Exit', self)  # No '&'
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close_application)
        file_menu.addAction(exit_action)

        # Edit Menu
        edit_menu = menubar.addMenu('Edit')  # No '&'
        paste_action = QAction('Paste', self)  # No '&'
        paste_action.setShortcut('Ctrl+V')
        paste_action.triggered.connect(self.terminal.paste_from_clipboard)
        edit_menu.addAction(paste_action)

        # View Menu
        view_menu = menubar.addMenu('View')  # No '&'
        self.fullscreen_action = QAction('Full Screen', self)  # No '&'
        self.fullscreen_action.setShortcut(QKeySequence('Ctrl+Alt+F11'))
        self.fullscreen_action.setCheckable(True)
        self.fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(self.fullscreen_action)

        # Theme Menu
        theme_menu = menubar.addMenu('Theme')  # No '&'
        self.theme_group = QActionGroup(self)

        # Get themes dynamically from theme manager
        themes = self.theme_manager.get_available_themes()

        # Define display names for better menu appearance (remove & from these too)
        theme_display_names = {
            'green': 'Green Phosphor',
            'amber': 'Amber Phosphor',
            'dos': 'DOS Terminal',
            'ibm_bw': 'IBM DOS',  # Removed B&W
            'plasma': 'Plasma Red'
        }

        current_theme = self.theme_manager.current_theme

        for i, theme_name in enumerate(themes):
            # Get nice display name or fallback to formatted theme name
            display_name = theme_display_names.get(theme_name, theme_name.replace('_', ' ').title())

            # Add keyboard shortcut for first 9 themes (Ctrl+1, Ctrl+2, etc.)
            # NO & characters in action names
            if i < 9:
                action = QAction(f'{i + 1}. {display_name}', self)  # No & here
                action.setShortcut(f'Ctrl+{i + 1}')
            else:
                action = QAction(f'{display_name}', self)

            action.setCheckable(True)
            action.setData(theme_name)  # Store the actual theme key

            # Set default theme as checked
            if theme_name == current_theme:
                action.setChecked(True)

            # Connect to theme change handler
            action.triggered.connect(lambda checked, t=theme_name: self.change_theme(t))

            self.theme_group.addAction(action)
            theme_menu.addAction(action)

        # Add separator and theme info action
        theme_menu.addSeparator()

        # Add "Show Theme Info" action for debugging (no &)
        theme_info_action = QAction('Show Theme Info...', self)
        theme_info_action.triggered.connect(self.show_theme_info)
        theme_menu.addAction(theme_info_action)

        # Effects Menu
        effects_menu = menubar.addMenu('Effects')  # No '&'

        # Phosphor glow (no &)
        self.glow_action = QAction('Phosphor Glow', self)
        self.glow_action.setCheckable(True)
        self.glow_action.setChecked(True)
        self.glow_action.setShortcut('Ctrl+G')
        self.glow_action.triggered.connect(self.toggle_glow)
        effects_menu.addAction(self.glow_action)

        # Ambient background glow (no &)
        self.ambient_glow_action = QAction('Ambient Background Glow', self)
        self.ambient_glow_action.setCheckable(True)
        self.ambient_glow_action.setChecked(True)  # Default on
        self.ambient_glow_action.setShortcut('Ctrl+Shift+A')
        self.ambient_glow_action.setToolTip("Subtle phosphor glow across entire screen background")
        self.ambient_glow_action.triggered.connect(self.toggle_ambient_glow)
        effects_menu.addAction(self.ambient_glow_action)

        increase_ambient_action = QAction('Increase Ambient Intensity', self)
        increase_ambient_action.setShortcut('Ctrl+Alt+I')
        increase_ambient_action.setToolTip("Increase ambient glow intensity")
        increase_ambient_action.triggered.connect(self.increase_ambient_glow)
        effects_menu.addAction(increase_ambient_action)

        decrease_ambient_action = QAction('Decrease Ambient Intensity', self)
        decrease_ambient_action.setShortcut('Ctrl+Alt+O')
        decrease_ambient_action.setToolTip("Decrease ambient glow intensity")
        decrease_ambient_action.triggered.connect(self.decrease_ambient_glow)
        effects_menu.addAction(decrease_ambient_action)

        # Scanlines (no &)
        self.scanlines_action = QAction('Scanlines', self)
        self.scanlines_action.setCheckable(True)
        self.scanlines_action.setChecked(True)
        self.scanlines_action.setShortcut('Ctrl+S')
        self.scanlines_action.triggered.connect(self.toggle_scanlines)
        effects_menu.addAction(self.scanlines_action)

        effects_menu.addSeparator()

        # Auto-adjust scanlines for DPI (no &)
        auto_scanlines_action = QAction('Auto-Adjust Scanlines', self)
        auto_scanlines_action.triggered.connect(self.auto_adjust_scanlines)
        effects_menu.addAction(auto_scanlines_action)
        effects_menu.addSeparator()

        # Cursor Controls submenu
        cursor_controls_menu = effects_menu.addMenu('&Cursor Controls')

        # Toggle cursor blinking
        self.cursor_blink_action = QAction('Cursor &Blinking', self)
        self.cursor_blink_action.setCheckable(True)
        self.cursor_blink_action.setChecked(True)  # Default enabled
        self.cursor_blink_action.triggered.connect(self.toggle_cursor_blinking)
        cursor_controls_menu.addAction(self.cursor_blink_action)

        cursor_controls_menu.addSeparator()

        # Blink rate options
        blink_rate_menu = cursor_controls_menu.addMenu('Blink &Rate')

        self.blink_rate_group = QActionGroup(self)
        blink_rates = [
            ('Fast (300ms)', 300),
            ('Normal (500ms)', 500),
            ('Slow (800ms)', 800),
            ('Very Slow (1200ms)', 1200)
        ]

        for rate_name, rate_ms in blink_rates:
            action = QAction(rate_name, self)
            action.setCheckable(True)
            action.setData(rate_ms)
            if rate_ms == 500:  # Default to normal
                action.setChecked(True)
            action.triggered.connect(lambda checked, ms=rate_ms: self.set_cursor_blink_rate(ms))
            self.blink_rate_group.addAction(action)
            blink_rate_menu.addAction(action)

    def show_theme_info(self):
        """Show information about current theme and available themes"""
        if self._is_closing:
            return

        from PyQt6.QtWidgets import QMessageBox

        current_theme = self.theme_manager.get_current_theme()
        available_themes = self.theme_manager.get_available_themes()

        info_text = f"Current Theme: {current_theme.name}\n"
        info_text += f"Description: {current_theme.description}\n\n"
        info_text += f"CRT Properties:\n"
        info_text += f"  • Background Glow: {current_theme.background_glow_intensity:.2f}\n"
        info_text += f"  • Brightness: {current_theme.brightness:.2f}\n"
        info_text += f"  • Contrast: {current_theme.contrast:.2f}\n"
        info_text += f"  • Phosphor Persistence: {current_theme.phosphor_persistence:.2f}\n"
        info_text += f"  • Bloom Radius: {current_theme.bloom_radius:.2f}\n\n"
        info_text += f"Available Themes ({len(available_themes)}):\n"

        for theme_name in available_themes:
            theme = self.theme_manager.get_theme(theme_name)
            info_text += f"  • {theme.name}: {theme.description}\n"

        QMessageBox.information(self, "Theme Information", info_text)


    def show_connection_manager(self):
        """Show the connection manager dialog"""
        if self._is_closing:
            return
        dialog = ConnectionDialog(self, self.connection_manager)
        dialog.connection_requested.connect(self.handle_connection_request)
        dialog.exec()

    def show_new_connection_dialog(self):
        """Show dialog for new connection"""
        self.show_connection_manager()

    def toggle_cursor_blinking(self):
        """Toggle cursor blinking on/off"""
        if hasattr(self, 'terminal') and not self._is_closing:
            enabled = self.cursor_blink_action.isChecked()
            self.terminal.grid_widget.enable_cursor_blink(enabled)

    def set_cursor_blink_rate(self, milliseconds):
        """Set cursor blink rate"""
        if hasattr(self, 'terminal') and not self._is_closing:
            self.terminal.grid_widget.set_cursor_blink_rate(milliseconds)
            print(f"Cursor blink rate changed to {milliseconds}ms")

    def toggle_background_glow(self):
        """NEW: Toggle background glow (replaces toggle_flicker)"""
        if not self._is_closing:
            self.terminal.grid_widget.toggle_background_glow()

    def toggle_ambient_glow(self):
        """NEW: Toggle ambient background glow"""
        if not self._is_closing:
            self.terminal.grid_widget.toggle_ambient_glow()

    def adjust_brightness(self, delta):
        """NEW: Adjust CRT brightness"""
        if hasattr(self, 'terminal') and not self._is_closing:
            current = self.terminal.grid_widget.brightness
            new_brightness = max(0.5, min(2.0, current + delta))
            self.terminal.grid_widget.set_crt_controls(brightness=new_brightness)

    def adjust_contrast(self, delta):
        """NEW: Adjust CRT contrast"""
        if hasattr(self, 'terminal') and not self._is_closing:
            current = self.terminal.grid_widget.contrast
            new_contrast = max(0.5, min(2.0, current + delta))
            self.terminal.grid_widget.set_crt_controls(contrast=new_contrast)

    # def auto_adjust_scanlines(self):
    #     """NEW: Auto-adjust scanlines for current display"""
    #     if hasattr(self, 'terminal') and not self._is_closing:
    #         self.terminal.grid_widget.adjust_scanlines_for_dpi()

    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode"""
        if self._is_closing:
            return
        if self.is_fullscreen:
            self.exit_fullscreen()
        else:
            self.enter_fullscreen()

    def enter_fullscreen(self):
        """Enter fullscreen mode"""
        if not self.is_fullscreen and not self._is_closing:
            # Save current window state
            self.windowed_geometry = self.geometry()
            self.windowed_state = self.windowState()

            # Create a new layout without menu bar for fullscreen
            self.create_fullscreen_layout()

            # Set window flags for true fullscreen
            self.setWindowFlags(
                Qt.WindowType.Window |
                Qt.WindowType.FramelessWindowHint |
                Qt.WindowType.WindowStaysOnTopHint
            )

            # Enter fullscreen
            self.showFullScreen()

            # Force exact screen geometry
            screen = QApplication.primaryScreen()
            if screen:
                screen_rect = screen.geometry()
                self.setGeometry(screen_rect)
                print(f"Setting fullscreen geometry to: {screen_rect}")

            self.is_fullscreen = True
            self.fullscreen_action.setChecked(True)

            print("Entered fullscreen mode (Ctrl Alt F11 to exit)")

    def exit_fullscreen(self):
        """Exit fullscreen mode"""
        if self.is_fullscreen and not self._is_closing:
            # Restore normal layout with menu bar
            self.restore_windowed_layout()

            # Restore window flags
            self.setWindowFlags(Qt.WindowType.Window)

            # Exit fullscreen
            self.showNormal()

            # Restore previous geometry
            if self.windowed_geometry:
                self.setGeometry(self.windowed_geometry)

            # Restore window state
            if self.windowed_state:
                self.setWindowState(self.windowed_state)

            # Ensure window is shown properly after flag changes
            self.show()

            self.is_fullscreen = False
            self.fullscreen_action.setChecked(False)

            print("Exited fullscreen mode")

    def create_fullscreen_layout(self):
        """Create layout for fullscreen mode without menu bar"""
        if self._is_closing:
            return

        # Hide the menu bar completely
        self.menuBar().hide()

        # Remove any margins from the central widget
        if self.terminal:
            # Create a new widget that will fill the entire window
            fullscreen_container = QWidget()
            fullscreen_layout = QVBoxLayout(fullscreen_container)
            fullscreen_layout.setContentsMargins(0, 0, 0, 0)
            fullscreen_layout.setSpacing(0)

            # Move terminal to fullscreen container
            self.terminal.setParent(fullscreen_container)
            fullscreen_layout.addWidget(self.terminal)

            # Set as central widget
            self.setCentralWidget(fullscreen_container)

    def restore_windowed_layout(self):
        """Restore normal windowed layout with menu bar"""
        if self._is_closing:
            return

        # Show the menu bar
        self.menuBar().show()

        # Restore terminal as direct central widget
        if self.terminal:
            self.terminal.setParent(self)
            self.setCentralWidget(self.terminal)

    def keyPressEvent(self, event):
        """Handle global key events for fullscreen"""
        if self._is_closing:
            return

        # Handle ambient glow shortcuts
        if (event.key() == Qt.Key.Key_A and
                event.modifiers() & Qt.KeyboardModifier.ControlModifier and
                event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
            self.toggle_ambient_glow()
            return

        elif (event.key() == Qt.Key.Key_I and
              event.modifiers() & Qt.KeyboardModifier.ControlModifier and
              event.modifiers() & Qt.KeyboardModifier.AltModifier):
            self.increase_ambient_glow()
            return

        elif (event.key() == Qt.Key.Key_O and
              event.modifiers() & Qt.KeyboardModifier.ControlModifier and
              event.modifiers() & Qt.KeyboardModifier.AltModifier):
            self.decrease_ambient_glow()
            return

        # Handle Escape key to exit fullscreen
        elif event.key() == Qt.Key.Key_Escape and self.is_fullscreen:
            self.exit_fullscreen()
            return

        # Handle F11 for fullscreen toggle
        elif (event.key() == Qt.Key.Key_F11 and
              event.modifiers() & Qt.KeyboardModifier.ControlModifier and
              event.modifiers() & Qt.KeyboardModifier.AltModifier):
            self.toggle_fullscreen()
            return

        # Pass other events to the terminal
        if hasattr(self, 'terminal'):
            self.terminal.keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def eventFilter(self, obj, event):
        """Event filter for global shortcuts"""
        if self._is_closing:
            return False

        # This ensures shortcuts work even when terminal has focus
        if event.type() == event.Type.KeyPress:
            if (event.key() == Qt.Key.Key_F11 and
                    event.modifiers() & Qt.KeyboardModifier.ControlModifier and
                    event.modifiers() & Qt.KeyboardModifier.AltModifier):
                self.toggle_fullscreen()
                return True
            elif event.key() == Qt.Key.Key_Escape and self.is_fullscreen:
                self.exit_fullscreen()
                return True

        return super().eventFilter(obj, event)

    def change_theme(self, theme_name):
        """CRITICAL FIX: Don't recreate terminal on theme change"""
        if self._is_closing:
            return

        print(f"Window {self.window_id} changing theme to: {theme_name}")

        # Update theme manager
        self.theme_manager.set_current_theme(theme_name)

        # CRITICAL: Just update existing terminal, don't recreate!
        if hasattr(self, 'terminal') and self.terminal:
            self.terminal.set_theme(theme_name)
        else:
            print(f"ERROR: Window {self.window_id} has no terminal!")

    def toggle_glow(self):
        """Toggle glow effect"""
        if hasattr(self, 'terminal') and not self._is_closing:
            self.terminal.toggle_glow()

    def toggle_scanlines(self):
        """Toggle scanlines effect"""
        if hasattr(self, 'terminal') and not self._is_closing:
            self.terminal.toggle_scanlines()

    def close_application(self):
        """Clean application shutdown"""
        if self._is_closing:
            return

        print("Starting clean application shutdown...")
        self._is_closing = True

        try:
            # Close terminal first
            if hasattr(self, 'terminal') and self.terminal:
                self.terminal.close()

            # Give time for cleanup
            QApplication.processEvents()

            # Quit application
            QApplication.quit()

        except Exception as e:
            print(f"Error during application shutdown: {e}")
            # Force exit if normal shutdown fails
            sys.exit(0)

    def closeEvent(self, event):
        """Handle window close event"""
        print("Close event received")

        # Start clean shutdown
        self.close_application()

        # Accept the event
        event.accept()

    def showEvent(self, event):
        """Handle window show event"""
        if self._is_closing:
            return

        super().showEvent(event)
        # Ensure terminal gets focus when window is shown
        if hasattr(self, 'terminal'):
            self.terminal.setFocus()

    def resizeEvent(self, event):
        """CRITICAL FIX: Don't trigger widget recreation on resize"""
        if self._is_closing:
            return

        print(f"Window {self.window_id} resize event: {event.size()}")

        # Call parent resize first
        super().resizeEvent(event)

        # Only do fullscreen-specific positioning
        if self.is_fullscreen and hasattr(self, 'terminal'):
            # Just ensure positioning, don't force resize
            self.terminal.move(0, 0)

    def __del__(self):
        """Track window destruction"""
        print(f"Terminal window {self.window_id} destroyed")


def cleanup_threads():
    """Force cleanup of any remaining threads"""
    try:
        import gc
        # Find QThread objects using garbage collector
        thread_objects = [obj for obj in gc.get_objects() if isinstance(obj, QThread)]

        if thread_objects:
            print(f"Found {len(thread_objects)} thread objects to cleanup...")

            for thread in thread_objects:
                try:
                    if thread.isRunning():
                        print(f"Waiting for thread {thread} to finish...")
                        thread.quit()
                        if not thread.wait(2000):  # Wait up to 2 seconds
                            print(f"Force terminating thread {thread}")
                            thread.terminate()
                            thread.wait(1000)  # Wait for termination
                except Exception as e:
                    print(f"Error cleaning up individual thread: {e}")
        else:
            print("No active threads found to cleanup")

    except Exception as e:
        print(f"Error cleaning up threads: {e}")


def debug_widget_count():
    """Debug function to check for widget leaks"""
    import gc
    terminals = [obj for obj in gc.get_objects() if isinstance(obj, TerminalWithHardwareGrid)]
    opengl_widgets = [obj for obj in gc.get_objects() if isinstance(obj, OpenGLRetroGridWidget)]

    print(f"Active terminals: {len(terminals)}")
    print(f"Active OpenGL widgets: {len(opengl_widgets)}")

    for i, terminal in enumerate(terminals):
        print(f"  Terminal {i}: {id(terminal)}")

    for i, widget in enumerate(opengl_widgets):
        print(f"  OpenGL widget {i}: {id(widget)}")

    return len(terminals), len(opengl_widgets)


def main():
    """STEP 3: Connection Manager starts first with clean shutdown"""
    # Enable clean shutdown on Ctrl+C
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    app.setApplicationName("Hardware-Accelerated Terminal")
    app.setApplicationVersion("1.0")

    # Ensure clean exit
    app.setQuitOnLastWindowClosed(True)

    try:
        window = HardwareTerminalWindow()
        window.show()

        print("STEP 3: Connection Manager starts first with CLEAN SHUTDOWN!")
        print("✅ Connection dialog appears immediately on startup")
        print("✅ Enhanced connection dialog with password field")
        print("✅ Profile management with save/load/delete")
        print("✅ Recent connections marked with ⭐")
        print("✅ Double-click profiles to connect instantly")
        print("✅ No hardcoded credentials - must use dialog")
        print("✅ CLEAN SHUTDOWN: Proper resource cleanup on exit")
        print()
        print("Features:")
        print("  ✅ Enhanced connection dialog with password field")
        print("  ✅ SSH key file support with browse button")
        print("  ✅ Profile management (save, update, delete)")
        print("  ✅ Recent connections tracking")
        print("  ✅ Connection validation")
        print("  ✅ Clean shutdown with signal handling")
        print()
        print("Controls:")
        print("  Ctrl+M - Show connection manager")
        print("  Ctrl+N - New connection")
        print("  Ctrl+Q - Quit (clean shutdown)")
        print("  F11 - Toggle fullscreen")
        print("  Ctrl+G - Toggle phosphor glow")
        print("  Ctrl+B - Toggle background glow")
        print("  Ctrl+S - Toggle scanlines")

        # Run the application
        exit_code = app.exec()

        print("Application finished, cleaning up...")

        # Force cleanup of any remaining threads
        cleanup_threads()

        # Force garbage collection
        import gc
        gc.collect()

        print("Clean shutdown completed!")
        return exit_code

    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt, shutting down...")
        if 'window' in locals():
            window.close_application()
        return 0
    except Exception as e:
        print(f"Unhandled exception: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())