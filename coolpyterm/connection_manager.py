"""
Complete ConnectionDialog implementation with proper state management
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



@dataclass
class ConnectionProfile:
    """SSH connection profile with all necessary details"""
    name: str
    hostname: str
    port: int = 22
    username: str = ""
    password: str = ""  # Warning: stored in plaintext for POC
    key_path: str = ""
    description: str = ""
    last_used: str = ""
    use_count: int = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'ConnectionProfile':
        """Create from dictionary"""
        return cls(**data)

    def get_display_name(self) -> str:
        """Get display name for UI"""
        if self.name:
            return f"{self.name} ({self.username}@{self.hostname}:{self.port})"
        return f"{self.username}@{self.hostname}:{self.port}"


class ConnectionManager:
    """Manages SSH connection profiles and history"""

    def __init__(self, settings_manager):
        self.settings_manager = settings_manager
        self.profiles: Dict[str, ConnectionProfile] = {}
        self.connection_history: List[str] = []  # Profile IDs in order of use
        self.max_history = 5

        # Load existing connections
        self.load_connections()

    def load_connections(self):
        """Load connections from settings"""
        try:
            # Load profiles
            profiles_data = self.settings_manager.get('connections/profiles', {})
            if isinstance(profiles_data, dict):
                for profile_id, profile_data in profiles_data.items():
                    if isinstance(profile_data, dict):
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
        # Generate unique ID
        profile_id = f"{profile.hostname}_{profile.port}_{profile.username}"
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

    def update_profile(self, profile_id: str, profile: ConnectionProfile):
        """Update an existing profile"""
        if profile_id in self.profiles:
            self.profiles[profile_id] = profile
            self.save_connections()

    def delete_profile(self, profile_id: str):
        """Delete a profile"""
        if profile_id in self.profiles:
            del self.profiles[profile_id]
            # Remove from history
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
            # Update profile
            profile = self.profiles[profile_id]
            profile.last_used = datetime.now().isoformat()
            profile.use_count += 1

            # Update history
            if profile_id in self.connection_history:
                self.connection_history.remove(profile_id)
            self.connection_history.insert(0, profile_id)

            # Keep only max_history items
            self.connection_history = self.connection_history[:self.max_history]

            self.save_connections()

    def get_all_profiles(self) -> List[Tuple[str, ConnectionProfile]]:
        """Get all profiles as (id, profile) tuples"""
        return list(self.profiles.items())


class ConnectionDialog(QDialog):
    """Enhanced connection dialog with password field and connection logic"""

    connection_requested = pyqtSignal(dict)  # Emits connection config when user wants to connect

    def __init__(self, parent=None, connection_manager=None):
        super().__init__(parent)
        self.connection_manager = connection_manager
        self.selected_profile_id = None

        self.setWindowTitle("SSH Connection Manager")
        self.setModal(True)
        self.resize(600, 500)

        self.setup_ui()
        self.load_profiles()

    def setup_ui(self):
        """Setup enhanced UI with password field"""
        layout = QVBoxLayout(self)

        # Create tab widget for better organization
        tabs = QTabWidget()

        # Connection tab
        connection_tab = QWidget()
        connection_layout = QVBoxLayout(connection_tab)

        # Connection form
        form_group = QGroupBox("Connection Details")
        form_layout = QFormLayout(form_group)

        # Basic fields
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Optional display name")
        form_layout.addRow("Name:", self.name_edit)

        self.hostname_edit = QLineEdit()
        self.hostname_edit.setPlaceholderText("hostname or IP address")
        form_layout.addRow("Hostname:", self.hostname_edit)

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("SSH username")
        form_layout.addRow("Username:", self.username_edit)

        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(22)
        form_layout.addRow("Port:", self.port_spin)

        # Password field
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("SSH password (optional if using key)")
        form_layout.addRow("Password:", self.password_edit)

        # Key file field
        key_layout = QHBoxLayout()
        self.key_path_edit = QLineEdit()
        self.key_path_edit.setPlaceholderText("Path to SSH private key (optional)")
        self.browse_key_btn = QPushButton("Browse...")
        self.browse_key_btn.clicked.connect(self.browse_key_file)
        key_layout.addWidget(self.key_path_edit)
        key_layout.addWidget(self.browse_key_btn)
        form_layout.addRow("Key File:", key_layout)

        connection_layout.addWidget(form_group)

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

    def browse_key_file(self):
        """Browse for SSH key file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select SSH Private Key", "", "All Files (*)"
        )
        if file_path:
            self.key_path_edit.setText(file_path)

    def load_profiles(self):
        """Load profiles into list"""
        self.profile_list.clear()

        if not self.connection_manager:
            return

        # Add recent connections first
        recent_profiles = self.connection_manager.get_recent_connections()
        if recent_profiles:
            for profile in recent_profiles:
                # Find profile ID
                profile_id = None
                for pid, p in self.connection_manager.get_all_profiles():
                    if p == profile:
                        profile_id = pid
                        break

                if profile_id:
                    item = QListWidgetItem(f"⭐ {profile.get_display_name()}")
                    item.setData(Qt.ItemDataRole.UserRole, (profile_id, profile))
                    self.profile_list.addItem(item)

        # Add all other profiles
        all_profiles = self.connection_manager.get_all_profiles()
        recent_ids = [pid for pid, _ in [(pid, p) for pid, p in all_profiles
                      if p in self.connection_manager.get_recent_connections()]]

        for profile_id, profile in all_profiles:
            if profile_id not in recent_ids:
                item = QListWidgetItem(profile.get_display_name())
                item.setData(Qt.ItemDataRole.UserRole, (profile_id, profile))
                self.profile_list.addItem(item)

    def on_profile_selected(self, item):
        """Handle profile selection"""
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            profile_id, profile = data
            self.selected_profile_id = profile_id

            # Populate form with profile data
            self.name_edit.setText(profile.name)
            self.hostname_edit.setText(profile.hostname)
            self.username_edit.setText(profile.username)
            self.port_spin.setValue(profile.port)
            self.password_edit.setText(profile.password)
            self.key_path_edit.setText(profile.key_path)

            self.delete_btn.setEnabled(True)

    def on_profile_double_clicked(self, item):
        """Handle double-click on profile - immediately connect"""
        self.on_profile_selected(item)
        self.connect_to_server()

    def save_profile(self):
        """Save current form data as a profile"""
        if not self.connection_manager:
            QMessageBox.warning(self, "Error", "No connection manager available.")
            return

        hostname = self.hostname_edit.text().strip()
        username = self.username_edit.text().strip()

        if not hostname or not username:
            QMessageBox.warning(self, "Invalid Profile", "Hostname and username are required.")
            return

        # Create profile
        profile = ConnectionProfile(
            name=self.name_edit.text().strip() or f"{username}@{hostname}",
            hostname=hostname,
            username=username,
            port=self.port_spin.value(),
            password=self.password_edit.text(),
            key_path=self.key_path_edit.text().strip()
        )

        if self.selected_profile_id:
            # Update existing profile
            self.connection_manager.update_profile(self.selected_profile_id, profile)
            QMessageBox.information(self, "Profile Updated", f"Profile '{profile.get_display_name()}' updated successfully.")
        else:
            # Save new profile
            profile_id = self.connection_manager.add_profile(profile)
            QMessageBox.information(self, "Profile Saved", f"Profile '{profile.get_display_name()}' saved successfully.")

        # Refresh list
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
            f"Are you sure you want to delete the profile '{profile.get_display_name()}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.connection_manager.delete_profile(self.selected_profile_id)
            self.selected_profile_id = None
            self.delete_btn.setEnabled(False)

            # Clear form
            self.clear_form()

            # Refresh list
            self.load_profiles()

            QMessageBox.information(self, "Profile Deleted", "Profile deleted successfully.")

    def clear_form(self):
        """Clear the connection form"""
        self.name_edit.clear()
        self.hostname_edit.clear()
        self.username_edit.clear()
        self.port_spin.setValue(22)
        self.password_edit.clear()
        self.key_path_edit.clear()

    def connect_to_server(self):
        """Connect to server with current form data"""
        hostname = self.hostname_edit.text().strip()
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        key_path = self.key_path_edit.text().strip()

        if not hostname or not username:
            QMessageBox.warning(self, "Invalid Connection", "Hostname and username are required to connect.")
            return

        if not password and not key_path:
            reply = QMessageBox.question(
                self, "No Authentication",
                "No password or key file specified. Continue anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # Create connection config
        connection_config = {
            'hostname': hostname,
            'username': username,
            'password': password,
            'port': self.port_spin.value(),
            'key_path': key_path if key_path else None
        }

        # Mark profile as used if it's a saved profile
        if self.selected_profile_id and self.connection_manager:
            self.connection_manager.mark_used(self.selected_profile_id)

        # Emit connection request
        self.connection_requested.emit(connection_config)

        # Close dialog
        self.accept()
