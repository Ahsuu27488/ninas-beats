"""
Director for Nina's Beats.

Main loop orchestrator that manages scene routing, time tracking, and transitions.
"""
import time
from dataclasses import dataclass, field
from typing import Dict, Type, Optional, List

from .scenes.base import Scene, SceneContext, SceneState
from .lyric_sync import LyricMap, LyricEntry


# Performance constants
TARGET_FPS = 30
FRAME_TIME = 1.0 / TARGET_FPS
INITIAL_PARTICLE_BUDGET = 500
MIN_PARTICLE_BUDGET = 50
LAG_THRESHOLD_MULTIPLIER = 1.5
FADE_DURATION = 0.5


@dataclass
class DirectorState:
    """Global state managed by Director."""
    # Time
    start_time: float = 0.0  # Wall clock when experience started
    current_time: float = 0.0  # Current song time in seconds
    is_paused: bool = False
    pause_offset: float = 0.0  # Accumulated pause duration

    # Scene management
    current_scene: Optional[SceneState] = None
    next_scene: Optional[str] = None  # Queued scene name for transition
    transition_alpha: float = 0.0  # 0.0 = fully old, 1.0 = fully new

    # Content
    lyric_map: Optional[LyricMap] = None
    current_lyric: Optional[LyricEntry] = None

    # Input
    pending_quit: bool = False

    # Performance
    last_frame_time: float = 0.0
    fps: float = 0.0
    particle_budget: int = INITIAL_PARTICLE_BUDGET


class Director:
    """Main loop orchestrator."""

    def __init__(self, lyric_map: LyricMap):
        """
        Initialize Director.

        Args:
            lyric_map: LyricMap with timestamped lyrics
        """
        self.lyric_map = lyric_map
        self.scenes: Dict[str, Type[Scene]] = {}
        self.current_scene: Optional[Scene] = None
        self.next_scene_name: Optional[str] = None
        self.transition_alpha: float = 0.0
        self.transitioning_scene: Optional[Scene] = None
        self.state = DirectorState(lyric_map=lyric_map)
        self.scene_start_time: float = 0.0

    def register_scene(self, name: str, scene_class: Type[Scene]) -> None:
        """
        Register a scene class for instantiation.

        Args:
            name: Scene identifier (e.g., "fireworks")
            scene_class: Scene class (not instance)
        """
        self.scenes[name] = scene_class

    def transition_to(self, scene_name: str) -> None:
        """
        Request a scene transition.

        Args:
            scene_name: Name of scene to transition to (must be registered)

        Transition takes FADE_DURATION (0.5s) with alpha blend.
        """
        if scene_name not in self.scenes:
            raise ValueError(f"Unknown scene: {scene_name}")
        self.next_scene_name = scene_name
        self.transition_alpha = 0.0

    def update_scenes(self, dt: float, context: SceneContext) -> None:
        """
        Update all active scenes.

        Args:
            dt: Delta time in seconds
            context: Current scene context from Director

        - If transitioning: update both current and next scenes
        - Otherwise: update only current scene
        """
        # Update current scene
        if self.current_scene:
            self.current_scene.update(dt, context)

        # Update transitioning scene
        if self.transitioning_scene:
            self.transitioning_scene.update(dt, context)

        # Handle transition progress
        if self.next_scene_name is not None:
            self.transition_alpha += dt / FADE_DURATION
            if self.transition_alpha >= 1.0:
                self._complete_transition()

    def render_scenes(self, console) -> None:
        """
        Render scenes with alpha blending.

        Args:
            console: Rich Console for rendering

        - If transitioning: render both scenes with appropriate alpha
        - Otherwise: render only current scene at full opacity
        """
        if self.transitioning_scene and self.current_scene:
            # Render both with alpha
            old_alpha = 1.0 - self.transition_alpha
            new_alpha = self.transition_alpha
            self.current_scene.render(console, alpha=old_alpha)
            self.transitioning_scene.render(console, alpha=new_alpha)
        elif self.current_scene:
            self.current_scene.render(console, alpha=1.0)

    def _complete_transition(self) -> None:
        """Complete the scene transition."""
        if self.transitioning_scene:
            # Exit old scene
            if self.current_scene:
                self.current_scene.exit()
            # New scene becomes current
            self.current_scene = self.transitioning_scene
            self.transitioning_scene = None
        elif self.next_scene_name in self.scenes:
            # Create and instantiate new scene directly
            SceneClass = self.scenes[self.next_scene_name]
            context = SceneContext(
                console_width=80,  # Will be updated per frame
                console_height=24,
                song_time=self.state.current_time,
                scene_time=0.0,
                beat_intensity=0.0,
                is_transitioning=False
            )
            if self.current_scene:
                self.current_scene.exit()

            # Pass finale_message to SceneFinale if available
            if self.next_scene_name == "finale" and self.lyric_map:
                self.current_scene = SceneClass(context, finale_message=self.lyric_map.finale_message)
            else:
                self.current_scene = SceneClass(context)
            self.current_scene.enter()

        self.next_scene_name = None
        self.transition_alpha = 0.0
        self.scene_start_time = time.time()

    def get_current_scene_name(self) -> Optional[str]:
        """Get the name of the currently active scene."""
        if self.current_scene:
            return self.current_scene.name
        return None

    def check_scene_triggers(self, time: float) -> None:
        """
        Check if a scene transition should trigger based on lyric time.

        Args:
            time: Current playback time
        """
        if self.lyric_map:
            scene_name = self.lyric_map.get_scene_trigger(time)
            if scene_name and scene_name != self.get_current_scene_name():
                self.transition_to(scene_name)

    def update_lyric(self, time: float) -> None:
        """
        Update the current lyric based on playback time.

        Args:
            time: Current playback time
        """
        if self.lyric_map:
            self.state.current_lyric = self.lyric_map.get_lyric_at(time)

    def monitor_performance(self, frame_time: float) -> None:
        """
        Monitor frame time and adjust particle budget if needed.

        Args:
            frame_time: Time taken for last frame in seconds
        """
        self.state.last_frame_time = frame_time

        # Calculate FPS
        if frame_time > 0:
            self.state.fps = 1.0 / frame_time

        # Check for lag and degrade particle budget
        if frame_time > FRAME_TIME * LAG_THRESHOLD_MULTIPLIER:
            # Reduce by 25%
            self.state.particle_budget = max(
                MIN_PARTICLE_BUDGET,
                int(self.state.particle_budget * 0.75)
            )
