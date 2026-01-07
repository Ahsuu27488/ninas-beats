"""
SceneFinale for Nina's Beats.

Clean, romantic closing with fading message and gentle particles.
"""
import random
import math

from .base import Scene, SceneContext
from ..particle import Particle, ParticleFactory
from ..colors import PINK, BLUE, GOLD, WHITE


class SceneFinale(Scene):
    """Finale scene with gentle effects and closing message."""

    name = "finale"
    mood = "romantic"

    def __init__(self, context: SceneContext, finale_message: str = "Forever yours,\nAhsan ♥"):
        """Initialize Finale scene."""
        super().__init__(context)
        self.finale_message = finale_message
        self.factory = ParticleFactory(
            chars=["✦", "⋆", "∗", "·"],
            colors=[PINK, GOLD, WHITE]
        )
        self.burst_timer = 0.0
        self.scene_time = 0.0
        self.message_alpha = 0.0  # Fade in the message

    def enter(self) -> None:
        """Called when scene becomes active."""
        self.particles = []
        self.burst_timer = 0.0
        self.scene_time = 0.0
        self.message_alpha = 0.0

    def exit(self) -> None:
        """Called when scene becomes inactive."""
        self.particles = []

    def update(self, dt: float, context: SceneContext) -> None:
        """Update scene state."""
        self.scene_time += dt

        # Gentle particle bursts (slower than fireworks)
        self.burst_timer -= dt
        if self.burst_timer <= 0:
            self._spawn_gentle_burst(context)
            self.burst_timer = 0.8  # Slower, more peaceful

        # Update particles
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.is_alive()]

        # Fade in message after 1 second
        if self.scene_time > 1.0:
            self.message_alpha = min(1.0, self.message_alpha + dt * 0.8)

    def _spawn_gentle_burst(self, context: SceneContext) -> None:
        """Spawn a gentle particle burst from bottom center."""
        cx = context.console_width / 2
        cy = context.console_height * 0.8  # Near bottom

        # Small bursts floating upward (negative gravity = floating up)
        count = 8 + int(context.beat_intensity * 5)
        for _ in range(count):
            offset_x = random.uniform(-15, 15)
            offset_y = random.uniform(-5, 5)
            speed_y = random.uniform(2, 5)  # Upward
            speed_x = random.uniform(-1, 1)
            life_time = random.uniform(1.5, 3.0)

            self.particles.append(Particle(
                x=cx + offset_x,
                y=cy + offset_y,
                vx=speed_x,
                vy=-speed_y,  # Negative = up
                gravity=-2.0,  # Negative gravity = float upward
                drag=0.1,  # Low drag
                life=1.0,  # Start at full life
                max_life=life_time,  # Lifetime in seconds
                char=random.choice(["✦", "⋆", "∗", "·"]),
                color=random.choice([PINK, GOLD, WHITE])
            ))

    def render(self, buffer, alpha: float = 1.0) -> None:
        """Render scene to frame buffer."""
        cx = self.context.console_width // 2
        cy = self.context.console_height // 2

        # Render particles (use built-in brightness curve)
        for p in self.particles:
            px, py = int(p.x), int(p.y)
            if 0 <= px < self.context.console_width and 0 <= py < self.context.console_height:
                # Use particle's built-in brightness based on life
                color = p.get_render_color()
                # Dim slightly for the finale effect
                self._set_buffer(buffer, px, py, p.char, color, alpha * 0.8)

        # Render heart symbol above message
        if self.message_alpha > 0:
            heart_line = "      ♥ ♥ ♥      "
            heart_y = cy - 3
            if heart_y >= 0:
                heart_x = (self.context.console_width - len(heart_line)) // 2
                self._set_text_buffer(buffer, heart_x, heart_y, heart_line, PINK, alpha * self.message_alpha)

        # Render closing message (centered, no padding overwrite)
        if self.message_alpha > 0:
            lines = self.finale_message.split('\n')
            start_y = cy - 1

            for i, line in enumerate(lines):
                y = start_y + i
                if 0 <= y < self.context.console_height:
                    # Center without padding (only write actual text chars)
                    line_x = (self.context.console_width - len(line)) // 2
                    self._set_text_buffer(buffer, line_x, y, line, PINK, alpha * self.message_alpha)
