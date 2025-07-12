"""
Enhanced Connection Manager - Improved UI flow and WSL detection
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QSpinBox, QCheckBox, QPushButton, QComboBox, QLabel, QGroupBox,
    QListWidget, QListWidgetItem, QTabWidget, QWidget, QTextEdit,
    QDialogButtonBox, QMessageBox, QFileDialog, QSplitter, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import platform


@dataclass
class ConnectionProfile:
    """Connection profile supporting both SSH and local terminals (backward compatible)"""
    name: str
    connection_type: str = "ssh"  # "ssh", "local"

    # SSH connection fields (existing)
    hostname: str = ""
    port: int = 22
    username: str = ""
    password: str = ""
    key_path: str = ""

    # Local terminal fields (new)
    shell_path: str = ""          # "cmd.exe", "powershell.exe", "wsl.exe"
    working_dir: str = ""         # Starting directory
    startup_command: str = ""     # Command to run on startup
    env_vars: dict = None         # Environment variables

    # Common fields
    description: str = ""
    last_used: str = ""
    use_count: int = 0

    def __post_init__(self):
        if self.env_vars is None:
            self.env_vars = {}

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'ConnectionProfile':
        """Create from dictionary with backward compatibility"""
        # Handle backward compatibility with old ConnectionProfile
        if 'connection_type' not in data:
            data['connection_type'] = 'ssh'

        # Map old specific shell types to generic 'local'
        if data['connection_type'] in ['cmd', 'powershell', 'wsl']:
            data['connection_type'] = 'local'

        if 'shell_path' not in data:
            data['shell_path'] = ''
        if 'working_dir' not in data:
            data['working_dir'] = ''
        if 'startup_command' not in data:
            data['startup_command'] = ''
        if 'env_vars' not in data:
            data['env_vars'] = {}

        return cls(**data)

    def get_display_name(self) -> str:
        """Get display name for UI"""
        if self.connection_type == 'ssh':
            if self.name:
                return f"{self.name} ({self.username}@{self.hostname}:{self.port})"
            return f"{self.username}@{self.hostname}:{self.port}"
        else:
            # Local terminal
            shell_name = self.shell_path.replace('.exe', '').title()
            if self.name:
                return f"{self.name} ({shell_name})"
            return f"{shell_name} Terminal"

    def get_connection_config(self) -> Dict:
        """Get connection configuration for backend creation"""
        if self.connection_type == 'ssh':
            return {
                'connection_type': 'ssh',
                'hostname': self.hostname,
                'username': self.username,
                'password': self.password,
                'port': self.port,
                'key_path': self.key_path if self.key_path else None
            }
        else:
            # Map shell paths to specific backend types for the factory
            shell_type_map = {
                'cmd.exe': 'cmd',
                'cmd': 'cmd',
                'powershell.exe': 'powershell',
                'powershell': 'powershell',
                'pwsh.exe': 'powershell',
                'pwsh': 'powershell',
                'wsl.exe': 'wsl',
                'wsl': 'wsl'
            }

            backend_type = shell_type_map.get(self.shell_path.lower(), 'cmd')

            return {
                'connection_type': backend_type,
                'shell_path': self.shell_path,
                'working_dir': self.working_dir if self.working_dir else None,
                'startup_command': self.startup_command if self.startup_command else None,
                'env_vars': self.env_vars
            }


def get_available_windows_shells():
    """
    Improved Windows shell detection with better WSL handling
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
                "name": f"PowerShell ({ps_exe.replace('.exe', '')})",
                "description": ps_desc,
                "shell_path": ps_exe,
                "type": "powershell"
            })

    # Windows Subsystem for Linux - IMPROVED DETECTION
    try:
        # Check if WSL is available and properly configured
        result = subprocess.run(
            ["wsl", "--list", "--quiet"],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW  # Hide console window
        )

        if result.returncode == 0 and result.stdout.strip():
            # Parse WSL distributions more carefully
            raw_output = result.stdout.strip()
            lines = [line.strip() for line in raw_output.split('\n') if line.strip()]

            # Filter out empty lines and invalid entries
            valid_distributions = []
            for line in lines:
                # Remove null characters and clean up the line
                clean_line = line.replace('\x00', '').strip()

                # Skip empty lines or lines that are just whitespace
                if not clean_line:
                    continue

                # Skip lines that look like headers or invalid entries
                if clean_line.lower() in ['windows subsystem for linux distributions:', 'name', '----']:
                    continue

                # Remove the default marker (*) if present
                if clean_line.startswith('*'):
                    clean_line = clean_line[1:].strip()

                # Only add if it looks like a valid distribution name
                if clean_line and len(clean_line) > 0:
                    valid_distributions.append(clean_line)

            print(f"Found WSL distributions: {valid_distributions}")

            # Add default WSL entry (uses default distribution)
            if valid_distributions:
                shells.append({
                    "name": "WSL (Default Distribution)",
                    "description": "Windows Subsystem for Linux - Default Distribution",
                    "shell_path": "wsl.exe",
                    "type": "wsl"
                })

                # Only add specific distributions if there are multiple
                if len(valid_distributions) > 1:
                    for distro in valid_distributions:
                        # Skip if distro name looks invalid
                        if len(distro) < 2 or distro.isspace():
                            continue

                        shells.append({
                            "name": f"WSL ({distro})",
                            "description": f"WSL Distribution: {distro}",
                            "shell_path": f"wsl.exe -d {distro}",
                            "type": "wsl"
                        })

    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError) as e:
        print(f"WSL not available or not accessible: {e}")

    return shells


