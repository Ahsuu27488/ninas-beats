"""
SceneStarfield for Nina's Beats.

Dreamy scene with 3D starfield moving toward camera (warp effect).
"""
import random
from rich.color import Color

from .base import Scene, SceneContext
from ..colors import BLUE, WHITE


class Star:
    """A single star in 3D space."""

    def __init__(self, max_depth: float = 100.0):
        """Initialize star with random 3D position."""
        self.x = random.uniform(-50, 50)
        self.y = random.uniform(-25, 25)
        self.z = random.uniform(1, max_depth)
        self.max_depth = max_depth

    def update(self, speed: float) -> None:
        """Move star toward camera (decrease z)."""
        self.z -= speed
        if self.z <= 1:
            # Reset star to back
            self.z = self.max_depth
            self.x = random.uniform(-50, 50)
            self.y = random.uniform(-25, 25)


class SceneStarfield(Scene):
    """Starfield scene with 3D warp effect."""

    name = "starfield"
    mood = "dreamy"

    STAR_CHARS = ["*", "✦", "⋆", "+", "."]
    NUM_STARS = 150  # More stars for better effect

    def __init__(self, context: SceneContext):
        """Initialize Starfield scene."""
        super().__init__(context)
        self.stars = [Star() for _ in range(self.NUM_STARS)]
        self.speed = 5.0

    def enter(self) -> None:
        """Called when scene becomes active."""
        pass

    def exit(self) -> None:
        """Called when scene becomes inactive."""
        pass

    def update(self, dt: float, context: SceneContext) -> None:
        """
        Update scene state.

        Args:
            dt: Delta time in seconds
            context: Current scene context
        """
        # Speed increases with beat intensity
        current_speed = self.speed * (1 + context.beat_intensity * 2)

        for star in self.stars:
            star.update(current_speed * dt)

    def render(self, buffer, alpha: float = 1.0) -> None:
        """
        Render scene to frame buffer.

        Args:
            buffer: FrameBuffer to render into
            alpha: Opacity 0.0-1.0 for fade
        """
        cx = self.context.console_width / 2
        cy = self.context.console_height / 2

        for star in self.stars:
            # Perspective projection
            if star.z <= 0:
                continue

            scale = 50 / star.z
            screen_x = int(cx + star.x * scale)
            screen_y = int(cy + star.y * scale)

            # Check bounds
            if 0 <= screen_x < self.context.console_width and 0 <= screen_y < self.context.console_height:
                # Choose character based on depth (closer = brighter)
                depth_idx = min(len(self.STAR_CHARS) - 1, int(star.z / 20))
                char = self.STAR_CHARS[depth_idx]

                # Color: white for close stars, blue for distant
                color = WHITE if star.z < 20 else BLUE
                self._set_buffer(buffer, screen_x, screen_y, char, color, alpha)
