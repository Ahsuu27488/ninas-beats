"""
SceneIntro for Nina's Beats.

Black screen with typing text in hacker style.
"""
import time

from rich.color import Color

from .base import Scene, SceneContext
from ..colors import PINK


class SceneIntro(Scene):
    """Intro scene with hacker-style typing text."""

    name = "intro"
    mood = "mysterious"

    # Intro text sequence
    TEXTS = [
        "Hey Mistress...",
        "You just got hacked..",
        "Just kidding, it's your boy."
    ]

    # Typing speed: 50-80ms per character
    TYPING_SPEED_MIN = 0.05
    TYPING_SPEED_MAX = 0.08
    PAUSE_BETWEEN_LINES = 1.0  # Seconds to wait before next line

    def __init__(self, context: SceneContext):
        """Initialize Intro scene."""
        super().__init__(context)
        self.current_text_index = 0
        self.current_char_index = 0
        self.type_timer = 0.0
        self.pause_timer = 0.0
        self.is_pausing = False

    def enter(self) -> None:
        """Called when scene becomes active."""
        self.current_text_index = 0
        self.current_char_index = 0
        self.type_timer = 0.0
        self.pause_timer = 0.0
        self.is_pausing = False

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
        # Check if all texts complete
        if self.current_text_index >= len(self.TEXTS):
            return

        # If we're pausing between lines
        if self.is_pausing:
            self.pause_timer += dt
            if self.pause_timer >= self.PAUSE_BETWEEN_LINES:
                # Move to next line
                self.current_text_index += 1
                self.current_char_index = 0
                self.is_pausing = False
                self.pause_timer = 0.0
            return

        # Typing animation
        self.type_timer += dt

        # Time to type next character?
        type_delay = self.TYPING_SPEED_MIN + (self.TYPING_SPEED_MAX - self.TYPING_SPEED_MIN) * (
            self.current_char_index % 10) / 10

        if self.type_timer >= type_delay:
            self.type_timer = 0
            self.current_char_index += 1

            # Check if current text is complete
            if self.current_char_index >= len(self.TEXTS[self.current_text_index]):
                # Start pause before next line
                if self.current_text_index < len(self.TEXTS) - 1:
                    self.is_pausing = True

    def render(self, buffer, alpha: float = 1.0) -> None:
        """
        Render scene to frame buffer.

        Args:
            buffer: FrameBuffer to render into
            alpha: Opacity 0.0-1.0 for fade
        """
        # Calculate vertical centering
        total_lines = len(self.TEXTS)
        start_y = (self.context.console_height - total_lines) // 2
        start_y = max(2, start_y)  # At least 2 lines from top

        # Render each text line
        for i, text in enumerate(self.TEXTS):
            y = start_y + i * 2  # Add spacing between lines
            if y >= self.context.console_height:
                break

            if i < self.current_text_index:
                # Previous texts - show complete
                centered = self._center_text(text, self.context.console_width)
                self._set_text_buffer(buffer, 0, y, centered, PINK, alpha)
            elif i == self.current_text_index:
                # Current text - show partial
                chars_to_show = min(self.current_char_index, len(text))
                partial = text[:chars_to_show]
                # Center the partial text
                x = (self.context.console_width - len(text)) // 2
                self._set_text_buffer(buffer, x, y, partial, PINK, alpha)
