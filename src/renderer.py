"""
Renderer for Nina's Beats.

Handles Rich Live display, terminal size detection, and frame composition.
"""
import shutil
from rich.console import Console
from rich.live import Live
from rich.color import Color
from rich.text import Text
from typing import Optional, Tuple, List


class FrameBuffer:
    """A 2D character buffer for building terminal frames."""

    def __init__(self, width: int, height: int):
        """Initialize an empty frame buffer."""
        self.width = width
        self.height = height
        # Buffer of (char, style) tuples
        self.buffer: List[List[tuple[str, str]]] = [
            [(" ", "") for _ in range(width)] for _ in range(height)
        ]

    def clear(self):
        """Clear the buffer to empty spaces."""
        self.buffer = [[(" ", "") for _ in range(self.width)] for _ in range(self.height)]

    def set(self, x: int, y: int, char: str, style: str = ""):
        """
        Set a character at a position.

        Args:
            x: Column (0-indexed)
            y: Row (0-indexed)
            char: Character to place (single char, multi-char will overwrite)
            style: Rich style string
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            self.buffer[y][x] = (char, style)

    def set_text(self, x: int, y: int, text: str, style: str = ""):
        """
        Place a horizontal string starting at position.

        Args:
            x: Starting column (0-indexed)
            y: Row (0-indexed)
            text: Text to place
            style: Rich style string
        """
        for i, char in enumerate(text):
            if 0 <= x + i < self.width and 0 <= y < self.height:
                self.buffer[y][x + i] = (char, style)

    def to_rich_text(self) -> Text:
        """
        Convert buffer to a Rich Text object.

        Returns:
            Text object with styled content
        """
        result = Text()
        for y in range(self.height):
            line_text = Text()
            x = 0
            while x < self.width:
                char, style = self.buffer[y][x]
                # Collect consecutive chars with same style
                run_start = x
                current_style = style
                while x + 1 < self.width and self.buffer[y][x + 1][1] == current_style:
                    x += 1
                    char += self.buffer[y][x][0]
                x += 1
                # Add styled segment
                if current_style:
                    line_text.append(char, style=current_style)
                else:
                    line_text.append(char)
            result.append(line_text)
            if y < self.height - 1:
                result.append("\n")
        return result


class Renderer:
    """Handles rendering to the terminal using Rich."""

    def __init__(self):
        """Initialize Renderer with Rich Console."""
        self.console = Console()
        self.terminal_width = 80
        self.terminal_height = 24
        self.live: Optional[Live] = None
        self.frame_buffer: Optional[FrameBuffer] = None

    def get_terminal_size(self) -> Tuple[int, int]:
        """
        Get current terminal size.

        Returns:
            Tuple of (width, height) in characters
        """
        size = shutil.get_terminal_size()
        self.terminal_width = size.columns
        self.terminal_height = size.lines

        # Rebuild frame buffer if size changed
        if self.frame_buffer is None or \
           self.frame_buffer.width != self.terminal_width or \
           self.frame_buffer.height != self.terminal_height:
            self.frame_buffer = FrameBuffer(self.terminal_width, self.terminal_height)

        return self.terminal_width, self.terminal_height

    def get_buffer(self) -> FrameBuffer:
        """Get the current frame buffer."""
        if self.frame_buffer is None:
            self.get_terminal_size()
        return self.frame_buffer

    def clear_buffer(self):
        """Clear the frame buffer."""
        if self.frame_buffer:
            self.frame_buffer.clear()

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

    def _apply_alpha(self, color: Color, alpha: float) -> Color:
        """
        Dim a color by alpha factor (simulated transparency).

        Args:
            color: Original color
            alpha: Opacity 0.0-1.0

        Returns:
            Color dimmed by alpha (blended toward black)
        """
        if alpha >= 1.0:
            return color
        # Blend toward black
        r, g, b = color.triplet
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
        r, g, b = color.triplet
        return f"rgb({int(r)},{int(g)},{int(b)})"

    def start_live(self) -> Live:
        """
        Start the Rich Live display.

        Returns:
            Live object for updating display
        """
        self.live = Live(
            console=self.console,
            refresh_per_second=30,
            screen=False  # Don't create a separate screen
        )
        self.live.start()
        return self.live

    def update_display(self, content: Text) -> None:
        """
        Update the Live display with new content.

        Args:
            content: Rich Text object to display
        """
        if self.live:
            self.live.update(content)

    def stop_live(self) -> None:
        """Stop the Rich Live display."""
        if self.live:
            self.live.stop()
            self.live = None
