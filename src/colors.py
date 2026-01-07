"""
Color palette constants for Nina's Beats.

Fixed RGB values for consistent appearance across terminals.
"""
from rich.color import Color

# Fixed RGB values for consistency
PINK = Color.from_rgb(255, 105, 180)   # Hot Pink
BLUE = Color.from_rgb(0, 191, 255)     # Deep Sky Blue
GOLD = Color.from_rgb(255, 215, 0)     # Gold
WHITE = Color.from_rgb(255, 255, 255)  # White
BLACK = Color.from_rgb(0, 0, 0)        # Black

# Color palette for particles
PARTICLE_COLORS = [PINK, BLUE, GOLD, WHITE]

# Color gradient for visualizer (low -> high)
def get_gradient_color(intensity: float) -> Color:
    """
    Get a color based on intensity level.

    Args:
        intensity: 0.0-1.0 intensity value

    Returns:
        Color interpolated through Blue -> Cyan -> Pink -> Gold
    """
    if intensity < 0.33:
        # Blue to Cyan
        t = intensity / 0.33
        return Color.from_rgb(
            int(0 * (1-t) + 0 * t),
            int(191 * (1-t) + 255 * t),
            int(255 * (1-t) + 255 * t)
        )
    elif intensity < 0.66:
        # Cyan to Pink
        t = (intensity - 0.33) / 0.33
        return Color.from_rgb(
            int(0 * (1-t) + 255 * t),
            int(255 * (1-t) + 105 * t),
            int(255 * (1-t) + 180 * t)
        )
    else:
        # Pink to Gold
        t = (intensity - 0.66) / 0.34
        return Color.from_rgb(
            int(255 * (1-t) + 255 * t),
            int(105 * (1-t) + 215 * t),
            int(180 * (1-t) + 0 * t)
        )
