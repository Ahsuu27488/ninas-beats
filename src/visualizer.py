"""
Audio spectrum visualizer for Nina's Beats.

Simulated beat reactor that generates convincing audio-reactive bars
without the latency of real FFT.
"""
import math
import random
import time
from rich.color import Color
from typing import List

from .colors import get_gradient_color


# Unicode block characters for smooth bars
BLOCK_CHARS = " ▂▃▄▅▆▇█"


class SpectrumVisualizer:
    """
    Simulated beat reactor for audio visualization.

    Uses Perlin-like noise + scene intensity to generate convincing
    bar movements without audio latency.
    """

    def __init__(self, num_bars: int = 20):
        """
        Initialize the visualizer.

        Args:
            num_bars: Number of bars to display
        """
        self.num_bars = num_bars
        self.offset = random.random() * 100  # Random offset for noise variation
        self.bar_heights: List[float] = [0.0] * num_bars

    def update(self, dt: float, beat_intensity: float) -> None:
        """
        Update bar heights based on simulated beat.

        Args:
            dt: Delta time in seconds
            beat_intensity: 0.0-1.0 intensity from scene
        """
        self.offset += dt * 2  # Animate noise

        for i in range(self.num_bars):
            # Generate Perlin-like noise
            noise = (math.sin(self.offset + i * 0.3) +
                     math.sin(self.offset * 1.5 + i * 0.7) * 0.5 +
                     math.sin(self.offset * 2.3 + i * 1.1) * 0.25)

            # Normalize to 0-1
            noise = (noise + 1.75) / 3.5
            noise = max(0, min(1, noise))

            # Combine with beat intensity
            # Higher intensity = more pronounced peaks
            energy = noise * (0.3 + beat_intensity * 0.7)

            # Smooth transition from previous height
            self.bar_heights[i] = self.bar_heights[i] * 0.7 + energy * 0.3

    def render(self, width: int) -> str:
        """
        Render the visualizer as unicode bars.

        Args:
            width: Terminal width in columns

        Returns:
            String of unicode block characters forming bars
        """
        # Calculate bar width - use full width
        bar_width = max(2, width // self.num_bars)

        # Use 3 rows for height
        result = []

        # Create 3 rows of unicode blocks
        for row in range(3):  # 3 rows high
            line_parts = []
            for i in range(self.num_bars):
                height = self.bar_heights[i]
                # Convert to block level (0-7)
                level = int(height * 8)
                if level > 0:
                    # Determine which character to use
                    char_index = min(7, max(1, level - row * 3))
                    if row * 3 < level:
                        char = BLOCK_CHARS[char_index]
                    else:
                        char = ' '
                else:
                    char = ' '
                line_parts.append(char * bar_width)

            result.append(''.join(line_parts))

        return '\n'.join(result)

    def get_bar_color(self, bar_index: int, height: float) -> Color:
        """
        Get color for a bar based on its height.

        Args:
            bar_index: Index of the bar
            height: Bar height 0.0-1.0

        Returns:
            Color from gradient (Blue -> Cyan -> Pink -> Gold)
        """
        return get_gradient_color(height)
