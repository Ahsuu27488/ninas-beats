"""
SceneMatrixRain for Nina's Beats.

Tech/Cool scene with digital rain using hearts/flowers instead of numbers.
Green → Pink color transition over time.
"""
import random

from rich.color import Color

from .base import Scene, SceneContext
from ..colors import PINK, BLUE


class RainColumn:
    """A single column of falling characters in matrix rain."""

    def __init__(self, x: int, max_height: int):
        """Initialize rain column."""
        self.x = x
        self.max_height = max_height
        self.chars = []  # List of (char, brightness) tuples
        self.speed = random.uniform(3, 8)  # Falling speed
        self.spawn_timer = 0
        self.brightness = 1.0  # For color transition

    def update(self, dt: float, speed_multiplier: float = 1.0) -> None:
        """Update column state."""
        self.spawn_timer -= dt * self.speed * speed_multiplier

        # Spawn new character at top
        if self.spawn_timer <= 0:
            self.chars.append((random.choice(["♥", "✿", "❀", "❁"]), 1.0))
            self.spawn_timer = random.uniform(0.1, 0.3)

        # Update character brightness (fade out as they fall)
        for i in range(len(self.chars)):
            self.chars[i] = (self.chars[i][0], self.chars[i][1] * 0.98)

        # Remove faded characters
        self.chars = [c for c in self.chars if c[1] > 0.05]

        # Move characters down
        if len(self.chars) > self.max_height:
            self.chars.pop(0)


class SceneMatrixRain(Scene):
    """Matrix rain scene with hearts/flowers and color transition."""

    name = "matrix_rain"
    mood = "tech/cool"

    HEART_FLOWER_CHARS = ["♥", "♡", "❤", "❥", "✿", "❀", "✾", "❁"]

    def __init__(self, context: SceneContext):
        """Initialize Matrix Rain scene."""
        super().__init__(context)
        self.columns = []
        self.scene_time = 0.0
        self.color_progress = 0.0  # 0 = green, 1 = pink
        self.last_width = 0  # Track width for resizing

    def enter(self) -> None:
        """Called when scene becomes active."""
        self.columns = []
        self.scene_time = 0.0
        self.color_progress = 0.0
        self.last_width = self.context.console_width
        self._ensure_columns()

    def exit(self) -> None:
        """Called when scene becomes inactive."""
        self.columns = []

    def _ensure_columns(self) -> None:
        """Ensure columns exist for current width."""
        current_width = self.context.console_width
        # If width changed significantly, regenerate columns
        if abs(current_width - self.last_width) > 4 or not self.columns:
            self.last_width = current_width
            self.columns = []
            # Create columns across the screen (every 2 columns)
            for x in range(0, current_width, 2):
                self.columns.append(RainColumn(x, self.context.console_height))

    def update(self, dt: float, context: SceneContext) -> None:
        """
        Update scene state.

        Args:
            dt: Delta time in seconds
            context: Current scene context
        """
        self.scene_time += dt

        # Check for resize
        self._ensure_columns()

        # Color transition: green → pink over 30 seconds
        self.color_progress = min(1.0, self.scene_time / 30.0)

        # Speed increases with time and beat intensity
        speed_multiplier = 1.0 + (self.scene_time / 60.0) + context.beat_intensity

        for column in self.columns:
            column.update(dt, speed_multiplier)

    def render(self, buffer, alpha: float = 1.0) -> None:
        """
        Render scene to frame buffer.

        Args:
            buffer: FrameBuffer to render into
            alpha: Opacity 0.0-1.0 for fade
        """
        # Interpolate from green to pink
        r = int(0 * (1 - self.color_progress) + 255 * self.color_progress)
        g = int(255 * (1 - self.color_progress) + 105 * self.color_progress)
        b = int(0 * (1 - self.color_progress) + 180 * self.color_progress)
        base_color = Color.from_rgb(r, g, b)

        # Render each column
        for column in self.columns:
            for y, (char, brightness) in enumerate(reversed(column.chars)):
                screen_y = self.context.console_height - 1 - y
                if 0 <= screen_y < self.context.console_height:
                    # Apply brightness to color
                    char_color = self._apply_alpha(base_color, alpha * brightness)
                    self._set_buffer(buffer, column.x, screen_y, char, char_color)
