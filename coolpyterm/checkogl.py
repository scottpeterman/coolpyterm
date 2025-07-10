#!/usr/bin/env python3
"""
Simple test script for OpenGL Grid Widget
Tests the widget in isolation without SSH, terminal emulation, or other complexity
"""
import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QColor

# Add the path to find your opengl_grid_widget
sys.path.append(os.path.dirname(__file__))

# Import your OpenGL widget
from opengl_grid_widget import OpenGLRetroGridWidget


# Simple theme class for testing
class SimpleTheme:
    def __init__(self):
        self.foreground = QColor(0, 255, 0)  # Green
        self.background = QColor(0, 0, 0)  # Black
        self.cursor = QColor(0, 255, 0)  # Green


class SimpleThemeManager:
    def __init__(self):
        self.current_theme_name = "green"
        self.theme = SimpleTheme()

    def get_current_theme(self):
        return self.theme

    def set_current_theme(self, name):
        self.current_theme_name = name


class SimpleOpenGLTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple OpenGL Grid Widget Test")
        self.setGeometry(100, 100, 800, 600)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create theme manager
        self.theme_manager = SimpleThemeManager()

        # Create the OpenGL grid widget
        print("Creating OpenGL grid widget...")
        self.grid_widget = OpenGLRetroGridWidget(
            parent=self,
            font_size=14,
            theme_manager=self.theme_manager
        )
        layout.addWidget(self.grid_widget)

        # Create button panel
        button_layout = QHBoxLayout()

        # Test buttons
        test1_btn = QPushButton("Test 1: Simple Text")
        test1_btn.clicked.connect(self.test_simple_text)
        button_layout.addWidget(test1_btn)

        test2_btn = QPushButton("Test 2: Green Screen")
        test2_btn.clicked.connect(self.test_green_screen)
        button_layout.addWidget(test2_btn)

        test3_btn = QPushButton("Test 3: Save Texture")
        test3_btn.clicked.connect(self.test_save_texture)
        button_layout.addWidget(test3_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.test_clear)
        button_layout.addWidget(clear_btn)

        layout.addLayout(button_layout)

        # Auto-run first test after a short delay
        QTimer.singleShot(1000, self.test_simple_text)
        print("Simple OpenGL test window created")

    def test_simple_text(self):
        """Test 1: Put some simple text in the grid"""
        print("=== TEST 1: SIMPLE TEXT ===")

        # Clear the grid first
        self.grid_widget.clear_screen()

        # Set some test text
        test_lines = [
            "SIMPLE OPENGL TEST",
            "Line 2: Hello World!",
            "Line 3: 123456789",
            "Line 4: ABCDEFGHIJK",
            "Line 5: Special chars: @#$%",
        ]

        for row, line in enumerate(test_lines):
            if row < self.grid_widget.rows:
                print(f"Setting line {row}: '{line}'")
                for col, char in enumerate(line):
                    if col < self.grid_widget.cols:
                        self.grid_widget.set_char(row, col, char)

        # Set cursor position
        self.grid_widget.set_cursor_position(5, 0)

        print("✅ Test text set in grid")
        print("You should see 5 lines of text and a cursor")

    def test_green_screen(self):
        """Test 2: Override paintGL to show simple green screen"""
        print("=== TEST 2: GREEN SCREEN ===")

        # Override paintGL with simple green screen
        def simple_green_paintGL():
            print("Simple green paintGL called")
            try:
                from OpenGL.GL import glClearColor, glClear, GL_COLOR_BUFFER_BIT
                glClearColor(0.0, 1.0, 0.0, 1.0)  # Bright green
                glClear(GL_COLOR_BUFFER_BIT)
                print("✅ Green screen rendered")
            except Exception as e:
                print(f"❌ OpenGL error: {e}")

        # Replace paintGL temporarily
        self.grid_widget.original_paintGL = self.grid_widget.paintGL
        self.grid_widget.paintGL = simple_green_paintGL

        # Force update
        self.grid_widget.update()
        print("Green screen test - you should see bright green")

    def test_save_texture(self):
        """Test 3: Save the texture image to see what's being rendered"""
        print("=== TEST 3: SAVE TEXTURE ===")

        # Restore original paintGL if it was overridden
        if hasattr(self.grid_widget, 'original_paintGL'):
            self.grid_widget.paintGL = self.grid_widget.original_paintGL

        # Make sure we have some text
        self.test_simple_text()

        # Force texture update
        self.grid_widget.render_grid_to_texture()

        # Save the texture image
        if self.grid_widget.text_image:
            filename = "debug_texture_simple.png"
            if self.grid_widget.text_image.save(filename):
                print(f"✅ Texture saved to {filename}")
                print(f"File size: {os.path.getsize(filename)} bytes")
                print("Open this PNG file to see the rendered characters")
            else:
                print("❌ Failed to save texture")
        else:
            print("❌ No text image found")

    def test_clear(self):
        """Clear the screen"""
        print("=== CLEARING SCREEN ===")

        # Restore original paintGL if needed
        if hasattr(self.grid_widget, 'original_paintGL'):
            self.grid_widget.paintGL = self.grid_widget.original_paintGL

        self.grid_widget.clear_screen()
        print("✅ Screen cleared")

    def keyPressEvent(self, event):
        """Handle key presses"""
        if event.key() == Qt.Key.Key_1:
            self.test_simple_text()
        elif event.key() == Qt.Key.Key_2:
            self.test_green_screen()
        elif event.key() == Qt.Key.Key_3:
            self.test_save_texture()
        elif event.key() == Qt.Key.Key_C:
            self.test_clear()
        elif event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)


def main():
    print("Starting simple OpenGL grid widget test...")

    app = QApplication(sys.argv)
    app.setApplicationName("Simple OpenGL Test")

    # Create and show the test window
    window = SimpleOpenGLTest()
    window.show()

    print("=" * 50)
    print("SIMPLE OPENGL GRID WIDGET TEST")
    print("=" * 50)
    print("Tests:")
    print("  1. Simple Text - puts text in the grid")
    print("  2. Green Screen - tests basic OpenGL")
    print("  3. Save Texture - saves texture image to PNG")
    print()
    print("Keyboard shortcuts:")
    print("  1 - Simple Text test")
    print("  2 - Green Screen test")
    print("  3 - Save Texture test")
    print("  C - Clear screen")
    print("  ESC - Exit")
    print("=" * 50)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()