class ConnectionManager:
    """Connection manager supporting both SSH and local terminals (backward compatible)"""

    def __init__(self, settings_manager):
        self.settings_manager = settings_manager
        self.profiles: Dict[str, ConnectionProfile] = {}
        self.connection_history: List[str] = []
        self.max_history = 5

        # Load existing connections and migrate if needed
        self.load_connections()

    def load_connections(self):
        """Load connections from settings with backward compatibility"""
        try:
            # Load profiles
            profiles_data = self.settings_manager.get('connections/profiles', {})
            if isinstance(profiles_data, dict):
                for profile_id, profile_data in profiles_data.items():
                    if isinstance(profile_data, dict):
                        # Migrate old profiles to new format
                        self.profiles[profile_id] = ConnectionProfile.from_dict(profile_data)

            # Load history
            history_data = self.settings_manager.get('connections/history', [])
            if isinstance(history_data, list):
                self.connection_history = history_data[:self.max_history]

        except Exception as e:
            print(f"Error loading connections: {e}")
            self.profiles = {}
            self.connection_history = []

    def save_connections(self):
        """Save connections to settings"""
        try:
            # Save profiles
            profiles_data = {}
            for profile_id, profile in self.profiles.items():
                profiles_data[profile_id] = profile.to_dict()
            self.settings_manager.set('connections/profiles', profiles_data)

            # Save history
            self.settings_manager.set('connections/history', self.connection_history)

        except Exception as e:
            print(f"Error saving connections: {e}")

    def add_profile(self, profile: ConnectionProfile) -> str:
        """Add a new connection profile"""
        # Generate unique ID based on connection type
        if profile.connection_type == 'ssh':
            profile_id = f"ssh_{profile.hostname}_{profile.port}_{profile.username}"
        else:
            shell_name = profile.shell_path.replace('.exe', '').replace(' ', '_')
            profile_id = f"local_{shell_name}_{profile.working_dir}".replace('\\', '_').replace(':', '')

        profile_id = profile_id.replace(' ', '_').replace('@', '_at_')

        # Ensure unique ID
        counter = 1
        base_id = profile_id
        while profile_id in self.profiles:
            profile_id = f"{base_id}_{counter}"
            counter += 1

        self.profiles[profile_id] = profile
        self.save_connections()
        return profile_id

    # Rest of the methods remain the same as before
    def update_profile(self, profile_id: str, profile: ConnectionProfile):
        """Update an existing profile"""
        if profile_id in self.profiles:
            self.profiles[profile_id] = profile
            self.save_connections()

    def delete_profile(self, profile_id: str):
        """Delete a profile"""
        if profile_id in self.profiles:
            del self.profiles[profile_id]
            if profile_id in self.connection_history:
                self.connection_history.remove(profile_id)
            self.save_connections()

    def get_profile(self, profile_id: str) -> Optional[ConnectionProfile]:
        """Get a profile by ID"""
        return self.profiles.get(profile_id)

    def get_recent_connections(self) -> List[ConnectionProfile]:
        """Get recent connections in order"""
        recent = []
        for profile_id in self.connection_history:
            if profile_id in self.profiles:
                recent.append(self.profiles[profile_id])
        return recent

    def mark_used(self, profile_id: str):
        """Mark a profile as recently used"""
        if profile_id in self.profiles:
            profile = self.profiles[profile_id]
            profile.last_used = datetime.now().isoformat()
            profile.use_count += 1

            if profile_id in self.connection_history:
                self.connection_history.remove(profile_id)
            self.connection_history.insert(0, profile_id)
            self.connection_history = self.connection_history[:self.max_history]

            self.save_connections()

    def get_all_profiles(self) -> List[Tuple[str, ConnectionProfile]]:
        """Get all profiles as (id, profile) tuples"""
        return list(self.profiles.items())


