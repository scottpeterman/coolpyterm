from PyQt6.QtGui import QColor
from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class TerminalTheme:
    """Clean theme class with only CRT-specific properties"""
    name: str
    foreground: QColor
    background: QColor

    # ANSI colors
    black: QColor
    red: QColor
    green: QColor
    yellow: QColor
    blue: QColor
    magenta: QColor
    cyan: QColor
    white: QColor

    # Bright ANSI colors
    bright_black: QColor
    bright_red: QColor
    bright_green: QColor
    bright_yellow: QColor
    bright_blue: QColor
    bright_magenta: QColor
    bright_cyan: QColor
    bright_white: QColor

    # CRT-specific properties
    background_glow_intensity: float = 0.15
    brightness: float = 1.2
    contrast: float = 1.3
    phosphor_persistence: float = 0.8
    bloom_radius: float = 1.8

    # Theme metadata
    description: str = ""
    extra_properties: Dict[str, Any] = field(default_factory=dict)


class RetroThemeManager:
    """Clean theme manager with only new CRT functionality"""

    def __init__(self):
        self.themes: Dict[str, TerminalTheme] = {}
        self.current_theme: str = "green"
        self._create_builtin_themes()

    def _create_builtin_themes(self):
        """Create the three classic themes with CRT properties"""

        # GREEN PHOSPHOR THEME
        self.themes["green"] = TerminalTheme(
            name="Green Phosphor",
            foreground=QColor(0, 255, 0),
            background=QColor(0, 0, 0),

            # ANSI colors - green variations
            black=QColor(0, 0, 0),
            red=QColor(0, 205, 0),
            green=QColor(0, 255, 0),
            yellow=QColor(0, 255, 85),
            blue=QColor(0, 205, 0),
            magenta=QColor(0, 255, 85),
            cyan=QColor(0, 255, 170),
            white=QColor(0, 255, 0),

            bright_black=QColor(0, 85, 0),
            bright_red=QColor(85, 255, 85),
            bright_green=QColor(85, 255, 85),
            bright_yellow=QColor(170, 255, 170),
            bright_blue=QColor(85, 255, 85),
            bright_magenta=QColor(170, 255, 170),
            bright_cyan=QColor(170, 255, 170),
            bright_white=QColor(170, 255, 170),

            # CRT properties for green phosphor
            background_glow_intensity=0.12,
            brightness=1.1,
            contrast=1.4,
            phosphor_persistence=0.9,
            bloom_radius=1.8,

            description="Classic green phosphor CRT terminal"
        )

        # AMBER PHOSPHOR THEME
        self.themes["amber"] = TerminalTheme(
            name="Amber Phosphor",
            foreground=QColor(255, 191, 0),
            background=QColor(0, 0, 0),

            # ANSI colors - amber/orange variations
            black=QColor(0, 0, 0),
            red=QColor(255, 127, 0),
            green=QColor(255, 191, 0),
            yellow=QColor(255, 255, 85),
            blue=QColor(191, 127, 0),
            magenta=QColor(255, 127, 85),
            cyan=QColor(255, 191, 85),
            white=QColor(255, 191, 0),

            bright_black=QColor(85, 42, 0),
            bright_red=QColor(255, 170, 85),
            bright_green=QColor(255, 212, 85),
            bright_yellow=QColor(255, 255, 170),
            bright_blue=QColor(212, 170, 85),
            bright_magenta=QColor(255, 191, 170),
            bright_cyan=QColor(255, 212, 170),
            bright_white=QColor(255, 212, 170),

            # CRT properties for amber phosphor - had more background glow
            background_glow_intensity=0.18,
            brightness=1.3,
            contrast=1.2,
            phosphor_persistence=0.7,
            bloom_radius=2.2,

            description="Warm amber phosphor CRT terminal"
        )

        # DOS TERMINAL THEME
        self.themes["dos"] = TerminalTheme(
            name="DOS Terminal",
            foreground=QColor(170, 170, 255),
            background=QColor(0, 0, 85),

            # ANSI colors - DOS-style palette
            black=QColor(0, 0, 0),
            red=QColor(170, 0, 0),
            green=QColor(0, 170, 0),
            yellow=QColor(170, 85, 0),
            blue=QColor(0, 0, 170),
            magenta=QColor(170, 0, 170),
            cyan=QColor(0, 170, 170),
            white=QColor(170, 170, 170),

            bright_black=QColor(85, 85, 85),
            bright_red=QColor(255, 85, 85),
            bright_green=QColor(85, 255, 85),
            bright_yellow=QColor(255, 255, 85),
            bright_blue=QColor(85, 85, 255),
            bright_magenta=QColor(255, 85, 255),
            bright_cyan=QColor(85, 255, 255),
            bright_white=QColor(255, 255, 255),

            # CRT properties for DOS-style blue monitor
            background_glow_intensity=0.10,
            brightness=1.0,
            contrast=1.5,
            phosphor_persistence=0.6,
            bloom_radius=1.5,

            description="Retro DOS-style blue terminal"
        )

        self.themes["ibm_bw"] = TerminalTheme(
            name="IBM DOS B&W",
            foreground=QColor(255, 255, 255),  # Bright white
            background=QColor(0, 0, 0),  # Pure black

            # ANSI colors - all grayscale variations for monochrome
            black=QColor(0, 0, 0),
            red=QColor(170, 170, 170),  # Light gray instead of red
            green=QColor(200, 200, 200),  # Lighter gray instead of green
            yellow=QColor(255, 255, 255),  # White instead of yellow
            blue=QColor(128, 128, 128),  # Medium gray instead of blue
            magenta=QColor(200, 200, 200),  # Light gray instead of magenta
            cyan=QColor(230, 230, 230),  # Very light gray instead of cyan
            white=QColor(255, 255, 255),  # Pure white

            bright_black=QColor(85, 85, 85),
            bright_red=QColor(200, 200, 200),
            bright_green=QColor(230, 230, 230),
            bright_yellow=QColor(255, 255, 255),
            bright_blue=QColor(170, 170, 170),
            bright_magenta=QColor(230, 230, 230),
            bright_cyan=QColor(245, 245, 245),
            bright_white=QColor(255, 255, 255),

            # CRT properties for sharp IBM monochrome monitor
            background_glow_intensity=0.05,  # Very minimal glow
            brightness=1.4,  # High brightness for crisp text
            contrast=1.8,  # Very high contrast
            phosphor_persistence=0.3,  # Quick decay for sharp text
            bloom_radius=0.8,  # Minimal bloom

            description="Sharp IBM DOS-style black and white monochrome"
        )

        # PLASMA RED THEME
        self.themes["plasma"] = TerminalTheme(
            name="Plasma Red",
            foreground=QColor(255, 85, 85),  # Bright red-orange
            background=QColor(0, 0, 0),  # Pure black

            # ANSI colors - red/orange variations for plasma look
            black=QColor(0, 0, 0),
            red=QColor(255, 100, 100),  # Bright red
            green=QColor(255, 140, 85),  # Orange-red (no true green on plasma)
            yellow=QColor(255, 200, 150),  # Yellowish-orange
            blue=QColor(200, 80, 80),  # Dark red (no true blue)
            magenta=QColor(255, 120, 180),  # Pink-red
            cyan=QColor(255, 160, 120),  # Light orange-red
            white=QColor(255, 200, 200),  # Light pink-white

            bright_black=QColor(80, 20, 20),  # Dark red-black
            bright_red=QColor(255, 120, 120),
            bright_green=QColor(255, 180, 120),
            bright_yellow=QColor(255, 220, 180),
            bright_blue=QColor(220, 100, 100),
            bright_magenta=QColor(255, 150, 200),
            bright_cyan=QColor(255, 200, 160),
            bright_white=QColor(255, 230, 230),

            # CRT properties for plasma display characteristics
            background_glow_intensity=0.22,  # Strong glow for plasma effect
            brightness=1.25,  # Moderate brightness
            contrast=1.1,  # Lower contrast for plasma warmth
            phosphor_persistence=1.2,  # Longer persistence for plasma glow
            bloom_radius=2.8,  # Strong bloom for plasma effect

            description="Red plasma display with warm glow"
        )

    def get_theme(self, theme_name: str) -> TerminalTheme:
        """Get a theme by name"""
        return self.themes.get(theme_name, self.themes["green"])

    def set_current_theme(self, theme_name: str):
        """Set the current active theme"""
        if theme_name in self.themes:
            self.current_theme = theme_name
            print(f"Theme changed to: {self.themes[theme_name].name}")
        else:
            print(f"Theme '{theme_name}' not found")

    def get_current_theme(self) -> TerminalTheme:
        """Get the currently active theme"""
        return self.themes[self.current_theme]

    def get_available_themes(self) -> list:
        """Get list of available theme names"""
        return list(self.themes.keys())

    def get_crt_properties(self, theme_name: str = None) -> Dict[str, float]:
        """Get CRT-specific properties for a theme"""
        if theme_name is None:
            theme_name = self.current_theme

        theme = self.themes.get(theme_name)
        if not theme:
            theme = self.get_current_theme()

        return {
            'background_glow_intensity': theme.background_glow_intensity,
            'brightness': theme.brightness,
            'contrast': theme.contrast,
            'phosphor_persistence': theme.phosphor_persistence,
            'bloom_radius': theme.bloom_radius
        }

    def map_pyte_color(self, pyte_color, theme: TerminalTheme = None) -> QColor:
        """Map pyte color to theme color"""
        if theme is None:
            theme = self.get_current_theme()

        # Color mapping dictionary
        color_map = {
            "black": theme.black,
            "red": theme.red,
            "green": theme.green,
            "yellow": theme.yellow,
            "blue": theme.blue,
            "magenta": theme.magenta,
            "cyan": theme.cyan,
            "white": theme.white,
            "bright_black": theme.bright_black,
            "bright_red": theme.bright_red,
            "bright_green": theme.bright_green,
            "bright_yellow": theme.bright_yellow,
            "bright_blue": theme.bright_blue,
            "bright_magenta": theme.bright_magenta,
            "bright_cyan": theme.bright_cyan,
            "bright_white": theme.bright_white,
        }

        # Handle different pyte color formats
        if isinstance(pyte_color, str):
            return color_map.get(pyte_color, theme.foreground)
        elif hasattr(pyte_color, 'name'):
            return color_map.get(pyte_color.name, theme.foreground)
        elif isinstance(pyte_color, int):
            if 0 <= pyte_color <= 15:
                color_names = list(color_map.keys())
                if pyte_color < len(color_names):
                    return color_map[color_names[pyte_color]]

        return theme.foreground

    def create_custom_theme(self, name: str, base_theme: str = "green", **overrides) -> bool:
        """Create custom theme with CRT properties"""
        if base_theme not in self.themes:
            print(f"Base theme '{base_theme}' not found")
            return False

        base = self.themes[base_theme]

        # Create new theme with all properties from base
        new_theme = TerminalTheme(
            name=name,
            foreground=overrides.get('foreground', base.foreground),
            background=overrides.get('background', base.background),

            # ANSI colors
            black=overrides.get('black', base.black),
            red=overrides.get('red', base.red),
            green=overrides.get('green', base.green),
            yellow=overrides.get('yellow', base.yellow),
            blue=overrides.get('blue', base.blue),
            magenta=overrides.get('magenta', base.magenta),
            cyan=overrides.get('cyan', base.cyan),
            white=overrides.get('white', base.white),

            bright_black=overrides.get('bright_black', base.bright_black),
            bright_red=overrides.get('bright_red', base.bright_red),
            bright_green=overrides.get('bright_green', base.bright_green),
            bright_yellow=overrides.get('bright_yellow', base.bright_yellow),
            bright_blue=overrides.get('bright_blue', base.bright_blue),
            bright_magenta=overrides.get('bright_magenta', base.bright_magenta),
            bright_cyan=overrides.get('bright_cyan', base.bright_cyan),
            bright_white=overrides.get('bright_white', base.bright_white),

            # CRT properties
            background_glow_intensity=overrides.get('background_glow_intensity', base.background_glow_intensity),
            brightness=overrides.get('brightness', base.brightness),
            contrast=overrides.get('contrast', base.contrast),
            phosphor_persistence=overrides.get('phosphor_persistence', base.phosphor_persistence),
            bloom_radius=overrides.get('bloom_radius', base.bloom_radius),

            description=overrides.get('description', f"Custom theme based on {base.name}")
        )

        self.themes[name] = new_theme
        print(f"Created custom theme: {name}")
        return True


# Example usage and testing
if __name__ == "__main__":
    theme_manager = RetroThemeManager()

    # Test all themes
    for theme_name in theme_manager.get_available_themes():
        theme = theme_manager.get_theme(theme_name)
        print(f"\n{theme.name} Theme:")
        print(f"  Background: {theme.background.name()}")
        print(f"  Foreground: {theme.foreground.name()}")
        print(f"  Background Glow: {theme.background_glow_intensity}")
        print(f"  Brightness: {theme.brightness}")
        print(f"  Contrast: {theme.contrast}")

    # Test color mapping
    print(f"\nColor mapping test:")
    theme_manager.set_current_theme("amber")
    print(f"Red in amber theme: {theme_manager.map_pyte_color('red').name()}")
    print(f"Green in amber theme: {theme_manager.map_pyte_color('green').name()}")

    # Test CRT properties
    print(f"\nCRT Properties test:")
    crt_props = theme_manager.get_crt_properties("green")
    print(f"Green theme CRT properties: {crt_props}")