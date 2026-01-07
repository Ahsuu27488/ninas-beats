"""
SceneFireworks for Nina's Beats.

Celebration scene with particle explosions and screen flashes.
"""
import random
from rich.color import Color

from .base import Scene, SceneContext
from ..particle import Particle, ParticleFactory
from ..colors import PINK, BLUE, GOLD


class SceneFireworks(Scene):
    """Fireworks scene with particle explosions."""

    name = "fireworks"
    mood = "celebration"

    def __init__(self, context: SceneContext):
        """Initialize Fireworks scene."""
        super().__init__(context)
        self.burst_timer = 0.0
        self.burst_interval = 0.5  # Time between bursts
        self.flash_timer = 0.0
        self.flash_duration = 0.1  # Flash duration
        self.is_flashing = False

        # Particle factory for firework particles
        self.factory = ParticleFactory(
            chars=["*", "✦", "✧", "⋆", "✵", "+"],
            colors=[PINK, BLUE, GOLD]
        )

    def enter(self) -> None:
        """Called when scene becomes active."""
        self.particles = []
        self.burst_timer = 0.0

    def exit(self) -> None:
        """Called when scene becomes inactive."""
        self.particles = []

    def update(self, dt: float, context: SceneContext) -> None:
        """
        Update scene state.

        Args:
            dt: Delta time in seconds
            context: Current scene context
        """
        # Update burst timer
        self.burst_timer -= dt

        # Spawn new burst on timer or beat intensity
        if self.burst_timer <= 0:
            self._spawn_burst(context)
            self.burst_timer = self.burst_interval * (1.1 - context.beat_intensity * 0.5)

        # Trigger flash on new burst
        if self.burst_timer > self.burst_interval - 0.1:
            self.is_flashing = True
            self.flash_timer = self.flash_duration

        # Update flash
        if self.is_flashing:
            self.flash_timer -= dt
            if self.flash_timer <= 0:
                self.is_flashing = False

        # Update existing particles
        for p in self.particles:
            p.update(dt)

        # Remove dead particles
        self.particles = [p for p in self.particles if p.is_alive()]

    def _spawn_burst(self, context: SceneContext) -> None:
        """Spawn a new particle burst."""
        # Random position in middle 60% of screen
        x = random.uniform(
            context.console_width * 0.2,
            context.console_width * 0.8
        )
        y = random.uniform(
            context.console_height * 0.2,
            context.console_height * 0.6
        )

        # Burst size varies with beat intensity
        count = int(20 + context.beat_intensity * 30)
        speed = 5.0 + context.beat_intensity * 10.0

        new_particles = self.factory.create_burst(x, y, count, speed)
        self.particles.extend(new_particles)

    def render(self, buffer, alpha: float = 1.0) -> None:
        """
        Render scene to frame buffer.

        Args:
            buffer: FrameBuffer to render into
            alpha: Opacity 0.0-1.0 for fade
        """
        # Render particles
        for p in self.particles:
            px, py = int(p.x), int(p.y)
            if 0 <= px < self.context.console_width and 0 <= py < self.context.console_height:
                color = p.get_render_color()
                self._set_buffer(buffer, px, py, p.char, color, alpha)