class ConnectionDialog(QDialog):
    """Improved connection dialog with better UI flow"""

    connection_requested = pyqtSignal(dict)

    def __init__(self, parent=None, connection_manager=None):
        super().__init__(parent)
        self.connection_manager = connection_manager
        self.selected_profile_id = None

        self.setWindowTitle("CoolPyTerm Connection Manager")
        self.setModal(True)
        self.resize(700, 600)

        self.setup_ui()
        self.load_profiles()

    def setup_ui(self):
        """Setup improved UI with simplified connection type selection"""
        layout = QVBoxLayout(self)

        # Create tab widget
        tabs = QTabWidget()

        # Connection tab
        connection_tab = QWidget()
        connection_layout = QVBoxLayout(connection_tab)

        # IMPROVED: Simplified connection type selection
        type_group = QGroupBox("Connection Type")
        type_layout = QFormLayout(type_group)

        self.connection_type_combo = QComboBox()
        # Simplified choices - just SSH or Local Shell
        connection_types = ["SSH"]
        if platform.system() == "Windows":
            connection_types.append("Local Shell")
        # Future: Add "Local Shell" for Linux/macOS too

        self.connection_type_combo.addItems(connection_types)
        self.connection_type_combo.currentTextChanged.connect(self.on_connection_type_changed)
        type_layout.addRow("Type:", self.connection_type_combo)

        connection_layout.addWidget(type_group)

        # Connection details form
        self.form_group = QGroupBox("Connection Details")
        self.form_layout = QFormLayout(self.form_group)

        # Name field (always visible)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Optional display name")
        self.form_layout.addRow("Name:", self.name_edit)

        # SSH-specific fields
        self.ssh_fields = {}
        self.ssh_fields['hostname'] = QLineEdit()
        self.ssh_fields['hostname'].setPlaceholderText("hostname or IP address")
        self.form_layout.addRow("Hostname:", self.ssh_fields['hostname'])

        self.ssh_fields['username'] = QLineEdit()
        self.ssh_fields['username'].setPlaceholderText("SSH username")
        self.form_layout.addRow("Username:", self.ssh_fields['username'])

        self.ssh_fields['port'] = QSpinBox()
        self.ssh_fields['port'].setRange(1, 65535)
        self.ssh_fields['port'].setValue(22)
        self.form_layout.addRow("Port:", self.ssh_fields['port'])

        self.ssh_fields['password'] = QLineEdit()
        self.ssh_fields['password'].setEchoMode(QLineEdit.EchoMode.Password)
        self.ssh_fields['password'].setPlaceholderText("SSH password (optional if using key)")
        self.form_layout.addRow("Password:", self.ssh_fields['password'])

        # Key file field with browse button
        key_layout = QHBoxLayout()
        self.ssh_fields['key_path'] = QLineEdit()
        self.ssh_fields['key_path'].setPlaceholderText("Path to SSH private key (optional)")
        self.browse_key_btn = QPushButton("Browse...")
        self.browse_key_btn.clicked.connect(self.browse_key_file)
        key_layout.addWidget(self.ssh_fields['key_path'])
        key_layout.addWidget(self.browse_key_btn)
        self.form_layout.addRow("Key File:", key_layout)

        # IMPROVED: Local shell fields with better shell selection
        self.local_fields = {}

        self.local_fields['shell_combo'] = QComboBox()
        self.local_fields['shell_combo'].setEditable(True)
        self._populate_shell_combo()
        self.form_layout.addRow("Shell:", self.local_fields['shell_combo'])

        self.local_fields['working_dir'] = QLineEdit()
        self.local_fields['working_dir'].setPlaceholderText("Starting directory (optional)")
        working_dir_layout = QHBoxLayout()
        working_dir_layout.addWidget(self.local_fields['working_dir'])
        browse_dir_btn = QPushButton("Browse...")
        browse_dir_btn.clicked.connect(self.browse_working_dir)
        working_dir_layout.addWidget(browse_dir_btn)
        self.form_layout.addRow("Working Dir:", working_dir_layout)

        self.local_fields['startup_command'] = QLineEdit()
        self.local_fields['startup_command'].setPlaceholderText("Command to run on startup (optional)")
        self.form_layout.addRow("Startup Cmd:", self.local_fields['startup_command'])

        connection_layout.addWidget(self.form_group)

        # Profile management buttons
        profile_buttons_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save Profile")
        self.save_btn.clicked.connect(self.save_profile)
        profile_buttons_layout.addWidget(self.save_btn)

        self.delete_btn = QPushButton("Delete Profile")
        self.delete_btn.clicked.connect(self.delete_profile)
        self.delete_btn.setEnabled(False)
        profile_buttons_layout.addWidget(self.delete_btn)

        profile_buttons_layout.addStretch()
        connection_layout.addLayout(profile_buttons_layout)

        tabs.addTab(connection_tab, "Connection")

        # Saved Profiles tab
        profiles_tab = QWidget()
        profiles_layout = QVBoxLayout(profiles_tab)

        profiles_group = QGroupBox("Saved Profiles")
        profiles_group_layout = QVBoxLayout(profiles_group)

        self.profile_list = QListWidget()
        self.profile_list.itemClicked.connect(self.on_profile_selected)
        self.profile_list.itemDoubleClicked.connect(self.on_profile_double_clicked)
        profiles_group_layout.addWidget(self.profile_list)

        profiles_layout.addWidget(profiles_group)
        tabs.addTab(profiles_tab, "Saved Profiles")

        layout.addWidget(tabs)

        # Connection buttons
        button_layout = QHBoxLayout()
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.connect_to_server)
        self.connect_btn.setDefault(True)
        button_layout.addWidget(self.connect_btn)

        button_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

        # Initialize field visibility
        self.on_connection_type_changed(self.connection_type_combo.currentText())

    def _populate_shell_combo(self):
        """IMPROVED: Populate shell combo with better shell detection"""
        if platform.system() == "Windows":
            try:
                shells = get_available_windows_shells()

                for shell in shells:
                    # Add item with display name, store actual shell_path as data
                    self.local_fields['shell_combo'].addItem(
                        shell['name'],  # Display name: "Command Prompt"
                        shell['shell_path']  # Actual path: "cmd.exe"
                    )

                print(f"Populated shell combo with {len(shells)} shells")

            except Exception as e:
                print(f"Error populating shells: {e}")
                # Fallback if shell detection fails
                fallback_shells = [
                    ("Command Prompt", "cmd.exe"),
                    ("PowerShell", "powershell.exe"),
                    ("PowerShell Core", "pwsh.exe"),
                ]
                for display_name, shell_path in fallback_shells:
                    self.local_fields['shell_combo'].addItem(display_name, shell_path)

    def on_connection_type_changed(self, connection_type):
        """Handle connection type change"""
        is_ssh = connection_type == "SSH"

        # Show/hide SSH fields
        for field_name, widget in self.ssh_fields.items():
            widget.setVisible(is_ssh)
            # Find the corresponding label and hide it too
            for i in range(self.form_layout.rowCount()):
                item = self.form_layout.itemAt(i, QFormLayout.ItemRole.LabelRole)
                if item and item.widget():
                    label_text = item.widget().text().replace(":", "").lower()
                    if field_name in label_text or (field_name == 'key_path' and 'key file' in label_text):
                        item.widget().setVisible(is_ssh)
                        break

        # Show/hide browse key button
        self.browse_key_btn.setVisible(is_ssh)

        # Show/hide local terminal fields
        for field_name, widget in self.local_fields.items():
            widget.setVisible(not is_ssh)
            # Find and hide corresponding labels
            for i in range(self.form_layout.rowCount()):
                item = self.form_layout.itemAt(i, QFormLayout.ItemRole.LabelRole)
                if item and item.widget():
                    label_text = item.widget().text().replace(":", "").lower()
                    field_labels = {
                        'shell_combo': 'shell',
                        'working_dir': 'working dir',
                        'startup_command': 'startup cmd'
                    }
                    if field_name in field_labels and field_labels[field_name] in label_text:
                        item.widget().setVisible(not is_ssh)
                        break

    def browse_key_file(self):
        """Browse for SSH key file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select SSH Private Key", "", "All Files (*)"
        )
        if file_path:
            self.ssh_fields['key_path'].setText(file_path)

    def browse_working_dir(self):
        """Browse for working directory"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Working Directory"
        )
        if dir_path:
            self.local_fields['working_dir'].setText(dir_path)

    def load_profiles(self):
        """Load profiles into list with connection type indicators"""
        self.profile_list.clear()

        if not self.connection_manager:
            return

        # Add recent connections first
        recent_profiles = self.connection_manager.get_recent_connections()
        if recent_profiles:
            for profile in recent_profiles:
                profile_id = None
                for pid, p in self.connection_manager.get_all_profiles():
                    if p == profile:
                        profile_id = pid
                        break

                if profile_id:
                    # Add connection type icon
                    type_icon = "🖥️" if profile.connection_type == "ssh" else "💻"
                    item = QListWidgetItem(f"⭐ {type_icon} {profile.get_display_name()}")
                    item.setData(Qt.ItemDataRole.UserRole, (profile_id, profile))
                    self.profile_list.addItem(item)

        # Add all other profiles
        all_profiles = self.connection_manager.get_all_profiles()
        recent_ids = [pid for pid, _ in [(pid, p) for pid, p in all_profiles
                      if p in self.connection_manager.get_recent_connections()]]

        for profile_id, profile in all_profiles:
            if profile_id not in recent_ids:
                type_icon = "🖥️" if profile.connection_type == "ssh" else "💻"
                item = QListWidgetItem(f"{type_icon} {profile.get_display_name()}")
                item.setData(Qt.ItemDataRole.UserRole, (profile_id, profile))
                self.profile_list.addItem(item)

    def on_profile_selected(self, item):
        """Handle profile selection and populate form"""
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            profile_id, profile = data
            self.selected_profile_id = profile_id

            # Set connection type first (simplified)
            if profile.connection_type == 'ssh':
                self.connection_type_combo.setCurrentText('SSH')
            else:
                self.connection_type_combo.setCurrentText('Local Shell')

            # Populate common fields
            self.name_edit.setText(profile.name)

            if profile.connection_type == 'ssh':
                # Populate SSH fields
                self.ssh_fields['hostname'].setText(profile.hostname)
                self.ssh_fields['username'].setText(profile.username)
                self.ssh_fields['port'].setValue(profile.port)
                self.ssh_fields['password'].setText(profile.password)
                self.ssh_fields['key_path'].setText(profile.key_path)
            else:
                # Populate local terminal fields
                # Find the combo box item with matching shell_path data
                combo_box = self.local_fields['shell_combo']
                for i in range(combo_box.count()):
                    if combo_box.itemData(i) == profile.shell_path:
                        combo_box.setCurrentIndex(i)
                        break
                else:
                    # If not found, set text directly (for custom paths)
                    combo_box.setCurrentText(profile.shell_path)

                self.local_fields['working_dir'].setText(profile.working_dir)
                self.local_fields['startup_command'].setText(profile.startup_command)

            self.delete_btn.setEnabled(True)

    def on_profile_double_clicked(self, item):
        """Handle double-click - connect immediately"""
        self.on_profile_selected(item)
        self.connect_to_server()

    def save_profile(self):
        """Save current form data as a profile"""
        if not self.connection_manager:
            QMessageBox.warning(self, "Error", "No connection manager available.")
            return

        connection_type = 'ssh' if self.connection_type_combo.currentText() == 'SSH' else 'local'

        if connection_type == 'ssh':
            hostname = self.ssh_fields['hostname'].text().strip()
            username = self.ssh_fields['username'].text().strip()

            if not hostname or not username:
                QMessageBox.warning(self, "Invalid Profile", "Hostname and username are required for SSH.")
                return

            profile = ConnectionProfile(
                name=self.name_edit.text().strip() or f"{username}@{hostname}",
                connection_type='ssh',
                hostname=hostname,
                username=username,
                port=self.ssh_fields['port'].value(),
                password=self.ssh_fields['password'].text(),
                key_path=self.ssh_fields['key_path'].text().strip()
            )
        else:
            # Get the actual shell path from combo box data, not display text
            combo_box = self.local_fields['shell_combo']
            current_index = combo_box.currentIndex()

            if current_index >= 0:
                # Get stored shell_path data
                shell_path = combo_box.itemData(current_index)
            else:
                # Fallback to current text if no data
                shell_path = combo_box.currentText()

            if not shell_path:
                QMessageBox.warning(self, "Invalid Profile", "Shell path is required for local terminals.")
                return

            profile = ConnectionProfile(
                name=self.name_edit.text().strip() or f"{shell_path} Terminal",
                connection_type='local',
                shell_path=shell_path,
                working_dir=self.local_fields['working_dir'].text().strip(),
                startup_command=self.local_fields['startup_command'].text().strip()
            )

        if self.selected_profile_id:
            self.connection_manager.update_profile(self.selected_profile_id, profile)
            QMessageBox.information(self, "Profile Updated", f"Profile '{profile.get_display_name()}' updated.")
        else:
            self.connection_manager.add_profile(profile)
            QMessageBox.information(self, "Profile Saved", f"Profile '{profile.get_display_name()}' saved.")

        self.load_profiles()

    def delete_profile(self):
        """Delete selected profile"""
        if not self.selected_profile_id or not self.connection_manager:
            return

        profile = self.connection_manager.get_profile(self.selected_profile_id)
        if not profile:
            return

        reply = QMessageBox.question(
            self, "Delete Profile",
            f"Delete profile '{profile.get_display_name()}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.connection_manager.delete_profile(self.selected_profile_id)
            self.selected_profile_id = None
            self.delete_btn.setEnabled(False)
            self.clear_form()
            self.load_profiles()
            QMessageBox.information(self, "Profile Deleted", "Profile deleted successfully.")

    def clear_form(self):
        """Clear all form fields"""
        self.name_edit.clear()

        # Clear SSH fields
        for widget in self.ssh_fields.values():
            if isinstance(widget, QLineEdit):
                widget.clear()
            elif isinstance(widget, QSpinBox):
                widget.setValue(22)

        # Clear local fields
        for widget in self.local_fields.values():
            if isinstance(widget, QLineEdit):
                widget.clear()
            elif isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)

    def connect_to_server(self):
        """Connect using current form data"""
        connection_type = 'ssh' if self.connection_type_combo.currentText() == 'SSH' else 'local'

        if connection_type == 'ssh':
            hostname = self.ssh_fields['hostname'].text().strip()
            username = self.ssh_fields['username'].text().strip()

            if not hostname or not username:
                QMessageBox.warning(self, "Invalid Connection", "Hostname and username required for SSH.")
                return

            connection_config = {
                'connection_type': 'ssh',
                'hostname': hostname,
                'username': username,
                'password': self.ssh_fields['password'].text(),
                'port': self.ssh_fields['port'].value(),
                'key_path': self.ssh_fields['key_path'].text().strip() or None
            }
        else:
            # Get the actual shell path from combo box data, not display text
            combo_box = self.local_fields['shell_combo']
            current_index = combo_box.currentIndex()

            if current_index >= 0:
                # Get stored shell_path data
                shell_path = combo_box.itemData(current_index)
            else:
                # Fallback to current text if no data
                shell_path = combo_box.currentText()

            if not shell_path:
                QMessageBox.warning(self, "Invalid Connection", "Shell path required for local terminal.")
                return

            # Map shell paths to backend types
            shell_type_map = {
                'cmd.exe': 'cmd',
                'cmd': 'cmd',
                'powershell.exe': 'powershell',
                'powershell': 'powershell',
                'pwsh.exe': 'powershell',
                'pwsh': 'powershell',
                'wsl.exe': 'wsl',
                'wsl': 'wsl'
            }

            # Handle WSL with distribution specification
            backend_type = 'wsl' if 'wsl' in shell_path.lower() else shell_type_map.get(shell_path.lower(), 'cmd')

            connection_config = {
                'connection_type': backend_type,
                'shell_path': shell_path,
                'working_dir': self.local_fields['working_dir'].text().strip() or None,
                'startup_command': self.local_fields['startup_command'].text().strip() or None,
                'env_vars': {}
            }

        # Mark profile as used
        if self.selected_profile_id and self.connection_manager:
            self.connection_manager.mark_used(self.selected_profile_id)

        # Emit connection request
        self.connection_requested.emit(connection_config)
        self.accept()