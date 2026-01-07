"""
Particle system for Nina's Beats.

Handles particle physics simulation with gravity, drag, and life/decay.
"""
import random
import math
from dataclasses import dataclass
from typing import List, Optional
from rich.color import Color


@dataclass
class Particle:
    """A visual particle with physics simulation."""

    # Position (screen coordinates, 0,0 = top-left)
    x: float
    y: float

    # Velocity (units per second)
    vx: float
    vy: float

    # Physics constants
    gravity: float  # Downward acceleration (positive = down)
    drag: float  # Air resistance 0-1

    # Lifecycle
    life: float  # Remaining life 0.0-1.0
    max_life: float  # Initial life value (seconds until death)

    # Appearance
    char: str  # Single character to render: ♥, *, ♪, ✿, etc.
    color: Color  # Rich color object

    def update(self, dt: float) -> None:
        """
        Update particle state by one time step.

        Args:
            dt: Delta time in seconds

        Physics applied:
        1. Gravity: vy += gravity * dt
        2. Drag: vx *= (1 - drag * dt), vy *= (1 - drag * dt)
        3. Position: x += vx * dt, y += vy * dt
        4. Life: life -= dt / max_life
        """
        # Apply gravity
        self.vy += self.gravity * dt

        # Apply drag (air resistance)
        drag_factor = max(0, 1 - self.drag * dt)
        self.vx *= drag_factor
        self.vy *= drag_factor

        # Update position
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Decrease life
        self.life -= dt / self.max_life

    def is_alive(self) -> bool:
        """Return True if particle is still alive (life > 0)."""
        return self.life > 0

    def get_brightness(self) -> float:
        """
        Get brightness modifier based on life.

        Returns:
            0.0-1.0 brightness factor

        Curve: Parabolic ease-in-out
        - Birth (life=1.0): brightness=0.0 (fade in from white)
        - Mid (life=0.5): brightness=1.0 (full color)
        - Death (life=0.0): brightness=0.0 (fade out)
        """
        return 4 * self.life * (1 - self.life)

    def get_render_color(self) -> Color:
        """
        Get color adjusted for life/brightness.

        Returns:
            Color dimmed by current brightness

        At birth: pure white (fade in effect)
        At midlife: full particle color
        At death: dim toward black
        """
        brightness = self.get_brightness()
        if brightness <= 0:
            return Color.from_rgb(0, 0, 0)

        r, g, b = self.color.triplet
        return Color.from_rgb(
            int(r * brightness),
            int(g * brightness),
            int(b * brightness)
        )


class ParticleFactory:
    """Factory for creating particles with random variation."""

    # Character sets for different effects
    HEARTS = ["♥", "♡", "❤", "❥"]
    STARS = ["*", "✦", "✧", "⋆", "✵"]
    MUSICAL = ["♪", "♫", "♬", "♩"]
    FLOWERS = ["✿", "❀", "✾", "❁"]
    DIGITAL = ["0", "1"]
    SPARKS = ["*", ".", "+", "✦"]

    def __init__(self, chars: List[str], colors: List[Color]):
        """
        Initialize factory.

        Args:
            chars: List of characters to randomly select from
            colors: List of colors to randomly select from
        """
        self.chars = chars
        self.colors = colors

    def create(
        self,
        x: float,
        y: float,
        vx_base: float,
        vy_base: float,
        life: float,
        gravity: float = 9.8,
        drag: float = 0.5,
        spread: float = 0.2
    ) -> Particle:
        """
        Create a particle with random variation.

        Args:
            x, y: Initial position
            vx_base, vy_base: Base velocity
            life: Particle lifetime in seconds
            gravity: Downward acceleration
            drag: Air resistance
            spread: Velocity variation (Gaussian std dev)

        Returns:
            New Particle with randomized attributes
        """
        vx = random.gauss(vx_base, spread)
        vy = random.gauss(vy_base, spread)
        char = random.choice(self.chars)
        color = random.choice(self.colors)
        return Particle(
            x=x, y=y,
            vx=vx, vy=vy,
            gravity=gravity,
            drag=drag,
            life=1.0,  # Start at full life
            max_life=life,
            char=char,
            color=color
        )

    def create_burst(
        self,
        x: float,
        y: float,
        count: int,
        speed: float = 10.0,
        life: float = 2.0
    ) -> List[Particle]:
        """
        Create a burst of particles in all directions.

        Args:
            x, y: Center of burst
            count: Number of particles to create
            speed: Base velocity magnitude
            life: Particle lifetime

        Returns:
            List of new particles
        """
        particles = []
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed_var = random.uniform(speed * 0.5, speed * 1.5)
            vx = math.cos(angle) * speed_var
            vy = math.sin(angle) * speed_var
            particles.append(self.create(x, y, vx, vy, life))
        return particles
