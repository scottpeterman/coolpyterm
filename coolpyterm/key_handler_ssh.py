# key_handler_ssh.py - PyQt6 version with fixed fullscreen handling

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent


class KeyHandler:
    @staticmethod
    def send(string, ssh_connection):
        """Send a string to SSH connection, handling newlines properly."""
        if "\n" in string:
            lines = string.splitlines()
            for line in lines:
                ssh_connection.send_command(line.encode('utf-8'))
                ssh_connection.send_command(b"\n")
        else:
            ssh_connection.send_command(string.encode('utf-8'))

    @staticmethod
    def is_fullscreen_toggle(event: QKeyEvent):
        """Check if event is the fullscreen toggle combination (Ctrl+Alt+F11)"""
        return (event.key() == Qt.Key.Key_F11 and
                event.modifiers() & Qt.KeyboardModifier.ControlModifier and
                event.modifiers() & Qt.KeyboardModifier.AltModifier)

    @staticmethod
    def should_handle_locally(event: QKeyEvent):
        """Check if this key event should be handled locally instead of sent to SSH"""
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

        return False

    @staticmethod
    def handle_key_event(event: QKeyEvent, ssh_connection):
        """
        Handle PyQt6 key press event and send appropriate command to SSH.
        Returns True if event was handled, False if it should be passed up.
        """
        # First check if this should be handled locally
        if KeyHandler.should_handle_locally(event):
            return False  # Let the application handle it

        key = event.key()
        modifiers = event.modifiers()
        text = event.text()

        # Mapping of Qt keys to escape sequences
        special_keys = {
            Qt.Key.Key_Return: b"\r",
            Qt.Key.Key_Enter: b"\r",
            Qt.Key.Key_Backspace: b"\b",
            Qt.Key.Key_Escape: b"\x1b",
            Qt.Key.Key_Up: b"\x1b[A",
            Qt.Key.Key_Down: b"\x1b[B",
            Qt.Key.Key_Right: b"\x1b[C",
            Qt.Key.Key_Left: b"\x1b[D",
            Qt.Key.Key_F1: b"\x1bOP",
            Qt.Key.Key_F2: b"\x1bOQ",
            Qt.Key.Key_F3: b"\x1bOR",
            Qt.Key.Key_F4: b"\x1bOS",
            Qt.Key.Key_F5: b"\x1b[15~",
            Qt.Key.Key_F6: b"\x1b[17~",
            Qt.Key.Key_F7: b"\x1b[18~",
            Qt.Key.Key_F8: b"\x1b[19~",
            Qt.Key.Key_F9: b"\x1b[20~",
            Qt.Key.Key_F10: b"\x1b[21~",
            Qt.Key.Key_F11: b"\x1b[23~",
            Qt.Key.Key_F12: b"\x1b[24~",
            Qt.Key.Key_Insert: b"\x1b[2~",
            Qt.Key.Key_Delete: b"\x1b[3~",
            Qt.Key.Key_Home: b"\x1b[H",
            Qt.Key.Key_End: b"\x1b[F",
            Qt.Key.Key_PageUp: b"\x1b[5~",
            Qt.Key.Key_PageDown: b"\x1b[6~",
            Qt.Key.Key_Tab: b"\t",
        }

        # Handle Ctrl combinations (but not Ctrl+Alt)
        if (modifiers & Qt.KeyboardModifier.ControlModifier and
                not (modifiers & Qt.KeyboardModifier.AltModifier)):

            if key == Qt.Key.Key_C:
                ssh_connection.send_command(b"\x03")  # Ctrl+C (SIGINT)
                return True
            elif key == Qt.Key.Key_D:
                ssh_connection.send_command(b"\x04")  # Ctrl+D (EOF)
                return True
            elif key == Qt.Key.Key_Z:
                ssh_connection.send_command(b"\x1a")  # Ctrl+Z (SIGTSTP)
                return True
            elif key == Qt.Key.Key_L:
                ssh_connection.send_command(b"\x0c")  # Ctrl+L (clear screen)
                return True
            elif key == Qt.Key.Key_A:
                ssh_connection.send_command(b"\x01")  # Ctrl+A (beginning of line)
                return True
            elif key == Qt.Key.Key_E:
                ssh_connection.send_command(b"\x05")  # Ctrl+E (end of line)
                return True
            elif key == Qt.Key.Key_K:
                ssh_connection.send_command(b"\x0b")  # Ctrl+K (kill to end of line)
                return True
            elif key == Qt.Key.Key_U:
                ssh_connection.send_command(b"\x15")  # Ctrl+U (kill to beginning of line)
                return True
            elif key == Qt.Key.Key_W:
                ssh_connection.send_command(b"\x17")  # Ctrl+W (kill word)
                return True
            elif key == Qt.Key.Key_R:
                ssh_connection.send_command(b"\x12")  # Ctrl+R (reverse search)
                return True
            # Handle other Ctrl+A-Z combinations
            elif Qt.Key.Key_A <= key <= Qt.Key.Key_Z:
                ctrl_char = key - Qt.Key.Key_A + 1
                ssh_connection.send_command(bytes([ctrl_char]))
                return True

        # Handle Alt combinations (but not Ctrl+Alt)
        if (modifiers & Qt.KeyboardModifier.AltModifier and
                not (modifiers & Qt.KeyboardModifier.ControlModifier)):

            if text:
                ssh_connection.send_command(b"\x1b" + text.encode('utf-8'))
                return True

        # Check if it's a special key
        if key in special_keys:
            ssh_connection.send_command(special_keys[key])
            return True

        # Handle regular text input
        if text and not (modifiers & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier)):
            ssh_connection.send_command(text.encode('utf-8'))
            return True

        return False

    @staticmethod
    def handle_paste(text, ssh_connection):
        """Handle pasted text, converting to appropriate format."""
        if text:
            # Convert line endings and send
            text = text.replace('\r\n', '\n').replace('\r', '\n')
            KeyHandler.send(text, ssh_connection)