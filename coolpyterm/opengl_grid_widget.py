"""
OpenGL Grid Widget - Drop-in replacement for your existing grid widget
Maintains exact same API but with OpenGL CRT effects - FIXED SHADER VERSION
"""
import os
import sys
import time
import math
import numpy as np
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer, Qt, QRect
from PyQt6.QtGui import QFont, QFontMetrics, QColor, QPainter, QImage
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtOpenGL import (QOpenGLShader, QOpenGLShaderProgram, QOpenGLTexture,
                           QOpenGLVertexArrayObject, QOpenGLBuffer)

try:
    from OpenGL.GL import *
    OPENGL_AVAILABLE = True
except ImportError:
    print("PyOpenGL not available. Install with: pip install PyOpenGL PyOpenGL_accelerate")
    OPENGL_AVAILABLE = False


class OpenGLRetroGridWidget(QOpenGLWidget):
    """
    Drop-in replacement for your HardwareAcceleratedGridWidget
    Maintains EXACT same API but with true OpenGL CRT effects
    """

    def __init__(self, parent=None, font_size=12, theme_manager=None):
        super().__init__(parent)

        # Theme management - EXACTLY like your original
        self.theme_manager = theme_manager
        if self.theme_manager:
            self.current_theme = self.theme_manager.get_current_theme()
        else:
            # Fallback theme
            from types import SimpleNamespace
            self.current_theme = SimpleNamespace(
                foreground=QColor(0, 255, 0),
                background=QColor(0, 0, 0),
                cursor=QColor(0, 255, 0)
            )

        # Font setup - EXACTLY like your original
        self.font = QFont("Consolas", font_size)
        self.font.setFixedPitch(True)
        self.font.setStyleHint(QFont.StyleHint.Monospace)

        # Calculate character dimensions - EXACTLY like your original
        self.font_metrics = QFontMetrics(self.font)
        self.char_width = self.font_metrics.horizontalAdvance('M')
        self.char_height = self.font_metrics.height()

        # Grid dimensions - EXACTLY like your original
        self.cols = 80
        self.rows = 24

        # Character grid - EXACTLY like your original
        self.grid = []
        self.init_grid()

        # Cursor position - EXACTLY like your original
        self.cursor_row = 0
        self.cursor_col = 0
        self.cursor_visible = True

        # Effect settings - make scanlines and flicker more visible
        self.glow_enabled = True
        self.cursor_blink_enabled = True
        self.glow_intensity = 0.6
        self.scanlines_enabled = True
        self.scanline_intensity = 0.25  # Increased for visibility
        self.flicker_enabled = True
        self.flicker_intensity = 0.08  # Increased for visibility
        self.curvature = 0.08
        self.brightness = 1.1
        self.contrast = 1.05

        # NEW: Ambient background glow setting
        self.ambient_glow = 0.12  # Subtle ambient glow by default

        # Animation state
        self.start_time = time.time()

        # OpenGL objects
        self.shader_program = None
        self.text_texture = None
        self.vao = None
        self.vertex_buffer = None
        self.index_buffer = None
        self.text_image = None

        # Enable focus and key events - EXACTLY like your original
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumSize(self.char_width * 80, self.char_height * 24)

        # Cursor blink timer - EXACTLY like your original
        self.cursor_timer = QTimer()
        self.cursor_timer.timeout.connect(self.toggle_cursor_visibility)
        self.cursor_timer.start(500)
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update)
        self.animation_timer.start(16)

    def toggle_cursor_visibility(self):
        """Toggle cursor visibility for blinking effect"""
        if self.cursor_blink_enabled:
            self.cursor_visible = not self.cursor_visible
            self.update()

    def init_grid(self):
        """Initialize the character grid - EXACTLY like your original"""
        self.grid = []
        for row in range(self.rows):
            grid_row = []
            for col in range(self.cols):
                cell = {
                    'char': ' ',
                    'fg_color': self.current_theme.foreground,
                    'bg_color': self.current_theme.background,
                    'bold': False,
                    'underline': False
                }
                grid_row.append(cell)
            self.grid.append(grid_row)

    def set_theme(self, theme_name):
        """Change the current theme - EXACTLY like your original"""
        if self.theme_manager and hasattr(self.theme_manager, 'set_current_theme'):
            self.theme_manager.set_current_theme(theme_name)
            self.current_theme = self.theme_manager.get_current_theme()
            self.init_grid()
            self.update()

    def resize_grid(self, new_cols, new_rows):
        """Resize the grid - EXACTLY like your original"""
        old_grid = self.grid
        old_rows = len(old_grid)
        old_cols = len(old_grid[0]) if old_rows > 0 else 0

        # Create new grid
        self.cols = new_cols
        self.rows = new_rows
        self.init_grid()

        # Copy old content to new grid
        copy_rows = min(old_rows, new_rows)
        copy_cols = min(old_cols, new_cols)

        for row in range(copy_rows):
            for col in range(copy_cols):
                self.grid[row][col] = old_grid[row][col]

        # Recreate OpenGL texture with new size
        if self.text_texture:
            self.create_text_texture()

        print(f"Grid resized to: {self.cols}x{self.rows}")

    def set_char(self, row, col, char, fg_color=None, bg_color=None, bold=False, underline=False):
        """Set a character - EXACTLY like your original"""
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.grid[row][col] = {
                'char': char,
                'fg_color': fg_color or self.current_theme.foreground,
                'bg_color': bg_color or self.current_theme.background,
                'bold': bold,
                'underline': underline
            }
            self.update()

    def get_char(self, row, col):
        """Get the character data - EXACTLY like your original"""
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.grid[row][col]
        return None

    def set_cursor_position(self, row, col):
        """Set the cursor position - EXACTLY like your original"""
        self.cursor_row = max(0, min(row, self.rows - 1))
        self.cursor_col = max(0, min(col, self.cols - 1))
        self.update()

    def toggle_cursor(self):
        """Toggle cursor visibility - EXACTLY like your original"""
        self.cursor_visible = not self.cursor_visible
        cursor_rect = QRect(
            self.cursor_col * self.char_width,
            self.cursor_row * self.char_height,
            self.char_width,
            self.char_height
        )
        self.update(cursor_rect)

    def clear_screen(self):
        """Clear the entire screen - EXACTLY like your original"""
        self.init_grid()
        self.cursor_row = 0
        self.cursor_col = 0
        self.update()

    def scroll_up(self, lines=1):
        """Scroll the content up - EXACTLY like your original"""
        for _ in range(lines):
            self.grid.pop(0)
            new_row = []
            for col in range(self.cols):
                cell = {
                    'char': ' ',
                    'fg_color': self.current_theme.foreground,
                    'bg_color': self.current_theme.background,
                    'bold': False,
                    'underline': False
                }
                new_row.append(cell)
            self.grid.append(new_row)
        self.update()

    def resizeEvent(self, event):
        """Handle widget resize events - EXACTLY like your original"""
        # Call QOpenGLWidget's resize event first
        QOpenGLWidget.resizeEvent(self, event)

        new_cols = max(1, self.width() // self.char_width)
        new_rows = max(1, self.height() // self.char_height)

        if new_cols != self.cols or new_rows != self.rows:
            self.resize_grid(new_cols, new_rows)

    # OpenGL-specific methods start here

    def initializeGL(self):
        """Initialize OpenGL"""
        if not OPENGL_AVAILABLE:
            print("OpenGL not available!")
            return

        # Enable blending for glow effects
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Create shader program
        self.create_shaders()

        # Create vertex data for fullscreen quad
        self.create_geometry()

        # Create texture for character rendering
        self.create_text_texture()

        print("OpenGL retro grid initialized")

    def create_shaders(self):
        """Create OpenGL shaders - WITH AMBIENT BACKGROUND GLOW"""
        vertex_shader_source = """
        #version 330 core
        layout (location = 0) in vec3 aPos;
        layout (location = 1) in vec2 aTexCoord;
        
        out vec2 TexCoord;
        out vec2 screenPos;
        
        void main()
        {
            gl_Position = vec4(aPos, 1.0);
            TexCoord = aTexCoord;
            screenPos = aPos.xy;
        }
        """

        # UPDATED fragment shader with ambient glow
        fragment_shader_source = """
        #version 330 core
        out vec4 FragColor;
        
        in vec2 TexCoord;
        in vec2 screenPos;
        
        uniform sampler2D textTexture;
        uniform float time;
        uniform float glowIntensity;
        uniform float scanlineIntensity;
        uniform float flickerIntensity;
        uniform float ambientGlow;
        uniform float curvature;
        uniform float brightness;
        uniform float contrast;
        uniform vec3 bgColor;
        uniform vec3 fgColor;
        uniform vec3 glowColor;
        uniform vec2 screenSize;
        
        void main()
        {
            // Apply barrel distortion for CRT curvature
            vec2 cc = TexCoord - 0.5;
            float dist = dot(cc, cc);
            vec2 distortedCoord = TexCoord + cc * (dist * curvature);
            
            // Check if we're outside the curved screen area
            if (distortedCoord.x < 0.0 || distortedCoord.x > 1.0 || 
                distortedCoord.y < 0.0 || distortedCoord.y > 1.0) {
                FragColor = vec4(bgColor, 1.0);
                return;
            }
            
            // Sample the text texture
            vec4 textColor = texture(textTexture, distortedCoord);
            
            // Convert to grayscale intensity
            float intensity = dot(textColor.rgb, vec3(0.299, 0.587, 0.114));
            
            // Apply theme colors with AMBIENT GLOW added to background
            vec3 ambientColor = bgColor + (fgColor * ambientGlow);
            vec3 color = mix(ambientColor, fgColor, intensity);
            
            // Apply phosphor glow - inline calculation
            if (intensity > 0.1 && glowIntensity > 0.0) {
                float glowAmount = glowIntensity * 0.3;
                vec3 glow = color * glowAmount;
                float bloom = smoothstep(0.0, 1.0, intensity) * 0.2;
                glow += vec3(bloom) * color;
                color = color + glow;
            }
            
            // Apply scanlines - inline calculation, guaranteed to work
            if (scanlineIntensity > 0.0) {
                float pixelY = distortedCoord.y * screenSize.y;
                float scanlinePattern = mod(pixelY, 2.0);
                if (scanlinePattern >= 1.0) {
                    color *= (1.0 - scanlineIntensity);
                }
            }
            
            // Apply screen flicker - inline calculation
            if (flickerIntensity > 0.0) {
                float slowFlicker = sin(time * 1.5) * 0.4;
                float mediumFlicker = sin(time * 3.7) * 0.3;
                float fastFlicker = sin(time * 12.1) * 0.3;
                float combined = (slowFlicker + mediumFlicker + fastFlicker) / 3.0;
                float flickerAmount = flickerIntensity * combined * 0.1;
                float flickerFactor = 1.0 + flickerAmount;
                color *= flickerFactor;
            }
            
            // Apply brightness and contrast
            color = ((color - 0.5) * contrast + 0.5) * brightness;
            
            // Vignette effect
            vec2 vignetteCoord = screenPos;
            float vignette = 1.0 - dot(vignetteCoord, vignetteCoord) * 0.2;
            color *= vignette;
            
            FragColor = vec4(color, 1.0);
        }
        """

        # Create shader program
        self.shader_program = QOpenGLShaderProgram()

        if not self.shader_program.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Vertex, vertex_shader_source):
            print("Vertex shader compilation failed:", self.shader_program.log())
            return

        if not self.shader_program.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Fragment, fragment_shader_source):
            print("Fragment shader compilation failed:", self.shader_program.log())
            return

        if not self.shader_program.link():
            print("Shader program linking failed:", self.shader_program.log())
            return

        print("Shaders compiled successfully")

    def create_geometry(self):
        """Create fullscreen quad geometry"""
        vertices = np.array([
            # positions     # texture coords
            -1.0, -1.0, 0.0,  0.0, 1.0,  # Bottom-left
             1.0, -1.0, 0.0,  1.0, 1.0,  # Bottom-right
             1.0,  1.0, 0.0,  1.0, 0.0,  # Top-right
            -1.0,  1.0, 0.0,  0.0, 0.0   # Top-left
        ], dtype=np.float32)

        indices = np.array([
            0, 1, 2,
            2, 3, 0
        ], dtype=np.uint32)

        # Create VAO
        self.vao = QOpenGLVertexArrayObject()
        if not self.vao.create():
            print("Failed to create VAO")
            return
        self.vao.bind()

        # Create vertex buffer
        self.vertex_buffer = QOpenGLBuffer(QOpenGLBuffer.Type.VertexBuffer)
        if not self.vertex_buffer.create():
            print("Failed to create vertex buffer")
            return
        self.vertex_buffer.bind()
        self.vertex_buffer.allocate(vertices.tobytes(), vertices.nbytes)

        # Create index buffer
        self.index_buffer = QOpenGLBuffer(QOpenGLBuffer.Type.IndexBuffer)
        if not self.index_buffer.create():
            print("Failed to create index buffer")
            return
        self.index_buffer.bind()
        self.index_buffer.allocate(indices.tobytes(), indices.nbytes)

        # Set vertex attributes
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 5 * 4, None)
        glEnableVertexAttribArray(0)

        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5 * 4, ctypes.c_void_p(3 * 4))
        glEnableVertexAttribArray(1)

        self.vao.release()

    def create_text_texture(self):
        """Create texture for text rendering"""
        # Calculate texture size based on grid
        texture_width = self.cols * self.char_width
        texture_height = self.rows * self.char_height

        # Create QImage for text rendering
        self.text_image = QImage(texture_width, texture_height, QImage.Format.Format_RGB888)
        self.text_image.fill(QColor(0, 0, 0))

        # Create OpenGL texture
        self.text_texture = QOpenGLTexture(QOpenGLTexture.Target.Target2D)
        if not self.text_texture.create():
            print("Failed to create texture")
            return

        self.text_texture.setSize(texture_width, texture_height)
        self.text_texture.setFormat(QOpenGLTexture.TextureFormat.RGB8_UNorm)
        self.text_texture.allocateStorage()

        # Set texture parameters
        self.text_texture.setWrapMode(QOpenGLTexture.CoordinateDirection.DirectionS,
                                     QOpenGLTexture.WrapMode.ClampToEdge)
        self.text_texture.setWrapMode(QOpenGLTexture.CoordinateDirection.DirectionT,
                                     QOpenGLTexture.WrapMode.ClampToEdge)
        self.text_texture.setMinMagFilters(QOpenGLTexture.Filter.Linear,
                                          QOpenGLTexture.Filter.Linear)

        # Upload initial data
        self.update_text_texture()

    def render_grid_to_texture(self):
        """Render character grid to texture with enhanced quality"""
        if not self.text_image:
            return

        # Clear the image
        self.text_image.fill(QColor(0, 0, 0))

        # Create painter for text rendering
        painter = QPainter(self.text_image)
        painter.setFont(self.font)

        # Enable high-quality text rendering
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Render each character from the grid
        for row in range(self.rows):
            for col in range(self.cols):
                cell = self.grid[row][col]
                char = cell['char']

                if char != ' ':
                    # Set text color (white for texture, theme applied in shader)
                    painter.setPen(QColor(255, 255, 255))

                    # Apply bold if needed
                    font = QFont(self.font)
                    if cell['bold']:
                        font.setBold(True)
                    painter.setFont(font)

                    # Calculate position
                    x = col * self.char_width
                    y = (row + 1) * self.char_height - self.font_metrics.descent()

                    # Draw character
                    painter.drawText(x, y, char)

                    # Draw underline if needed
                    if cell['underline']:
                        underline_y = (row + 1) * self.char_height - 2
                        painter.drawLine(x, underline_y, x + self.char_width, underline_y)

                # Render cursor
                if (row == self.cursor_row and col == self.cursor_col and self.cursor_visible):
                    cursor_rect = QRect(col * self.char_width, row * self.char_height,
                                      self.char_width, self.char_height)
                    painter.fillRect(cursor_rect, QColor(128, 128, 128))

        painter.end()

    def update_text_texture(self):
        """Update OpenGL texture with current grid"""
        if not self.text_texture:
            return

        # Render grid to image
        self.render_grid_to_texture()

        # Convert to OpenGL format
        gl_image = self.text_image.convertToFormat(QImage.Format.Format_RGB888)

        # Upload to texture
        self.text_texture.bind()
        self.text_texture.setData(QOpenGLTexture.PixelFormat.RGB,
                                 QOpenGLTexture.PixelType.UInt8,
                                 gl_image.constBits())

    def paintGL(self):
        """Render with OpenGL"""
        if not OPENGL_AVAILABLE or not self.shader_program:
            return

        # Get theme colors
        bg_rgb = [0, 0, 0]
        fg_rgb = [0, 1, 0]  # Default green
        if self.current_theme:
            bg = self.current_theme.background
            fg = self.current_theme.foreground
            bg_rgb = [bg.redF(), bg.greenF(), bg.blueF()]
            fg_rgb = [fg.redF(), fg.greenF(), fg.blueF()]

        # Clear screen
        glClearColor(bg_rgb[0], bg_rgb[1], bg_rgb[2], 1.0)
        glClear(GL_COLOR_BUFFER_BIT)

        # Update texture with current grid
        self.update_text_texture()

        # Use shader program
        if not self.shader_program.bind():
            return

        # Set uniforms with debugging
        current_time = time.time() - self.start_time

        # Calculate actual values to send to shader
        actual_glow = self.glow_intensity if self.glow_enabled else 0.0
        actual_scanlines = self.scanline_intensity if self.scanlines_enabled else 0.0
        # actual_flicker = self.flicker_intensity if self.flicker_enabled else 0.0

        # Debug print occasionally
        # if int(current_time) % 5 == 0 and int(current_time * 10) % 10 == 0:  # Every 5 seconds
        #     print(f"Shader uniforms - Glow: {actual_glow}, Scanlines: {actual_scanlines}, Flicker: {actual_flicker}, Ambient: {self.ambient_glow}")

        self.shader_program.setUniformValue("time", current_time)
        self.shader_program.setUniformValue("glowIntensity", actual_glow)
        self.shader_program.setUniformValue("scanlineIntensity", actual_scanlines)
        self.shader_program.setUniformValue("ambientGlow", self.ambient_glow)  # NEW: Ambient glow uniform
        self.shader_program.setUniformValue("curvature", self.curvature)
        self.shader_program.setUniformValue("brightness", self.brightness)
        self.shader_program.setUniformValue("contrast", self.contrast)
        self.shader_program.setUniformValue("bgColor", bg_rgb[0], bg_rgb[1], bg_rgb[2])
        self.shader_program.setUniformValue("fgColor", fg_rgb[0], fg_rgb[1], fg_rgb[2])
        self.shader_program.setUniformValue("glowColor", fg_rgb[0], fg_rgb[1], fg_rgb[2])
        self.shader_program.setUniformValue("screenSize", float(self.width()), float(self.height()))

        # Bind texture
        if self.text_texture:
            self.text_texture.bind(0)
            self.shader_program.setUniformValue("textTexture", 0)

        # Draw quad
        if self.vao:
            self.vao.bind()
            glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
            self.vao.release()

        # Release resources
        if self.text_texture:
            self.text_texture.release()
        self.shader_program.release()

    def resizeGL(self, width, height):
        """Handle OpenGL resize"""
        glViewport(0, 0, width, height)

    # Effect toggle methods
    def toggle_glow(self):
        """Toggle glow effect"""
        self.glow_enabled = not self.glow_enabled
        print(f"Glow: {'ON' if self.glow_enabled else 'OFF'} (intensity: {self.glow_intensity})")
        self.update()

    def toggle_scanlines(self):
        """Toggle scanlines effect"""
        self.scanlines_enabled = not self.scanlines_enabled
        print(f"Scanlines: {'ON' if self.scanlines_enabled else 'OFF'} (intensity: {self.scanline_intensity})")
        self.update()

    def toggle_flicker(self):
        """Toggle flicker effect"""
        self.flicker_enabled = not self.flicker_enabled
        print(f"Flicker: {'ON' if self.flicker_enabled else 'OFF'} (intensity: {self.flicker_intensity})")
        self.update()

    # NEW: Ambient glow controls
    def toggle_ambient_glow(self):
        """Toggle ambient background glow"""
        self.ambient_glow = 0.0 if self.ambient_glow > 0.0 else 0.15
        print(f"Ambient glow: {'ON' if self.ambient_glow > 0.0 else 'OFF'} (intensity: {self.ambient_glow})")
        self.update()

    def set_ambient_glow(self, intensity):
        """Set ambient glow intensity (0.0 to 1.0)"""
        self.ambient_glow = max(0.0, min(1.0, intensity))
        print(f"Ambient glow intensity: {self.ambient_glow}")
        self.update()

    def test_ambient_glow(self):
        """Test ambient glow at high intensity"""
        self.ambient_glow = 0.3
        print(f"Testing ambient glow at high intensity: {self.ambient_glow}")
        print("The entire background should now have a subtle color tint!")
        self.update()

    # MISSING CURSOR CONTROL METHODS
    def enable_cursor_blink(self, enabled=True):
        """Enable or disable cursor blinking"""
        self.cursor_blink_enabled = enabled

        if enabled:
            # Enable blinking
            if not self.cursor_timer.isActive():
                self.cursor_timer.start(500)
            print("Cursor blinking enabled")
        else:
            # Disable blinking - cursor always visible
            self.cursor_visible = True
            if self.cursor_timer.isActive():
                self.cursor_timer.stop()
            print("Cursor blinking disabled - cursor always visible")

        self.update()

    def set_cursor_blink_rate(self, milliseconds):
        """Set cursor blink rate in milliseconds"""
        if self.cursor_timer:
            self.cursor_timer.stop()
            self.cursor_timer.start(milliseconds)
            print(f"Cursor blink rate set to {milliseconds}ms")

    def toggle_cursor_blinking(self):
        """Toggle cursor blinking on/off"""
        self.enable_cursor_blink(not self.cursor_blink_enabled)

    # MISSING BACKGROUND GLOW METHOD (for backward compatibility)
    def toggle_background_glow(self):
        """Toggle background glow (alias for toggle_ambient_glow for compatibility)"""
        self.toggle_ambient_glow()

    def increase_scanlines(self):
        """Increase scanline intensity for testing"""
        self.scanline_intensity = min(1.0, self.scanline_intensity + 0.1)
        print(f"Scanlines intensity: {self.scanline_intensity}")
        self.update()

    def increase_flicker(self):
        """Increase flicker intensity for testing"""
        self.flicker_intensity = min(1.0, self.flicker_intensity + 0.05)
        print(f"Flicker intensity: {self.flicker_intensity}")
        self.update()

    # Add these methods to your OpenGLRetroGridWidget class in opengl_grid_widget.py
    # Place them after the existing effect toggle methods

    def adjust_scanlines_for_dpi(self):
        """Auto-adjust scanlines intensity based on screen DPI and widget size"""
        try:
            # Get screen DPI information
            from PyQt6.QtGui import QGuiApplication
            screen = QGuiApplication.primaryScreen()

            if not screen:
                print("Could not get screen information for DPI adjustment")
                return 0.25

            # Get DPI values
            logical_dpi = screen.logicalDotsPerInch()
            physical_dpi = screen.physicalDotsPerInch()
            device_pixel_ratio = screen.devicePixelRatio()

            print(
                f"Screen info - Logical DPI: {logical_dpi}, Physical DPI: {physical_dpi}, Pixel Ratio: {device_pixel_ratio}")

            # Calculate optimal scanline intensity based on DPI and widget size
            widget_height = self.height()
            char_height_pixels = self.char_height

            # Higher DPI screens need more subtle scanlines
            # Lower resolution screens need more pronounced scanlines
            base_intensity = 0.25  # Default intensity

            if logical_dpi >= 150:  # High DPI screen
                # Reduce intensity for high DPI screens
                dpi_factor = min(logical_dpi / 96.0, 3.0)  # Cap at 3x
                adjusted_intensity = base_intensity / (dpi_factor * 0.5)
            elif logical_dpi <= 96:  # Standard or low DPI
                # Increase intensity for lower DPI screens
                adjusted_intensity = base_intensity * 1.2
            else:
                # Medium DPI - use base intensity
                adjusted_intensity = base_intensity

            # Factor in character height - smaller characters need less intense scanlines
            if char_height_pixels < 16:
                adjusted_intensity *= 0.8
            elif char_height_pixels > 20:
                adjusted_intensity *= 1.2

            # Factor in widget height - taller widgets can handle more scanlines
            if widget_height > 800:
                adjusted_intensity *= 1.1
            elif widget_height < 400:
                adjusted_intensity *= 0.9

            # Clamp to reasonable range
            adjusted_intensity = max(0.05, min(0.6, adjusted_intensity))

            # Apply the new scanline intensity
            self.scanline_intensity = adjusted_intensity
            self.scanlines_enabled = True  # Enable scanlines when auto-adjusting

            print(f"Auto-adjusted scanlines:")
            print(f"  - Widget size: {self.width()}x{widget_height}")
            print(f"  - Character height: {char_height_pixels}px")
            print(f"  - DPI: {logical_dpi}")
            print(f"  - New scanline intensity: {adjusted_intensity:.3f}")

            # Force an update to show the changes
            self.update()

            return adjusted_intensity

        except Exception as e:
            print(f"Error in adjust_scanlines_for_dpi: {e}")
            # Fallback to a safe default
            self.scanline_intensity = 0.25
            self.scanlines_enabled = True
            self.update()
            return 0.25

    def get_optimal_scanline_intensity(self):
        """Get the optimal scanline intensity for current display without applying it"""
        try:
            from PyQt6.QtGui import QGuiApplication
            screen = QGuiApplication.primaryScreen()

            if not screen:
                return 0.25

            logical_dpi = screen.logicalDotsPerInch()

            # Same calculation as adjust_scanlines_for_dpi but return value only
            base_intensity = 0.25

            if logical_dpi >= 150:
                dpi_factor = min(logical_dpi / 96.0, 3.0)
                adjusted_intensity = base_intensity / (dpi_factor * 0.5)
            elif logical_dpi <= 96:
                adjusted_intensity = base_intensity * 1.2
            else:
                adjusted_intensity = base_intensity

            if self.char_height < 16:
                adjusted_intensity *= 0.8
            elif self.char_height > 20:
                adjusted_intensity *= 1.2

            if self.height() > 800:
                adjusted_intensity *= 1.1
            elif self.height() < 400:
                adjusted_intensity *= 0.9

            return max(0.05, min(0.6, adjusted_intensity))

        except Exception:
            return 0.25

    def reset_scanlines_to_default(self):
        """Reset scanlines to theme-appropriate defaults"""
        # Get theme-specific defaults if available
        if self.theme_manager and hasattr(self.theme_manager, 'get_current_theme'):
            theme = self.theme_manager.get_current_theme()
            if hasattr(theme, 'scanline_intensity'):
                self.scanline_intensity = theme.scanline_intensity
            else:
                self.scanline_intensity = 0.25  # Default
        else:
            self.scanline_intensity = 0.25

        self.scanlines_enabled = True
        print(f"Reset scanlines to default intensity: {self.scanline_intensity}")
        self.update()

    def set_scanline_intensity(self, intensity):
        """Manually set scanline intensity with validation"""
        old_intensity = self.scanline_intensity
        self.scanline_intensity = max(0.0, min(1.0, intensity))

        if abs(self.scanline_intensity - old_intensity) > 0.001:  # Only update if changed
            print(f"Scanline intensity changed: {old_intensity:.3f} -> {self.scanline_intensity:.3f}")
            self.update()

        return self.scanline_intensity

    def set_crt_controls(self, brightness=None, contrast=None, curvature=None):
        """Set CRT control values"""
        if brightness is not None:
            self.brightness = max(0.5, min(2.0, brightness))
            print(f"Brightness set to: {self.brightness}")

        if contrast is not None:
            self.contrast = max(0.5, min(2.0, contrast))
            print(f"Contrast set to: {self.contrast}")

        if curvature is not None:
            self.curvature = max(0.0, min(0.2, curvature))
            print(f"Curvature set to: {self.curvature}")

        self.update()

    # Add these methods to your OpenGLRetroGridWidget class in opengl_grid_widget.py

    def increase_ambient_glow(self, step=0.05):
        """Increase ambient glow intensity"""
        old_value = self.ambient_glow
        self.ambient_glow = min(1.0, self.ambient_glow + step)

        if abs(self.ambient_glow - old_value) > 0.001:
            print(f"Ambient glow increased: {old_value:.3f} -> {self.ambient_glow:.3f}")
            self.update()
            return True
        else:
            print(f"Ambient glow already at maximum: {self.ambient_glow:.3f}")
            return False

    def decrease_ambient_glow(self, step=0.05):
        """Decrease ambient glow intensity"""
        old_value = self.ambient_glow
        self.ambient_glow = max(0.0, self.ambient_glow - step)

        if abs(self.ambient_glow - old_value) > 0.001:
            print(f"Ambient glow decreased: {old_value:.3f} -> {self.ambient_glow:.3f}")
            self.update()
            return True
        else:
            print(f"Ambient glow already at minimum: {self.ambient_glow:.3f}")
            return False

    def get_ambient_glow_level(self):
        """Get current ambient glow level as percentage"""
        return int(self.ambient_glow * 100)

    def set_ambient_glow_percentage(self, percentage):
        """Set ambient glow as percentage (0-100)"""
        old_value = self.ambient_glow
        self.ambient_glow = max(0.0, min(1.0, percentage / 100.0))

        if abs(self.ambient_glow - old_value) > 0.001:
            print(f"Ambient glow set to {percentage}%: {old_value:.3f} -> {self.ambient_glow:.3f}")
            self.update()
            return True
        return False

    def reset_ambient_glow_to_theme_default(self):
        """Reset ambient glow to theme-specific default"""
        if self.theme_manager and hasattr(self.theme_manager, 'get_current_theme'):
            theme = self.theme_manager.get_current_theme()

            # Get theme-specific defaults or use sensible defaults per theme
            if hasattr(theme, 'ambient_glow'):
                default_glow = theme.ambient_glow
            else:
                # Theme-specific defaults based on theme name
                theme_name = getattr(theme, 'name', '').lower()
                if 'green' in theme_name:
                    default_glow = 0.15  # Green phosphor - moderate glow
                elif 'amber' in theme_name:
                    default_glow = 0.20  # Amber - warmer, more glow
                elif 'dos' in theme_name or 'blue' in theme_name:
                    default_glow = 0.10  # DOS blue - subtle glow
                else:
                    default_glow = 0.15  # Default
        else:
            default_glow = 0.15

        old_value = self.ambient_glow
        self.ambient_glow = default_glow

        print(f"Reset ambient glow to theme default: {old_value:.3f} -> {self.ambient_glow:.3f}")
        self.update()

    def print_ambient_glow_status(self):
        """Print current ambient glow status"""
        percentage = int(self.ambient_glow * 100)
        print(f"Ambient Glow: {self.ambient_glow:.3f} ({percentage}%)")

        if self.ambient_glow == 0.0:
            print("  Status: OFF")
        elif self.ambient_glow < 0.1:
            print("  Status: Very Subtle")
        elif self.ambient_glow < 0.2:
            print("  Status: Moderate")
        elif self.ambient_glow < 0.3:
            print("  Status: Strong")
        else:
            print("  Status: Very Strong")

    # Add these preset methods for quick adjustment
    def set_ambient_glow_subtle(self):
        """Set ambient glow to subtle level"""
        self.ambient_glow = 0.08
        print("Ambient glow set to SUBTLE (8%)")
        self.update()

    def set_ambient_glow_moderate(self):
        """Set ambient glow to moderate level"""
        self.ambient_glow = 0.15
        print("Ambient glow set to MODERATE (15%)")
        self.update()

    def set_ambient_glow_strong(self):
        """Set ambient glow to strong level"""
        self.ambient_glow = 0.25
        print("Ambient glow set to STRONG (25%)")
        self.update()

    def set_ambient_glow_maximum(self):
        """Set ambient glow to maximum level"""
        self.ambient_glow = 0.40
        print("Ambient glow set to MAXIMUM (40%)")
        self.update()

    def force_scanlines_visible(self):
        """Force scanlines to be highly visible for testing"""
        print("Forcing scanlines to maximum visibility...")
        self.scanlines_enabled = True
        self.scanline_intensity = 0.8  # Very high
        print(f"Scanlines enabled: {self.scanlines_enabled}, intensity: {self.scanline_intensity}")
        self.update()

    def force_flicker_visible(self):
        """Force flicker to be highly visible for testing"""
        print("Forcing flicker to maximum visibility...")
        self.flicker_enabled = True
        self.flicker_intensity = 0.3  # Very high
        print(f"Flicker enabled: {self.flicker_enabled}, intensity: {self.flicker_intensity}")
        self.update()

    def print_current_effects(self):
        """Print current effect status"""
        print("=== Current Effect Status ===")
        print(f"Glow: {'ON' if self.glow_enabled else 'OFF'} (intensity: {self.glow_intensity})")
        print(f"Scanlines: {'ON' if self.scanlines_enabled else 'OFF'} (intensity: {self.scanline_intensity})")
        print(f"Flicker: {'ON' if self.flicker_enabled else 'OFF'} (intensity: {self.flicker_intensity})")
        print(f"Ambient Glow: {self.ambient_glow}")  # NEW: Show ambient glow status
        print(f"Curvature: {self.curvature}")
        print("==============================")

    def keyPressEvent(self, event):
        """Forward keyboard events to parent terminal"""
        if self.parent():
            self.parent().keyPressEvent(event)
        else:
            super().keyPressEvent(event)