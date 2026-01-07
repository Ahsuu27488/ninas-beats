"""
SceneHeartbeat for Nina's Beats.
Refined: Smaller, galaxy-style aesthetic with stardust fill.
"""
import math
import random
from rich.color import Color
from .base import Scene, SceneContext
from ..colors import PINK, WHITE

class SceneHeartbeat(Scene):
    """Heartbeat scene with a smaller, stardust-style heart."""

    name = "heartbeat"
    mood = "deep/intense"

    def __init__(self, context: SceneContext):
        super().__init__(context)
        self.current_scale = 1.0
        self.beat_phase = 0.0
        # Pre-calculate some random static noise for the "stars" inside the heart
        # so they don't jitter around constantly
        self.noise_map = {} 

    def enter(self) -> None:
        self.current_scale = 1.0
        self.beat_phase = 0.0

    def update(self, dt: float, context: SceneContext) -> None:
        # Slower, deeper throb
        self.beat_phase += dt * 3.5

        # Organic heartbeat curve (sharp rise, slow fall)
        # sin^6 gives a nice sharp "thump"
        thump = math.sin(self.beat_phase) ** 6
        
        # Reduced scaling range so it doesn't jump too much
        # Base scale 1.0, max scale 1.15
        target = 1.0 + (thump * 0.15) + (context.beat_intensity * 0.1)

        # Smooth movement
        self.current_scale += (target - self.current_scale) * (dt * 5)

    def _get_noise(self, x, y):
        """Stable random noise for stardust effect"""
        if (x, y) not in self.noise_map:
            self.noise_map[(x, y)] = random.random()
        return self.noise_map[(x, y)]

    def render(self, buffer, alpha: float = 1.0) -> None:
        cx = self.context.console_width // 2
        cy = self.context.console_height // 2
        
        # SIGNIFICANTLY REDUCED SIZE
        # Radius 6 means approx 13 lines tall (much better for mobile)
        radius_y = 6.5 * self.current_scale
        radius_x = radius_y * 2.2  # Aspect ratio correction

        # Optimization: Scissor test (only loop relevant area)
        min_y = int(cy - radius_y * 1.5)
        max_y = int(cy + radius_y * 1.5)
        min_x = int(cx - radius_x * 1.5)
        max_x = int(cx + radius_x * 1.5)

        for y in range(max(0, min_y), min(self.context.console_height, max_y)):
            ny = (cy - y) / radius_y
            
            for x in range(max(0, min_x), min(self.context.console_width, max_x)):
                nx = (x - cx) / radius_x
                
                # Heart Equation
                a = nx*nx + ny*ny - 1
                value = a*a*a - (nx*nx * ny*ny*ny)
                
                # Check if we are inside or on the edge
                if value <= 0:
                    # EDGE DETECTION
                    # If value is close to 0, it's the outline.
                    # If value is negative, it's the inside.
                    
                    if value > -0.2:
                        # THE OUTLINE (Bright & Clean)
                        self._set_buffer(buffer, x, y, "*", PINK, alpha)
                    
                    else:
                        # THE INSIDE (Stardust Fill)
                        # We don't fill every pixel. We leave some empty for "space"
                        noise = self._get_noise(x, y)
                        
                        if noise > 0.7:
                            # Sparse stars inside
                            self._set_buffer(buffer, x, y, "·", PINK, alpha * 0.5)
                        elif noise > 0.95:
                            # Rare bright sparkles
                            self._set_buffer(buffer, x, y, "+", WHITE, alpha * 0.8)