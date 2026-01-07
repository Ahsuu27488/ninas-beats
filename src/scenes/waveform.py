"""
SceneWaveform for Nina's Beats.

Energetic scene with vertical bars at screen bottom.
"""
import math
from rich.color import Color

from .base import Scene, SceneContext
from ..colors import get_gradient_color


class SceneWaveform(Scene):
    """Waveform scene with vertical audio visualizer bars."""

    name = "waveform"
    mood = "energetic"

    BLOCK_CHARS = [' ', '▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']

    def __init__(self, context: SceneContext):
        """Initialize Waveform scene."""
        super().__init__(context)
        self.bar_heights = []
        self.offset = 0.0
        self.num_bars = 40  # Will be adjusted based on width
        self.last_width = 0

    def enter(self) -> None:
        """Called when scene becomes active."""
        self.offset = 0.0
        self.last_width = self.context.console_width
        self._ensure_bars()

    def exit(self) -> None:
        """Called when scene becomes inactive."""
        pass

    def _ensure_bars(self) -> None:
        """Ensure bar heights array exists for current width."""
        current_width = self.context.console_width
        # Calculate optimal number of bars (one per ~3 columns)
        target_bars = max(20, current_width // 3)

        if abs(target_bars - self.num_bars) > 5 or not self.bar_heights:
            self.num_bars = target_bars
            self.bar_heights = [0.0] * self.num_bars

    def update(self, dt: float, context: SceneContext) -> None:
        """
        Update scene state.

        Args:
            dt: Delta time in seconds
            context: Current scene context
        """
        self._ensure_bars()
        self.offset += dt * 3

        for i in range(self.num_bars):
            # Generate wave pattern
            wave = math.sin(self.offset + i * 0.3)
            wave = (wave + 1) / 2  # Normalize to 0-1

            # Modulate with beat intensity
            height = wave * (0.3 + context.beat_intensity * 0.7)

            # Smooth transition
            self.bar_heights[i] = self.bar_heights[i] * 0.8 + height * 0.2

    def render(self, buffer, alpha: float = 1.0) -> None:
        """
        Render scene to frame buffer.

        Args:
            buffer: FrameBuffer to render into
            alpha: Opacity 0.0-1.0 for fade
        """
        max_height = self.context.console_height // 2
        bar_width = max(1, self.context.console_width // self.num_bars)

        # Render bars from bottom up
        for i, height in enumerate(self.bar_heights):
            bar_height = int(height * max_height)
            x = (i * self.context.console_width) // self.num_bars

            for y in range(bar_height):
                screen_y = self.context.console_height - 2 - y
                if screen_y >= 0:
                    # Get color based on height/intensity
                    color = get_gradient_color(height)

                    # Choose block character
                    block_idx = min(8, int((y / max_height) * 9))
                    char = self.BLOCK_CHARS[block_idx]

                    # Fill bar width
                    for dx in range(bar_width):
                        if x + dx < self.context.console_width:
                            self._set_buffer(buffer, x + dx, screen_y, char, color, alpha)
