"""
Scene base classes for Nina's Beats.

Defines the abstract Scene interface and context data structures.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, TYPE_CHECKING
from rich.console import Console
from rich.color import Color

from ..particle import Particle

if TYPE_CHECKING:
    from ..renderer import FrameBuffer


@dataclass
class SceneContext:
    """Context provided to scenes by Director."""
    console_width: int
    console_height: int
    song_time: float  # Current audio position in seconds
    scene_time: float  # Time since scene started
    beat_intensity: float  # 0.0-1.0, from simulated beat reactor
    is_transitioning: bool


@dataclass
class SceneState:
    """Current state of the active scene."""
    name: str  # Scene class name
    alpha: float  # Opacity 0.0-1.0 (for fade in/out)
    started_at: float  # When this scene became active
    particles: List[Particle]  # Scene-owned particles (if applicable)

    def is_fading(self) -> bool:
        return self.alpha < 1.0


class Scene(ABC):
    """Abstract base class for all visual scenes."""

    # Class attributes
    name: str  # Unique identifier (e.g., "fireworks")
    mood: str  # For docs: "celebration", "dreamy", etc.

    def __init__(self, context: SceneContext):
        """
        Initialize scene with initial context.

        Args:
            context: Initial scene context
        """
        self.context = context
        self.particles: List[Particle] = []

    @abstractmethod
    def update(self, dt: float, context: SceneContext) -> None:
        """
        Update scene state.

        Args:
            dt: Delta time in seconds since last update
            context: Current scene context from Director

        Called every frame. Update animations, particles, etc.
        """
        pass

    @abstractmethod
    def render(self, buffer: 'FrameBuffer', alpha: float = 1.0) -> None:
        """
        Render scene to frame buffer.

        Args:
            buffer: FrameBuffer to render into
            alpha: Opacity 0.0-1.0 (for fade in/out transitions)

        Called every frame after update(). Render visual elements.
        """
        pass

    def enter(self) -> None:
        """Called when scene becomes active. Override for setup."""
        pass

    def exit(self) -> None:
        """Called when scene becomes inactive. Override for cleanup."""
        pass

    def get_particle_count(self) -> int:
        """Return current number of active particles."""
        return len(self.particles)

    def reduce_particles(self, ratio: float) -> None:
        """
        Reduce particle count for graceful degradation.

        Args:
            ratio: Keep this fraction of particles (0.0-1.0)
        """
        keep_count = int(len(self.particles) * ratio)
        self.particles = self.particles[:keep_count]

    def _apply_alpha(self, color: Color, alpha: float) -> Color:
        """
        Dim a color by alpha factor (simulated transparency).

        Args:
            color: Original color
            alpha: Opacity 0.0-1.0

        Returns:
            Color dimmed by alpha
        """
        if alpha >= 1.0:
            return color
        # Blend toward black
        if color.triplet is not None:
            r, g, b = color.triplet
        else:
            # Fallback to white if triplet is None
            r, g, b = 255, 255, 255
        return Color.from_rgb(
            int(r * alpha),
            int(g * alpha),
            int(b * alpha)
        )

    def _color_to_style(self, color: Color) -> str:
        """
        Convert a Color object to a style string for Rich.

        Args:
            color: Rich Color object

        Returns:
            Style string that Rich accepts (e.g., "rgb(255,105,180)")
        """
        if color.triplet is not None:
            r, g, b = color.triplet
        else:
            r, g, b = 255, 255, 255  # fallback to white if triplet is None
        return f"rgb({int(r)},{int(g)},{int(b)})"

    def _set_buffer(self, buffer: 'FrameBuffer', x: int, y: int, char: str, color: Color, alpha: float = 1.0) -> None:
        """
        Set a character in the frame buffer with color and alpha.

        Args:
            buffer: FrameBuffer to modify
            x: Column (0-indexed)
            y: Row (0-indexed)
            char: Character to place
            color: Rich Color object
            alpha: Additional opacity 0.0-1.0
        """
        if 0 <= x < self.context.console_width and 0 <= y < self.context.console_height:
            final_color = self._apply_alpha(color, alpha)
            style = self._color_to_style(final_color)
            buffer.set(x, y, char, style)

    def _set_text_buffer(self, buffer: 'FrameBuffer', x: int, y: int, text: str, color: Color, alpha: float = 1.0) -> None:
        """
        Place text in the frame buffer with color and alpha.

        Args:
            buffer: FrameBuffer to modify
            x: Starting column (0-indexed)
            y: Row (0-indexed)
            text: Text to place
            color: Rich Color object
            alpha: Additional opacity 0.0-1.0
        """
        if 0 <= y < self.context.console_height:
            final_color = self._apply_alpha(color, alpha)
            style = self._color_to_style(final_color)
            buffer.set_text(x, y, text, style)

    def _center_text(self, text: str, width: int) -> str:
        """
        Center text within given width.

        Args:
            text: Text to center
            width: Width to center within

        Returns:
            Centered text with padding
        """
        if len(text) >= width:
            return text[:width]
        padding = (width - len(text)) // 2
        return ' ' * padding + text + ' ' * (width - len(text) - padding)
