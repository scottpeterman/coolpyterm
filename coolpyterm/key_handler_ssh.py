
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent


class KeyHandler:
    @staticmethod
    def send(string, backend_connection):
        """Send a string to backend connection, handling newlines and backend types properly."""
        if "\n" in string:
            lines = string.splitlines()
            for line in lines:
                KeyHandler._send_to_backend(line, backend_connection)
                KeyHandler._send_to_backend("\n", backend_connection)
        else:
            KeyHandler._send_to_backend(string, backend_connection)

    @staticmethod
    def _send_to_backend(data, backend_connection):
        """Send data to appropriate backend type (SSH bytes vs Windows strings)."""
        # Detect backend type by checking for Windows-specific attributes
        if hasattr(backend_connection, 'pty_process'):
            # Windows backend - expects strings
            if hasattr(backend_connection, 'send_command'):
                backend_connection.send_command(data)
            elif hasattr(backend_connection, 'write_data'):
                backend_connection.write_data(data)
        else:
            # SSH backend - expects bytes
            if hasattr(backend_connection, 'send_command'):
                if isinstance(data, str):
                    backend_connection.send_command(data.encode('utf-8'))
                else:
                    backend_connection.send_command(data)

    @staticmethod
    def is_fullscreen_toggle(event: QKeyEvent):
        """Check if event is the fullscreen toggle combination (Ctrl+Alt+F11)"""
        return (event.key() == Qt.Key.Key_F11 and
                event.modifiers() & Qt.KeyboardModifier.ControlModifier and
                event.modifiers() & Qt.KeyboardModifier.AltModifier)

    @staticmethod
    def is_theme_shortcut(event: QKeyEvent):
        """Check if event is a theme shortcut (Ctrl+1-9)"""
        if (event.modifiers() & Qt.KeyboardModifier.ControlModifier and
                not (event.modifiers() & Qt.KeyboardModifier.AltModifier) and
                not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier)):
            # Check for Ctrl+1 through Ctrl+9 (theme shortcuts)
            if Qt.Key.Key_1 <= event.key() <= Qt.Key.Key_9:
                return True
        return False

    @staticmethod
    def should_handle_locally(event: QKeyEvent):
        """Check if this key event should be handled locally instead of sent to backend"""
        # Theme shortcuts (Ctrl+1-9) - CRITICAL FIX
        if KeyHandler.is_theme_shortcut(event):
            return True

        # Fullscreen toggle
        if KeyHandler.is_fullscreen_toggle(event):
            return True

        # Application shortcuts with Ctrl+Alt
        if (event.modifiers() & Qt.KeyboardModifier.ControlModifier and
                event.modifiers() & Qt.KeyboardModifier.AltModifier):

            # Specific application shortcuts
            if event.key() in [Qt.Key.Key_F11, Qt.Key.Key_I, Qt.Key.Key_O]:
                return True

            # Let other Ctrl+Alt combinations be handled locally too
            return True

        # Application shortcuts with Ctrl+Shift (ambient glow toggle)
        if (event.modifiers() & Qt.KeyboardModifier.ControlModifier and
                event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
            if event.key() == Qt.Key.Key_A:
                return True

        # Effect toggles (Ctrl only, no other modifiers)
        if (event.modifiers() & Qt.KeyboardModifier.ControlModifier and
                not (event.modifiers() & Qt.KeyboardModifier.AltModifier) and
                not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier)):

            # Application effect shortcuts
            if event.key() in [
                Qt.Key.Key_G,  # Toggle glow
                Qt.Key.Key_S,  # Toggle scanlines
                Qt.Key.Key_M,  # Connection manager
                Qt.Key.Key_N,  # New connection
                Qt.Key.Key_Q,  # Quit application
                Qt.Key.Key_V  # Paste (let app handle)
            ]:
                return True

        return False

    @staticmethod
    def handle_key_event(event: QKeyEvent, backend_connection):
        """
        Handle PyQt6 key press event and send appropriate command to backend.
        Returns True if event was handled, False if it should be passed up.
        """
        # First check if this should be handled locally
        if KeyHandler.should_handle_locally(event):
            print(f"🔑 KeyHandler: Passing key {event.key()} to application (local handling)")
            return False  # Let the application handle it

        key = event.key()
        modifiers = event.modifiers()
        text = event.text()

        # In your key_handler_ssh.py, implement backspace as left arrow + delete:

        # SPECIAL HANDLING FOR BACKSPACE - LEFT ARROW + DELETE METHOD
        if key == Qt.Key.Key_Backspace:
            print("🔙 Backspace pressed - using left arrow + delete method")

            if hasattr(backend_connection, 'pty_process'):
                # Windows backend - simulate left arrow + delete
                print("🔙 Windows backend - sending: left arrow (\\x1b[D) + delete (\\x1b[3~)")

                # Method 1: Two separate sends
                KeyHandler._send_to_backend("\x1b[D", backend_connection)  # Left arrow
                KeyHandler._send_to_backend("\x1b[3~", backend_connection)  # Delete key

                # Alternative: Single send (uncomment to try this instead)
                # KeyHandler._send_to_backend("\x1b[D\x1b[3~", backend_connection)

            else:
                # SSH backend - use standard backspace
                print("🔙 SSH backend - using standard backspace")
                KeyHandler._send_to_backend("\x08", backend_connection)
            return True
        print(f"🔑 KeyHandler: Sending key {event.key()} to backend")

        # Mapping of Qt keys to escape sequences (as strings for compatibility)
        special_keys = {
            Qt.Key.Key_Return: "\r",
            Qt.Key.Key_Enter: "\r",
            # Qt.Key.Key_Backspace: "\b",
            Qt.Key.Key_Escape: "\x1b",
            Qt.Key.Key_Up: "\x1b[A",
            Qt.Key.Key_Down: "\x1b[B",
            Qt.Key.Key_Right: "\x1b[C",
            Qt.Key.Key_Left: "\x1b[D",
            Qt.Key.Key_F1: "\x1bOP",
            Qt.Key.Key_F2: "\x1bOQ",
            Qt.Key.Key_F3: "\x1bOR",
            Qt.Key.Key_F4: "\x1bOS",
            Qt.Key.Key_F5: "\x1b[15~",
            Qt.Key.Key_F6: "\x1b[17~",
            Qt.Key.Key_F7: "\x1b[18~",
            Qt.Key.Key_F8: "\x1b[19~",
            Qt.Key.Key_F9: "\x1b[20~",
            Qt.Key.Key_F10: "\x1b[21~",
            Qt.Key.Key_F11: "\x1b[23~",
            Qt.Key.Key_F12: "\x1b[24~",
            Qt.Key.Key_Insert: "\x1b[2~",
            Qt.Key.Key_Delete: "\x1b[3~",
            Qt.Key.Key_Home: "\x1b[H",
            Qt.Key.Key_End: "\x1b[F",
            Qt.Key.Key_PageUp: "\x1b[5~",
            Qt.Key.Key_PageDown: "\x1b[6~",
            Qt.Key.Key_Tab: "\t",
        }

        # Handle Ctrl combinations (but not Ctrl+Alt, and exclude theme shortcuts)
        if (modifiers & Qt.KeyboardModifier.ControlModifier and
                not (modifiers & Qt.KeyboardModifier.AltModifier) and
                not KeyHandler.is_theme_shortcut(event)):  # Exclude theme shortcuts

            if key == Qt.Key.Key_C:
                KeyHandler._send_to_backend("\x03", backend_connection)  # Ctrl+C (SIGINT)
                return True
            elif key == Qt.Key.Key_D:
                KeyHandler._send_to_backend("\x04", backend_connection)  # Ctrl+D (EOF)
                return True
            elif key == Qt.Key.Key_Z:
                KeyHandler._send_to_backend("\x1a", backend_connection)  # Ctrl+Z (SIGTSTP)
                return True
            elif key == Qt.Key.Key_L:
                KeyHandler._send_to_backend("\x0c", backend_connection)  # Ctrl+L (clear screen)
                return True
            elif key == Qt.Key.Key_A:
                KeyHandler._send_to_backend("\x01", backend_connection)  # Ctrl+A (beginning of line)
                return True
            elif key == Qt.Key.Key_E:
                KeyHandler._send_to_backend("\x05", backend_connection)  # Ctrl+E (end of line)
                return True
            elif key == Qt.Key.Key_K:
                KeyHandler._send_to_backend("\x0b", backend_connection)  # Ctrl+K (kill to end of line)
                return True
            elif key == Qt.Key.Key_U:
                KeyHandler._send_to_backend("\x15", backend_connection)  # Ctrl+U (kill to beginning of line)
                return True
            elif key == Qt.Key.Key_W:
                KeyHandler._send_to_backend("\x17", backend_connection)  # Ctrl+W (kill word)
                return True
            elif key == Qt.Key.Key_R:
                KeyHandler._send_to_backend("\x12", backend_connection)  # Ctrl+R (reverse search)
                return True
            # Handle other Ctrl+A-Z combinations (excluding reserved shortcuts)
            elif Qt.Key.Key_A <= key <= Qt.Key.Key_Z:
                # Skip keys that are handled by the application
                if key not in [Qt.Key.Key_G, Qt.Key.Key_S, Qt.Key.Key_M, Qt.Key.Key_N, Qt.Key.Key_Q, Qt.Key.Key_V]:
                    ctrl_char = chr(key - Qt.Key.Key_A + 1)
                    KeyHandler._send_to_backend(ctrl_char, backend_connection)
                    return True

        # Handle Alt combinations (but not Ctrl+Alt)
        if (modifiers & Qt.KeyboardModifier.AltModifier and
                not (modifiers & Qt.KeyboardModifier.ControlModifier)):

            if text:
                KeyHandler._send_to_backend("\x1b" + text, backend_connection)
                return True

        # Check if it's a special key
        if key in special_keys:
            KeyHandler._send_to_backend(special_keys[key], backend_connection)
            return True

        # Handle regular text input
        if text and not (modifiers & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier)):
            KeyHandler._send_to_backend(text, backend_connection)
            return True

        return False

    @staticmethod
    def handle_paste(text, backend_connection):
        """Handle pasted text, converting to appropriate format."""
        if text:
            # Convert line endings and send
            text = text.replace('\r\n', '\n').replace('\r', '\n')
            KeyHandler.send(text, backend_connection)