from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer
from coolpyterm.sshshellreader import ShellReaderThread


class SSHBackend(QObject):
    """
    SSH Backend with immediate connection like your working version
    """
    send_output = pyqtSignal(str)
    connection_failed = pyqtSignal(str)
    connection_established = pyqtSignal()

    def __init__(self, host, username, password=None, port=22, key_path=None, parent_widget=None, parent=None):
        super().__init__(parent)
        self.parent_widget = parent_widget
        self.client = None
        self.channel = None
        self.reader_thread = None
        self.auth_method_used = None
        self.is_connected = False

        # Store connection parameters
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.key_path = key_path

        # Apply transport settings
        self._apply_transport_settings()

        # CRITICAL FIX: Connect immediately like your working version
        # Don't use QTimer - connect synchronously so signals can be connected before data flows
        try:
            self._attempt_connection()
        except Exception as e:
            error_msg = f"SSH Connection Error: {str(e)}"
            print(error_msg)
            # Emit error signal after a short delay to ensure UI is ready
            QTimer.singleShot(10, lambda: self.connection_failed.emit(error_msg))

    def _attempt_connection(self):
        """Attempt SSH connection immediately"""
        print("Starting immediate SSH connection...")

        import paramiko

        self.client = paramiko.SSHClient()
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        host = str(self.host).strip()
        username = str(self.username).strip()
        port = int(self.port)

        print(f"Attempting SSH connection to {username}@{host}:{port}")

        # Authentication
        if self.key_path:
            self._try_key_auth(host, port, username, self.key_path)
        else:
            password = str(self.password).strip() if self.password else ""
            print(f"Using password auth, password length: {len(password)}")
            self._try_password_auth(host, port, username, password)

        # Get transport and set keepalive
        transport = self.client.get_transport()
        if transport:
            transport.set_keepalive(60)
            print("Transport keepalive set")

        # Setup shell but DON'T start reader thread yet
        self._setup_shell_without_reader()

        self.is_connected = True
        print("SSH connection established, shell ready")

        # Emit connection established signal to allow UI to connect
        # Use a small delay to ensure the signal is processed
        QTimer.singleShot(50, self._signal_connection_ready)

    def _setup_shell_without_reader(self):
        """Setup shell but don't start reader thread yet"""
        try:
            self.channel = self.client.invoke_shell("xterm")
            self.channel.set_combine_stderr(True)
            print("Invoked Shell!")
        except Exception as e:
            print(f"Shell not supported, falling back to pty...")
            transport = self.client.get_transport()
            if transport:
                self.channel = transport.open_session()
                self.channel.get_pty()
                self.channel.set_combine_stderr(True)
            else:
                raise Exception("No transport available for shell")

        print("Shell setup complete, waiting for signal connection...")

    def _signal_connection_ready(self):
        """Called after UI has had time to connect signals"""
        print("Emitting connection_established signal...")
        self.connection_established.emit()

        # Start reader thread after a small delay to ensure signals are connected
        QTimer.singleShot(100, self._start_reader_thread)

    def _start_reader_thread(self):
        """Start the reader thread after signals are connected"""
        if self.channel is not None:
            print("=== STARTING SHELL READER THREAD ===")
            print("Signals should be connected by now...")

            self.reader_thread = ShellReaderThread(self.channel, "", self.parent_widget)

            print(f"Connecting ShellReaderThread.data_ready to SSHBackend.send_output...")
            self.reader_thread.data_ready.connect(self._on_data_received)

            print("Starting ShellReaderThread...")
            self.reader_thread.start()
            print("✅ ShellReaderThread started successfully")

            # Send initial newline to get prompt
            QTimer.singleShot(500, lambda: self.write_data("\n"))
        else:
            print("❌ No channel available for ShellReaderThread")

    def _on_data_received(self, data):
        """Handle data from ShellReaderThread and forward to UI"""
        print(f"🔥 SSH Backend received data: {len(data)} chars")
        print(f"First 50 chars: {repr(data[:50])}")

        # Forward to UI
        self.send_output.emit(data)
        print(f"✅ Data forwarded to UI via send_output signal")

    def _apply_transport_settings(self):
        """Apply custom transport settings for better compatibility"""
        import paramiko

        cipher_settings = (
            "aes128-cbc", "aes128-ctr", "aes192-ctr", "aes256-ctr",
            "aes256-cbc", "3des-cbc", "aes192-cbc", "aes256-gcm@openssh.com",
            "aes128-gcm@openssh.com", "chacha20-poly1305@openssh.com"
        )

        kex_settings = (
            "diffie-hellman-group14-sha1", "diffie-hellman-group-exchange-sha1",
            "diffie-hellman-group-exchange-sha256", "diffie-hellman-group1-sha1",
            "ecdh-sha2-nistp256", "ecdh-sha2-nistp384", "ecdh-sha2-nistp521",
            "curve25519-sha256", "curve25519-sha256@libssh.org",
            "diffie-hellman-group16-sha512", "diffie-hellman-group18-sha512"
        )

        key_settings = (
            "ssh-rsa", "ssh-dss", "ecdsa-sha2-nistp256", "ecdsa-sha2-nistp384",
            "ecdsa-sha2-nistp521", "ssh-ed25519", "rsa-sha2-256", "rsa-sha2-512"
        )

        paramiko.Transport._preferred_ciphers = cipher_settings
        paramiko.Transport._preferred_kex = kex_settings
        paramiko.Transport._preferred_keys = key_settings
        print("Applied custom transport settings for compatibility")

    def _try_key_auth(self, host, port, username, key_path):
        """Try authentication with RSA key"""
        import paramiko
        print(f"Trying key authentication with {key_path}")
        try:
            private_key = paramiko.RSAKey(filename=key_path.strip())
            self.client.connect(hostname=host, port=port, username=username, pkey=private_key)
            self.auth_method_used = "publickey"
        except Exception as e:
            print(f"Key auth failed: {e}")
            raise

    def _try_password_auth(self, host, port, username, password):
        """Try password authentication"""
        try:
            self.client.connect(
                hostname=host,
                port=port,
                username=username,
                password=password,
                look_for_keys=False,
                allow_agent=False
            )
            self.auth_method_used = "password"
            print("Password authentication successful")
        except Exception as e:
            print(f"Password auth error: {e}")
            raise

    @pyqtSlot(str)
    def write_data(self, data):
        """Write data to SSH channel"""
        if not self.is_connected:
            print("Error: Not connected to SSH server")
            return

        if self.channel and self.channel.send_ready():
            try:
                self.channel.send(data)
                print(f"✅ Sent data: {repr(data[:50])}")
            except Exception as e:
                print(f"Error while writing to channel: {e}")
                self.is_connected = False
        else:
            print("Error: Channel is not ready or doesn't exist")

    def send_command(self, data):
        """Compatibility method for KeyHandler"""
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        self.write_data(data)

    @pyqtSlot(str)
    def set_pty_size(self, data):
        """Set PTY size following your pattern"""
        if not self.is_connected:
            return

        if self.channel and self.channel.send_ready():
            try:
                cols = data.split("::")[0]
                cols = int(cols.split(":")[1])
                rows = data.split("::")[1]
                rows = int(rows.split(":")[1])
                self.channel.resize_pty(width=cols, height=rows)
                print(f"backend pty resize -> cols:{cols} rows:{rows}")
            except Exception as e:
                print(f"Error setting backend pty term size: {e}")

    def close(self):
        """Clean up resources"""
        self.is_connected = False

        print("Closing SSH backend...")

        try:
            if self.reader_thread and self.reader_thread.isRunning():
                print("Stopping reader thread...")
                self.reader_thread.terminate()
                self.reader_thread.wait(2000)
                print("Reader thread stopped")
        except Exception as e:
            print(f"Error stopping reader thread: {e}")

        try:
            if self.channel:
                print("Closing channel...")
                self.channel.close()
                print("Channel closed")
        except Exception as e:
            print(f"Error closing channel: {e}")

        try:
            if self.client:
                print("Closing client...")
                self.client.close()
                print("Client closed")
        except Exception as e:
            print(f"Error closing client: {e}")