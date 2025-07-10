"""
Enhanced Terminal with Qt Settings and Ambient Glow Controls
Adds proper settings persistence and fine-grained ambient glow controls
"""
import os
import sys
import time
import math
from PyQt6.QtWidgets import (QWidget, QApplication, QMainWindow, QVBoxLayout,
                             QHBoxLayout, QLabel, QSlider, QSpinBox, QCheckBox,
                             QGroupBox, QDialog, QPushButton, QTabWidget,
                             QDialogButtonBox, QGridLayout, QComboBox)
from PyQt6.QtCore import QTimer, Qt, pyqtSlot, QRect, QSettings, pyqtSignal
from PyQt6.QtGui import QAction, QActionGroup, QFont, QFontMetrics, QColor, QPainter, QPen, QBrush, QImage, QKeySequence


# Your existing imports would go here
# from coolpyterm.opengl_grid_widget import OpenGLRetroGridWidget
# from coolpyterm.ssh_backend import SSHBackend
# from coolpyterm.key_handler_ssh import KeyHandler
# from coolpyterm.retro_theme_manager import RetroThemeManager


class SettingsManager:
    """
    Centralized settings management using QSettings for cross-platform persistence
    """

    def __init__(self):
        # Initialize QSettings with organization and application name
        self.settings = QSettings("RetroTerminal", "HardwareAcceleratedTerminal")

        # Define default values
        self.defaults = {
            # CRT Effects
            'effects/glow_enabled': True,
            'effects/glow_intensity': 0.6,
            'effects/scanlines_enabled': True,
            'effects/scanline_intensity': 0.25,
            'effects/flicker_enabled': True,
            'effects/flicker_intensity': 0.08,
            'effects/ambient_glow': 0.12,
            'effects/curvature': 0.08,
            'effects/brightness': 1.1,
            'effects/contrast': 1.05,
            'effects/vignette_strength': 0.2,

            # Cursor
            'cursor/blink_enabled': True,
            'cursor/blink_rate': 500,
            'cursor/style': 'block',  # block, underline, beam

            # Terminal
            'terminal/font_family': 'Consolas',
            'terminal/font_size': 12,
            'terminal/cols': 80,
            'terminal/rows': 24,
            'terminal/theme': 'green',
            'terminal/scrollback_lines': 1000,

            # Window
            'window/width': 1200,
            'window/height': 800,
            'window/x': 100,
            'window/y': 100,
            'window/maximized': False,
            'window/fullscreen': False,

            # SSH
            'ssh/last_host': '',
            'ssh/last_username': '',
            'ssh/last_port': 22,
            'ssh/save_credentials': False,
        }

    def get(self, key, default=None):
        """Get a setting value with fallback to defaults"""
        if default is None:
            default = self.defaults.get(key)
        return self.settings.value(key, default)

    def set(self, key, value):
        """Set a setting value and sync immediately"""
        self.settings.setValue(key, value)
        self.settings.sync()

    def get_bool(self, key):
        """Get boolean setting (QSettings stores as string)"""
        value = self.get(key)
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)

    def get_int(self, key):
        """Get integer setting"""
        return int(self.get(key, 0))

    def get_float(self, key):
        """Get float setting"""
        return float(self.get(key, 0.0))

    def restore_defaults(self):
        """Restore all settings to defaults"""
        for key, value in self.defaults.items():
            self.set(key, value)

    def export_settings(self, filename):
        """Export settings to a file"""
        try:
            export_settings = QSettings(filename, QSettings.Format.IniFormat)
            for key in self.settings.allKeys():
                export_settings.setValue(key, self.settings.value(key))
            export_settings.sync()
            return True
        except Exception as e:
            print(f"Failed to export settings: {e}")
            return False

    def import_settings(self, filename):
        """Import settings from a file"""
        try:
            import_settings = QSettings(filename, QSettings.Format.IniFormat)
            for key in import_settings.allKeys():
                self.settings.setValue(key, import_settings.value(key))
            self.settings.sync()
            return True
        except Exception as e:
            print(f"Failed to import settings: {e}")
            return False


class AdvancedSettingsDialog(QDialog):
    """
    Advanced settings dialog with real-time preview and fine controls
    """

    # Signal emitted when settings change
    settings_changed = pyqtSignal(str, object)  # key, value

    def __init__(self, parent=None, settings_manager=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setWindowTitle("Advanced CRT Settings")
        self.setModal(False)  # Allow interaction with main window
        self.resize(400, 600)

        # Create tabbed interface
        self.setup_ui()
        self.load_current_settings()

        # Connect all controls to update methods
        self.connect_controls()

    def setup_ui(self):
        """Setup the UI with tabs for different setting categories"""
        layout = QVBoxLayout(self)

        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # CRT Effects tab
        self.create_crt_effects_tab()

        # Cursor tab
        self.create_cursor_tab()

        # Terminal tab
        self.create_terminal_tab()

        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.RestoreDefaults |
            QDialogButtonBox.StandardButton.Close
        )
        button_box.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(self.restore_defaults)
        button_box.button(QDialogButtonBox.StandardButton.Close).clicked.connect(self.close)
        layout.addWidget(button_box)

    def create_crt_effects_tab(self):
        """Create CRT effects configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Ambient Glow Group - THE MAIN FEATURE
        ambient_group = QGroupBox("Ambient Background Glow")
        ambient_layout = QGridLayout(ambient_group)

        # Ambient glow enable
        self.ambient_enabled = QCheckBox("Enable Ambient Glow")
        ambient_layout.addWidget(self.ambient_enabled, 0, 0, 1, 2)

        # Ambient glow intensity - HIGH PRECISION
        ambient_layout.addWidget(QLabel("Intensity:"), 1, 0)
        self.ambient_slider = QSlider(Qt.Orientation.Horizontal)
        self.ambient_slider.setRange(0, 100)  # 0.00 to 1.00
        self.ambient_slider.setValue(12)  # Default 0.12
        self.ambient_spinbox = QSpinBox()
        self.ambient_spinbox.setRange(0, 100)
        self.ambient_spinbox.setSuffix("%")
        self.ambient_spinbox.setValue(12)
        ambient_layout.addWidget(self.ambient_slider, 1, 1)
        ambient_layout.addWidget(self.ambient_spinbox, 1, 2)

        # Ambient glow color temperature
        ambient_layout.addWidget(QLabel("Color Temperature:"), 2, 0)
        self.ambient_temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.ambient_temp_slider.setRange(0, 100)  # Cool to warm
        self.ambient_temp_slider.setValue(50)  # Neutral
        self.ambient_temp_spinbox = QSpinBox()
        self.ambient_temp_spinbox.setRange(0, 100)
        self.ambient_temp_spinbox.setSuffix("%")
        self.ambient_temp_spinbox.setValue(50)
        ambient_layout.addWidget(self.ambient_temp_slider, 2, 1)
        ambient_layout.addWidget(self.ambient_temp_spinbox, 2, 2)

        # Monitor brightness compensation
        ambient_layout.addWidget(QLabel("Monitor Compensation:"), 3, 0)
        self.monitor_comp_slider = QSlider(Qt.Orientation.Horizontal)
        self.monitor_comp_slider.setRange(-50, 50)  # -0.5 to +0.5
        self.monitor_comp_slider.setValue(0)  # Default 0
        self.monitor_comp_spinbox = QSpinBox()
        self.monitor_comp_spinbox.setRange(-50, 50)
        self.monitor_comp_spinbox.setValue(0)
        ambient_layout.addWidget(self.monitor_comp_slider, 3, 1)
        ambient_layout.addWidget(self.monitor_comp_spinbox, 3, 2)

        layout.addWidget(ambient_group)

        # Phosphor Glow Group
        phosphor_group = QGroupBox("Phosphor Glow")
        phosphor_layout = QGridLayout(phosphor_group)

        self.glow_enabled = QCheckBox("Enable Phosphor Glow")
        phosphor_layout.addWidget(self.glow_enabled, 0, 0, 1, 2)

        phosphor_layout.addWidget(QLabel("Intensity:"), 1, 0)
        self.glow_slider = QSlider(Qt.Orientation.Horizontal)
        self.glow_slider.setRange(0, 100)
        self.glow_slider.setValue(60)
        self.glow_spinbox = QSpinBox()
        self.glow_spinbox.setRange(0, 100)
        self.glow_spinbox.setSuffix("%")
        self.glow_spinbox.setValue(60)
        phosphor_layout.addWidget(self.glow_slider, 1, 1)
        phosphor_layout.addWidget(self.glow_spinbox, 1, 2)

        layout.addWidget(phosphor_group)

        # Scanlines Group
        scanlines_group = QGroupBox("Scanlines")
        scanlines_layout = QGridLayout(scanlines_group)

        self.scanlines_enabled = QCheckBox("Enable Scanlines")
        scanlines_layout.addWidget(self.scanlines_enabled, 0, 0, 1, 2)

        scanlines_layout.addWidget(QLabel("Intensity:"), 1, 0)
        self.scanlines_slider = QSlider(Qt.Orientation.Horizontal)
        self.scanlines_slider.setRange(0, 100)
        self.scanlines_slider.setValue(25)
        self.scanlines_spinbox = QSpinBox()
        self.scanlines_spinbox.setRange(0, 100)
        self.scanlines_spinbox.setSuffix("%")
        self.scanlines_spinbox.setValue(25)
        scanlines_layout.addWidget(self.scanlines_slider, 1, 1)
        scanlines_layout.addWidget(self.scanlines_spinbox, 1, 2)

        layout.addWidget(scanlines_group)

        # CRT Characteristics Group
        crt_group = QGroupBox("CRT Characteristics")
        crt_layout = QGridLayout(crt_group)

        # Brightness
        crt_layout.addWidget(QLabel("Brightness:"), 0, 0)
        self.brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.brightness_slider.setRange(50, 200)  # 0.5 to 2.0
        self.brightness_slider.setValue(110)  # 1.1
        self.brightness_spinbox = QSpinBox()
        self.brightness_spinbox.setRange(50, 200)
        self.brightness_spinbox.setSuffix("%")
        self.brightness_spinbox.setValue(110)
        crt_layout.addWidget(self.brightness_slider, 0, 1)
        crt_layout.addWidget(self.brightness_spinbox, 0, 2)

        # Contrast
        crt_layout.addWidget(QLabel("Contrast:"), 1, 0)
        self.contrast_slider = QSlider(Qt.Orientation.Horizontal)
        self.contrast_slider.setRange(50, 200)  # 0.5 to 2.0
        self.contrast_slider.setValue(105)  # 1.05
        self.contrast_spinbox = QSpinBox()
        self.contrast_spinbox.setRange(50, 200)
        self.contrast_spinbox.setSuffix("%")
        self.contrast_spinbox.setValue(105)
        crt_layout.addWidget(self.contrast_slider, 1, 1)
        crt_layout.addWidget(self.contrast_spinbox, 1, 2)

        # Curvature
        crt_layout.addWidget(QLabel("Curvature:"), 2, 0)
        self.curvature_slider = QSlider(Qt.Orientation.Horizontal)
        self.curvature_slider.setRange(0, 20)  # 0.0 to 0.2
        self.curvature_slider.setValue(8)  # 0.08
        self.curvature_spinbox = QSpinBox()
        self.curvature_spinbox.setRange(0, 20)
        self.curvature_spinbox.setValue(8)
        crt_layout.addWidget(self.curvature_slider, 2, 1)
        crt_layout.addWidget(self.curvature_spinbox, 2, 2)

        layout.addWidget(crt_group)

        # Quick presets
        presets_group = QGroupBox("Quick Presets")
        presets_layout = QHBoxLayout(presets_group)

        preset_subtle = QPushButton("Subtle")
        preset_subtle.clicked.connect(lambda: self.apply_preset("subtle"))
        preset_normal = QPushButton("Normal")
        preset_normal.clicked.connect(lambda: self.apply_preset("normal"))
        preset_intense = QPushButton("Intense")
        preset_intense.clicked.connect(lambda: self.apply_preset("intense"))
        preset_custom = QPushButton("Save Custom")
        preset_custom.clicked.connect(self.save_custom_preset)

        presets_layout.addWidget(preset_subtle)
        presets_layout.addWidget(preset_normal)
        presets_layout.addWidget(preset_intense)
        presets_layout.addWidget(preset_custom)

        layout.addWidget(presets_group)

        self.tab_widget.addTab(widget, "CRT Effects")

    def create_cursor_tab(self):
        """Create cursor configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Cursor behavior
        cursor_group = QGroupBox("Cursor Behavior")
        cursor_layout = QGridLayout(cursor_group)

        self.cursor_blink_enabled = QCheckBox("Enable Blinking")
        cursor_layout.addWidget(self.cursor_blink_enabled, 0, 0, 1, 2)

        cursor_layout.addWidget(QLabel("Blink Rate (ms):"), 1, 0)
        self.cursor_blink_rate = QSpinBox()
        self.cursor_blink_rate.setRange(100, 2000)
        self.cursor_blink_rate.setValue(500)
        cursor_layout.addWidget(self.cursor_blink_rate, 1, 1)

        cursor_layout.addWidget(QLabel("Style:"), 2, 0)
        self.cursor_style = QComboBox()
        self.cursor_style.addItems(["Block", "Underline", "Beam"])
        cursor_layout.addWidget(self.cursor_style, 2, 1)

        layout.addWidget(cursor_group)

        self.tab_widget.addTab(widget, "Cursor")

    def create_terminal_tab(self):
        """Create terminal configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Font settings
        font_group = QGroupBox("Font Settings")
        font_layout = QGridLayout(font_group)

        font_layout.addWidget(QLabel("Font Family:"), 0, 0)
        self.font_family = QComboBox()
        self.font_family.addItems(["Consolas", "Courier New", "Monaco", "DejaVu Sans Mono"])
        font_layout.addWidget(self.font_family, 0, 1)

        font_layout.addWidget(QLabel("Font Size:"), 1, 0)
        self.font_size = QSpinBox()
        self.font_size.setRange(6, 24)
        self.font_size.setValue(12)
        font_layout.addWidget(self.font_size, 1, 1)

        layout.addWidget(font_group)

        # Theme settings
        theme_group = QGroupBox("Theme Settings")
        theme_layout = QGridLayout(theme_group)

        theme_layout.addWidget(QLabel("Theme:"), 0, 0)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["green", "amber", "blue", "white", "red"])
        theme_layout.addWidget(self.theme_combo, 0, 1)

        layout.addWidget(theme_group)

        self.tab_widget.addTab(widget, "Terminal")

    def connect_controls(self):
        """Connect all controls to their update methods"""
        # Ambient glow controls
        self.ambient_enabled.toggled.connect(self.update_ambient_glow)
        self.ambient_slider.valueChanged.connect(self.update_ambient_intensity)
        self.ambient_spinbox.valueChanged.connect(self.update_ambient_intensity_spinbox)
        self.ambient_temp_slider.valueChanged.connect(self.update_ambient_temp)
        self.ambient_temp_spinbox.valueChanged.connect(self.update_ambient_temp_spinbox)
        self.monitor_comp_slider.valueChanged.connect(self.update_monitor_compensation)
        self.monitor_comp_spinbox.valueChanged.connect(self.update_monitor_compensation_spinbox)

        # Other controls
        self.glow_enabled.toggled.connect(self.update_glow)
        self.glow_slider.valueChanged.connect(self.update_glow_intensity)
        self.glow_spinbox.valueChanged.connect(self.update_glow_intensity_spinbox)

        self.scanlines_enabled.toggled.connect(self.update_scanlines)
        self.scanlines_slider.valueChanged.connect(self.update_scanlines_intensity)
        self.scanlines_spinbox.valueChanged.connect(self.update_scanlines_intensity_spinbox)

        self.brightness_slider.valueChanged.connect(self.update_brightness)
        self.brightness_spinbox.valueChanged.connect(self.update_brightness_spinbox)

        self.contrast_slider.valueChanged.connect(self.update_contrast)
        self.contrast_spinbox.valueChanged.connect(self.update_contrast_spinbox)

        self.curvature_slider.valueChanged.connect(self.update_curvature)
        self.curvature_spinbox.valueChanged.connect(self.update_curvature_spinbox)

        # Cursor controls
        self.cursor_blink_enabled.toggled.connect(self.update_cursor_blink)
        self.cursor_blink_rate.valueChanged.connect(self.update_cursor_blink_rate)

        # Terminal controls
        self.font_family.currentTextChanged.connect(self.update_font_family)
        self.font_size.valueChanged.connect(self.update_font_size)
        self.theme_combo.currentTextChanged.connect(self.update_theme)

    def update_ambient_glow(self):
        """Update ambient glow enable/disable"""
        enabled = self.ambient_enabled.isChecked()
        self.settings_changed.emit('effects/ambient_glow_enabled', enabled)
        self.settings_manager.set('effects/ambient_glow_enabled', enabled)

    def update_ambient_intensity(self, value):
        """Update ambient glow intensity from slider"""
        self.ambient_spinbox.setValue(value)
        intensity = value / 100.0  # Convert to 0.0-1.0 range
        self.settings_changed.emit('effects/ambient_glow', intensity)
        self.settings_manager.set('effects/ambient_glow', intensity)

    def update_ambient_intensity_spinbox(self, value):
        """Update ambient glow intensity from spinbox"""
        self.ambient_slider.setValue(value)
        intensity = value / 100.0
        self.settings_changed.emit('effects/ambient_glow', intensity)
        self.settings_manager.set('effects/ambient_glow', intensity)

    def update_ambient_temp(self, value):
        """Update ambient glow color temperature"""
        self.ambient_temp_spinbox.setValue(value)
        temp = value / 100.0
        self.settings_changed.emit('effects/ambient_temperature', temp)
        self.settings_manager.set('effects/ambient_temperature', temp)

    def update_ambient_temp_spinbox(self, value):
        """Update ambient glow color temperature from spinbox"""
        self.ambient_temp_slider.setValue(value)
        temp = value / 100.0
        self.settings_changed.emit('effects/ambient_temperature', temp)
        self.settings_manager.set('effects/ambient_temperature', temp)

    def update_monitor_compensation(self, value):
        """Update monitor brightness compensation"""
        self.monitor_comp_spinbox.setValue(value)
        comp = value / 100.0  # Convert to -0.5 to +0.5 range
        self.settings_changed.emit('effects/monitor_compensation', comp)
        self.settings_manager.set('effects/monitor_compensation', comp)

    def update_monitor_compensation_spinbox(self, value):
        """Update monitor brightness compensation from spinbox"""
        self.monitor_comp_slider.setValue(value)
        comp = value / 100.0
        self.settings_changed.emit('effects/monitor_compensation', comp)
        self.settings_manager.set('effects/monitor_compensation', comp)

    def update_glow(self):
        """Update phosphor glow enable/disable"""
        enabled = self.glow_enabled.isChecked()
        self.settings_changed.emit('effects/glow_enabled', enabled)
        self.settings_manager.set('effects/glow_enabled', enabled)

    def update_glow_intensity(self, value):
        """Update phosphor glow intensity"""
        self.glow_spinbox.setValue(value)
        intensity = value / 100.0
        self.settings_changed.emit('effects/glow_intensity', intensity)
        self.settings_manager.set('effects/glow_intensity', intensity)

    def update_glow_intensity_spinbox(self, value):
        """Update phosphor glow intensity from spinbox"""
        self.glow_slider.setValue(value)
        intensity = value / 100.0
        self.settings_changed.emit('effects/glow_intensity', intensity)
        self.settings_manager.set('effects/glow_intensity', intensity)

    def update_scanlines(self):
        """Update scanlines enable/disable"""
        enabled = self.scanlines_enabled.isChecked()
        self.settings_changed.emit('effects/scanlines_enabled', enabled)
        self.settings_manager.set('effects/scanlines_enabled', enabled)

    def update_scanlines_intensity(self, value):
        """Update scanlines intensity"""
        self.scanlines_spinbox.setValue(value)
        intensity = value / 100.0
        self.settings_changed.emit('effects/scanline_intensity', intensity)
        self.settings_manager.set('effects/scanline_intensity', intensity)

    def update_scanlines_intensity_spinbox(self, value):
        """Update scanlines intensity from spinbox"""
        self.scanlines_slider.setValue(value)
        intensity = value / 100.0
        self.settings_changed.emit('effects/scanline_intensity', intensity)
        self.settings_manager.set('effects/scanline_intensity', intensity)

    def update_brightness(self, value):
        """Update brightness"""
        self.brightness_spinbox.setValue(value)
        brightness = value / 100.0
        self.settings_changed.emit('effects/brightness', brightness)
        self.settings_manager.set('effects/brightness', brightness)

    def update_brightness_spinbox(self, value):
        """Update brightness from spinbox"""
        self.brightness_slider.setValue(value)
        brightness = value / 100.0
        self.settings_changed.emit('effects/brightness', brightness)
        self.settings_manager.set('effects/brightness', brightness)

    def update_contrast(self, value):
        """Update contrast"""
        self.contrast_spinbox.setValue(value)
        contrast = value / 100.0
        self.settings_changed.emit('effects/contrast', contrast)
        self.settings_manager.set('effects/contrast', contrast)

    def update_contrast_spinbox(self, value):
        """Update contrast from spinbox"""
        self.contrast_slider.setValue(value)
        contrast = value / 100.0
        self.settings_changed.emit('effects/contrast', contrast)
        self.settings_manager.set('effects/contrast', contrast)

    def update_curvature(self, value):
        """Update curvature"""
        self.curvature_spinbox.setValue(value)
        curvature = value / 100.0
        self.settings_changed.emit('effects/curvature', curvature)
        self.settings_manager.set('effects/curvature', curvature)

    def update_curvature_spinbox(self, value):
        """Update curvature from spinbox"""
        self.curvature_slider.setValue(value)
        curvature = value / 100.0
        self.settings_changed.emit('effects/curvature', curvature)
        self.settings_manager.set('effects/curvature', curvature)

    def update_cursor_blink(self):
        """Update cursor blink enable/disable"""
        enabled = self.cursor_blink_enabled.isChecked()
        self.settings_changed.emit('cursor/blink_enabled', enabled)
        self.settings_manager.set('cursor/blink_enabled', enabled)

    def update_cursor_blink_rate(self, value):
        """Update cursor blink rate"""
        self.settings_changed.emit('cursor/blink_rate', value)
        self.settings_manager.set('cursor/blink_rate', value)

    def update_font_family(self, font_family):
        """Update font family"""
        self.settings_changed.emit('terminal/font_family', font_family)
        self.settings_manager.set('terminal/font_family', font_family)

    def update_font_size(self, size):
        """Update font size"""
        self.settings_changed.emit('terminal/font_size', size)
        self.settings_manager.set('terminal/font_size', size)

    def update_theme(self, theme):
        """Update theme"""
        self.settings_changed.emit('terminal/theme', theme)
        self.settings_manager.set('terminal/theme', theme)

    def load_current_settings(self):
        """Load current settings into the dialog"""
        if not self.settings_manager:
            return

        # Load ambient glow settings
        self.ambient_enabled.setChecked(self.settings_manager.get_bool('effects/ambient_glow_enabled'))
        ambient_intensity = int(self.settings_manager.get_float('effects/ambient_glow') * 100)
        self.ambient_slider.setValue(ambient_intensity)
        self.ambient_spinbox.setValue(ambient_intensity)

        # Load other settings
        glow_intensity = int(self.settings_manager.get_float('effects/glow_intensity') * 100)
        self.glow_enabled.setChecked(self.settings_manager.get_bool('effects/glow_enabled'))
        self.glow_slider.setValue(glow_intensity)
        self.glow_spinbox.setValue(glow_intensity)

        scanlines_intensity = int(self.settings_manager.get_float('effects/scanline_intensity') * 100)
        self.scanlines_enabled.setChecked(self.settings_manager.get_bool('effects/scanlines_enabled'))
        self.scanlines_slider.setValue(scanlines_intensity)
        self.scanlines_spinbox.setValue(scanlines_intensity)

        brightness = int(self.settings_manager.get_float('effects/brightness') * 100)
        self.brightness_slider.setValue(brightness)
        self.brightness_spinbox.setValue(brightness)

        contrast = int(self.settings_manager.get_float('effects/contrast') * 100)
        self.contrast_slider.setValue(contrast)
        self.contrast_spinbox.setValue(contrast)

        curvature = int(self.settings_manager.get_float('effects/curvature') * 100)
        self.curvature_slider.setValue(curvature)
        self.curvature_spinbox.setValue(curvature)

        # Load cursor settings
        self.cursor_blink_enabled.setChecked(self.settings_manager.get_bool('cursor/blink_enabled'))
        self.cursor_blink_rate.setValue(self.settings_manager.get_int('cursor/blink_rate'))

        # Load terminal settings
        self.font_family.setCurrentText(self.settings_manager.get('terminal/font_family'))
        self.font_size.setValue(self.settings_manager.get_int('terminal/font_size'))
        self.theme_combo.setCurrentText(self.settings_manager.get('terminal/theme'))

    def apply_preset(self, preset_name):
        """Apply a preset configuration"""
        presets = {
            'subtle': {
                'ambient_glow': 0.05,
                'glow_intensity': 0.3,
                'scanlines_intensity': 0.1,
                'brightness': 1.0,
                'contrast': 1.0,
            },
            'normal': {
                'ambient_glow': 0.12,
                'glow_intensity': 0.6,
                'scanlines_intensity': 0.25,
                'brightness': 1.1,
                'contrast': 1.05,
            },
            'intense': {
                'ambient_glow': 0.25,
                'glow_intensity': 0.8,
                'scanlines_intensity': 0.4,
                'brightness': 1.2,
                'contrast': 1.15,
            }
        }

        if preset_name in presets:
            preset = presets[preset_name]

            # Update sliders and emit changes
            self.ambient_slider.setValue(int(preset['ambient_glow'] * 100))
            self.glow_slider.setValue(int(preset['glow_intensity'] * 100))
            self.scanlines_slider.setValue(int(preset['scanlines_intensity'] * 100))
            self.brightness_slider.setValue(int(preset['brightness'] * 100))
            self.contrast_slider.setValue(int(preset['contrast'] * 100))

            print(f"Applied {preset_name} preset")

    def save_custom_preset(self):
        """Save current settings as a custom preset"""
        # This could open a dialog to name the preset
        # For now, just save to a "custom" preset
        custom_preset = {
            'ambient_glow': self.ambient_slider.value() / 100.0,
            'glow_intensity': self.glow_slider.value() / 100.0,
            'scanlines_intensity': self.scanlines_slider.value() / 100.0,
            'brightness': self.brightness_slider.value() / 100.0,
            'contrast': self.contrast_slider.value() / 100.0,
        }

        self.settings_manager.set('presets/custom', custom_preset)
        print("Custom preset saved")

    def restore_defaults(self):
        """Restore all settings to defaults"""
        self.settings_manager.restore_defaults()
        self.load_current_settings()
        print("Settings restored to defaults")


# Integration methods for your existing terminal class
class EnhancedTerminalMixin:
    """
    Mixin to add to your existing TerminalWithHardwareGrid class
    """

    def __init__(self, *args, **kwargs):
        # Initialize settings manager
        self.settings_manager = SettingsManager()

        # Initialize settings dialog
        self.settings_dialog = None

        # Load settings and apply them
        self.load_settings()

        # Continue with normal initialization
        super().__init__(*args, **kwargs)

    def load_settings(self):
        """Load settings and apply them to the terminal"""
        # Load CRT effects settings
        self.glow_enabled = self.settings_manager.get_bool('effects/glow_enabled')
        self.glow_intensity = self.settings_manager.get_float('effects/glow_intensity')
        self.scanlines_enabled = self.settings_manager.get_bool('effects/scanlines_enabled')
        self.scanline_intensity = self.settings_manager.get_float('effects/scanline_intensity')
        self.flicker_enabled = self.settings_manager.get_bool('effects/flicker_enabled')
        self.flicker_intensity = self.settings_manager.get_float('effects/flicker_intensity')
        self.ambient_glow = self.settings_manager.get_float('effects/ambient_glow')
        self.curvature = self.settings_manager.get_float('effects/curvature')
        self.brightness = self.settings_manager.get_float('effects/brightness')
        self.contrast = self.settings_manager.get_float('effects/contrast')

        # Load cursor settings
        self.cursor_blink_enabled = self.settings_manager.get_bool('cursor/blink_enabled')
        cursor_blink_rate = self.settings_manager.get_int('cursor/blink_rate')

        # Load terminal settings
        font_family = self.settings_manager.get('terminal/font_family')
        font_size = self.settings_manager.get_int('terminal/font_size')
        theme = self.settings_manager.get('terminal/theme')

        # Apply settings
        if hasattr(self, 'grid_widget'):
            self.grid_widget.glow_enabled = self.glow_enabled
            self.grid_widget.glow_intensity = self.glow_intensity
            self.grid_widget.scanlines_enabled = self.scanlines_enabled
            self.grid_widget.scanline_intensity = self.scanline_intensity
            self.grid_widget.flicker_enabled = self.flicker_enabled
            self.grid_widget.flicker_intensity = self.flicker_intensity
            self.grid_widget.ambient_glow = self.ambient_glow
            self.grid_widget.curvature = self.curvature
            self.grid_widget.brightness = self.brightness
            self.grid_widget.contrast = self.contrast

            # Apply cursor settings
            self.grid_widget.enable_cursor_blink(self.cursor_blink_enabled)
            self.grid_widget.set_cursor_blink_rate(cursor_blink_rate)

        # Apply theme
        if hasattr(self, 'theme_manager'):
            self.theme_manager.set_current_theme(theme)

    def save_settings(self):
        """Save current settings"""
        if hasattr(self, 'grid_widget'):
            self.settings_manager.set('effects/glow_enabled', self.grid_widget.glow_enabled)
            self.settings_manager.set('effects/glow_intensity', self.grid_widget.glow_intensity)
            self.settings_manager.set('effects/scanlines_enabled', self.grid_widget.scanlines_enabled)
            self.settings_manager.set('effects/scanline_intensity', self.grid_widget.scanline_intensity)
            self.settings_manager.set('effects/flicker_enabled', self.grid_widget.flicker_enabled)
            self.settings_manager.set('effects/flicker_intensity', self.grid_widget.flicker_intensity)
            self.settings_manager.set('effects/ambient_glow', self.grid_widget.ambient_glow)
            self.settings_manager.set('effects/curvature', self.grid_widget.curvature)
            self.settings_manager.set('effects/brightness', self.grid_widget.brightness)
            self.settings_manager.set('effects/contrast', self.grid_widget.contrast)

    def open_settings_dialog(self):
        """Open the advanced settings dialog"""
        if not self.settings_dialog:
            self.settings_dialog = AdvancedSettingsDialog(self, self.settings_manager)
            self.settings_dialog.settings_changed.connect(self.on_setting_changed)

        self.settings_dialog.show()
        self.settings_dialog.raise_()
        self.settings_dialog.activateWindow()

    def on_setting_changed(self, key, value):
        """Handle real-time setting changes"""
        if key == 'effects/ambient_glow':
            if hasattr(self, 'grid_widget'):
                self.grid_widget.ambient_glow = value
                self.grid_widget.update()
        elif key == 'effects/glow_intensity':
            if hasattr(self, 'grid_widget'):
                self.grid_widget.glow_intensity = value
                self.grid_widget.update()
        elif key == 'effects/scanline_intensity':
            if hasattr(self, 'grid_widget'):
                self.grid_widget.scanline_intensity = value
                self.grid_widget.update()
        elif key == 'effects/brightness':
            if hasattr(self, 'grid_widget'):
                self.grid_widget.brightness = value
                self.grid_widget.update()
        elif key == 'effects/contrast':
            if hasattr(self, 'grid_widget'):
                self.grid_widget.contrast = value
                self.grid_widget.update()
        elif key == 'cursor/blink_enabled':
            if hasattr(self, 'grid_widget'):
                self.grid_widget.enable_cursor_blink(value)
        elif key == 'cursor/blink_rate':
            if hasattr(self, 'grid_widget'):
                self.grid_widget.set_cursor_blink_rate(value)
        elif key == 'terminal/theme':
            if hasattr(self, 'theme_manager'):
                self.theme_manager.set_current_theme(value)
                self.set_theme(value)

        # Always save the setting
        self.save_settings()

    def closeEvent(self, event):
        """Save settings when closing"""
        self.save_settings()
        super().closeEvent(event)


# Example integration with your existing window class
def add_settings_menu_to_window(window):
    """Add settings menu to your existing window"""
    # Add to your existing menu creation
    settings_menu = window.menuBar().addMenu('&Settings')

    # Advanced settings action
    advanced_settings_action = QAction('&Advanced Settings...', window)
    advanced_settings_action.setShortcut('Ctrl+,')
    advanced_settings_action.triggered.connect(window.open_settings_dialog)
    settings_menu.addAction(advanced_settings_action)

    settings_menu.addSeparator()

    # Quick ambient glow controls
    ambient_up_action = QAction('Ambient Glow &Up', window)
    ambient_up_action.setShortcut('Ctrl+Shift+Plus')
    ambient_up_action.triggered.connect(lambda: window.adjust_ambient_glow(0.02))
    settings_menu.addAction(ambient_up_action)

    ambient_down_action = QAction('Ambient Glow &Down', window)
    ambient_down_action.setShortcut('Ctrl+Shift+Minus')
    ambient_down_action.triggered.connect(lambda: window.adjust_ambient_glow(-0.02))
    settings_menu.addAction(ambient_down_action)

    settings_menu.addSeparator()

    # Import/Export settings
    export_action = QAction('&Export Settings...', window)
    export_action.triggered.connect(window.export_settings)
    settings_menu.addAction(export_action)

    import_action = QAction('&Import Settings...', window)
    import_action.triggered.connect(window.import_settings)
    settings_menu.addAction(import_action)

    # Restore defaults
    restore_action = QAction('&Restore Defaults', window)
    restore_action.triggered.connect(window.restore_default_settings)
    settings_menu.addAction(restore_action)


# Quick helper methods to add to your window class
def add_settings_helper_methods(window):
    """Add helper methods to your window class"""

    def adjust_ambient_glow(self, delta):
        """Adjust ambient glow by delta amount"""
        if hasattr(self, 'terminal') and hasattr(self.terminal, 'grid_widget'):
            current = self.terminal.grid_widget.ambient_glow
            new_value = max(0.0, min(1.0, current + delta))
            self.terminal.grid_widget.ambient_glow = new_value
            self.terminal.grid_widget.update()

            # Save setting
            if hasattr(self.terminal, 'settings_manager'):
                self.terminal.settings_manager.set('effects/ambient_glow', new_value)

            print(f"Ambient glow adjusted to: {new_value:.3f}")

    def export_settings(self):
        """Export settings to file"""
        from PyQt6.QtWidgets import QFileDialog

        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Settings", "terminal_settings.ini", "INI Files (*.ini)"
        )

        if filename and hasattr(self.terminal, 'settings_manager'):
            if self.terminal.settings_manager.export_settings(filename):
                print(f"Settings exported to: {filename}")

    def import_settings(self):
        """Import settings from file"""
        from PyQt6.QtWidgets import QFileDialog

        filename, _ = QFileDialog.getOpenFileName(
            self, "Import Settings", "", "INI Files (*.ini)"
        )

        if filename and hasattr(self.terminal, 'settings_manager'):
            if self.terminal.settings_manager.import_settings(filename):
                self.terminal.load_settings()
                print(f"Settings imported from: {filename}")

    def restore_default_settings(self):
        """Restore default settings"""
        if hasattr(self.terminal, 'settings_manager'):
            self.terminal.settings_manager.restore_defaults()
            self.terminal.load_settings()
            print("Settings restored to defaults")

    # Add these methods to your window class
    window.adjust_ambient_glow = adjust_ambient_glow.__get__(window, window.__class__)
    window.export_settings = export_settings.__get__(window, window.__class__)
    window.import_settings = import_settings.__get__(window, window.__class__)
    window.restore_default_settings = restore_default_settings.__get__(window, window.__class__)


print("Enhanced settings system created!")
print("Features:")
print("- Cross-platform settings persistence using QSettings")
print("- Real-time ambient glow adjustment with fine controls")
print("- Monitor compensation for different display brightness")
print("- Preset system for quick configuration")
print("- Import/export settings")
print("- Tabbed settings dialog")
print("- All settings auto-save when changed")