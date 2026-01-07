"""
Nina's Beats (Symphony Edition) - Main Entry Point

A terminal-based audio-visual love experience for Nina.
"""
import sys
import time
import signal
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.live import Live
from rich.text import Text

from .director import Director, FRAME_TIME
from .audio_manager import AudioManager
from .renderer import Renderer
from .visualizer import SpectrumVisualizer
from .lyric_sync import LyricMap
from .scenes.base import SceneContext

# Scene imports
from .scenes.intro import SceneIntro
from .scenes.starfield import SceneStarfield
from .scenes.matrix import SceneMatrixRain
from .scenes.fireworks import SceneFireworks
from .scenes.heartbeat import SceneHeartbeat
from .scenes.waveform import SceneWaveform
from .scenes.finale import SceneFinale

# Configuration
DEFAULT_ASSETS_DIR = Path(__file__).parent.parent / "assets"
DEFAULT_LYRICS_PATH = DEFAULT_ASSETS_DIR / "lyrics.json"
DEFAULT_AUDIO_PATH = DEFAULT_ASSETS_DIR / "audio.mp3"

# Frame timing
TARGET_FPS = 30


class NonBlockingInput:
    """Non-blocking keyboard input handler."""

    def __init__(self):
        self._quit_requested = False
        self._pause_requested = False

        # Set up signal handlers for clean shutdown
        signal.signal(signal.SIGINT, self._handle_sigint)

    def _handle_sigint(self, signum, frame):
        """Handle Ctrl+C gracefully."""
        self._quit_requested = True

    def check(self) -> tuple[bool, bool]:
        """
        Check for input events.

        Returns:
            Tuple of (should_quit, toggle_pause)
        """
        # For terminal compatibility, we use a simple approach
        # Real non-blocking input requires termios/unistd (Unix) or msvcrt (Windows)
        # Since we're targeting Termux, we'll use signal-based quit
        # and a simple flag for pause toggle

        quit_requested = self._quit_requested
        pause_requested = self._pause_requested

        # Reset pause flag after reading
        self._pause_requested = False

        return quit_requested, pause_requested

    def request_pause_toggle(self):
        """Request pause toggle (called by external input handler if available)."""
        self._pause_requested = True


def load_assets(lyrics_path: Path, audio_path: Path) -> tuple[Optional[LyricMap], Optional[Path]]:
    """
    Load lyrics.json and verify audio file exists.

    Args:
        lyrics_path: Path to lyrics.json
        audio_path: Path to audio.mp3

    Returns:
        Tuple of (LyricMap or None, audio_path or None)

    Displays friendly error messages if assets are missing.
    """
    console = Console()

    # Load lyrics
    lyric_map = None
    if lyrics_path.exists():
        try:
            lyric_map = LyricMap.from_json(lyrics_path)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load lyrics: {e}[/yellow]")
    else:
        console.print(f"[yellow]Lyrics file not found: {lyrics_path}[/yellow]")
        console.print("[yellow]Using default placeholder lyrics.[/yellow]")
        # Create default lyric map
        lyric_map = LyricMap(
            lyrics=[],
            finale_message="Forever yours,\nAhsan ♥"
        )

    # Check audio file
    if not audio_path.exists():
        console.print(f"\n[red]Audio file not found: {audio_path}[/red]")
        console.print(f"[yellow]Expected at: {audio_path}[/yellow]")
        console.print("[yellow]Please place your song file as 'audio.mp3' in the assets folder.[/yellow]")
        console.print("[dim]The experience will run without audio.[/dim]\n")
        return lyric_map, None

    return lyric_map, audio_path


def get_beat_intensity(song_time: float, scene_mood: str) -> float:
    """
    Get simulated beat intensity based on time and scene mood.

    Args:
        song_time: Current playback time in seconds
        scene_mood: Mood string from current scene

    Returns:
        Beat intensity 0.0-1.0
    """
    import math

    # Base rhythm: steady pulse
    base = (math.sin(song_time * 3) + 1) / 2

    # Mood modulation
    mood_multiplier = 1.0
    if scene_mood in ("energetic", "celebration"):
        mood_multiplier = 1.2
    elif scene_mood in ("dreamy", "romantic"):
        mood_multiplier = 0.7

    # Add some variance
    intensity = min(1.0, base * mood_multiplier)
    return intensity


def build_frame(
    renderer: Renderer,
    director,
    visualizer: SpectrumVisualizer,
    lyric_text: Optional[str],
    beat_intensity: float,
    width: int,
    height: int
) -> Text:
    """
    Build a complete frame with scene, lyrics, and visualizer.

    Args:
        renderer: Renderer with frame buffer
        director: Director with active scenes
        visualizer: SpectrumVisualizer for beat display
        lyric_text: Current lyric to display
        beat_intensity: Current beat intensity
        width: Terminal width
        height: Terminal height

    Returns:
        Rich Text object with complete frame
    """
    # Clear and get frame buffer
    renderer.clear_buffer()
    buffer = renderer.get_buffer()

    # Render the current scene to the buffer
    if director.current_scene:
        scene = director.current_scene
        # Call the scene's render method with the buffer
        # Get scene alpha from director state
        scene_alpha = 1.0
        if hasattr(director, 'current_state') and director.current_state:
            scene_alpha = director.current_state.alpha

        # Create a context for the scene with current dimensions
        context = SceneContext(
            console_width=width,
            console_height=height,
            song_time=director.song_time if hasattr(director, 'song_time') else 0,
            scene_time=director.current_state.started_at if hasattr(director, 'current_state') and director.current_state else 0,
            beat_intensity=beat_intensity,
            is_transitioning=False
        )

        # Update scene's context and render
        scene.context = context
        scene.render(buffer, scene_alpha)

    # Render lyrics on top (centered with padding) - only if not intro/finale
    if lyric_text and director.current_scene:
        scene_name = director.current_scene.name
        # Don't show lyrics during intro or finale (they have their own text)
        if scene_name not in ("intro", "finale"):
            # Calculate padded width (10% padding on each side)
            padding = max(4, width // 10)
            text_width = width - 2 * padding
            if text_width < 20:  # Too narrow, reduce padding
                padding = 2
                text_width = width - 4

            # Word-wrap the lyric text
            import textwrap
            wrapped_lines = textwrap.wrap(lyric_text, width=text_width, break_long_words=False)

            # Render each line, centered within padded area
            lyric_start_y = (height - len(wrapped_lines)) // 2
            for i, line in enumerate(wrapped_lines):
                y = lyric_start_y + i
                if 0 <= y < height:
                    # Calculate x position (centered within padded area)
                    # Only write the actual text, not padding spaces (so scene shows through)
                    line_padding = (text_width - len(line)) // 2
                    start_x = padding + line_padding
                    buffer.set_text(start_x, y, line, "pink1 bold")

    # Render visualizer at bottom (subtle)
    viz_lines = visualizer.render(width).split('\n')
    viz_y = height - len(viz_lines)
    for i, line in enumerate(viz_lines):
        buffer.set_text(0, viz_y + i, line, "cyan dim")

    return buffer.to_rich_text()


def run_main_loop(
    director: Director,
    audio_manager: Optional[AudioManager],
    renderer: Renderer,
    visualizer: SpectrumVisualizer,
    console: Console,
    input_handler: NonBlockingInput
) -> bool:
    """
    Run the main event loop.

    Args:
        director: Director instance
        audio_manager: AudioManager instance (may be None)
        renderer: Renderer instance
        visualizer: SpectrumVisualizer instance
        console: Rich Console
        input_handler: NonBlockingInput instance

    Returns:
        True if completed normally, False if error occurred
    """
    # Track state
    is_paused = False
    experience_complete = False
    song_duration = 180.0  # Default, will be updated from lyrics

    # Get song duration from lyrics
    if director.lyric_map and hasattr(director.lyric_map, 'duration'):
        song_duration = getattr(director.lyric_map, 'duration', 180.0)

    # Start audio
    if audio_manager:
        audio_state = audio_manager.start()
        if audio_state.has_error:
            console.print("[dim]♫ Imagine beautiful music here... ♫[/dim]\n")
            time.sleep(1)
            audio_manager = None

    # Set initial scene
    if not director.current_scene:
        # Check lyrics for initial scene
        initial_scene = director.lyric_map.get_scene_trigger(0.0) if director.lyric_map else None
        if not initial_scene:
            initial_scene = "intro"  # Default
        director.transition_to(initial_scene)
        director._complete_transition()

    # Start Rich Live display
    live = renderer.start_live()

    # Start time for experience
    start_time = time.time()
    frame_count = 0

    try:
        while True:
            frame_start = time.time()

            # Check for quit
            should_quit, toggle_pause = input_handler.check()
            if should_quit:
                break

            # Handle pause toggle
            if toggle_pause:
                is_paused = not is_paused
                if audio_manager:
                    if is_paused:
                        audio_manager.pause()
                    else:
                        audio_manager.resume()

            # Get current time
            if audio_manager:
                current_time = audio_manager.get_time()
            else:
                current_time = time.time() - start_time

            # Check if experience is complete
            # If finale scene is active, give it extra time to display
            scene_name = director.get_current_scene_name() or "intro"
            is_finale = scene_name == "finale"

            if current_time >= song_duration:
                if is_finale:
                    # Give finale 5 more seconds after song ends
                    if current_time >= song_duration + 5:
                        experience_complete = True
                        break
                else:
                    experience_complete = True
                    break

            # Update terminal size
            width, height = renderer.get_terminal_size()

            # Calculate beat intensity
            scene_name = director.get_current_scene_name() or "intro"
            scene_mood = "dreamy"
            if scene_name == "fireworks":
                scene_mood = "celebration"
            elif scene_name == "heartbeat":
                scene_mood = "romantic"
            elif scene_name == "matrix_rain":
                scene_mood = "tech/cool"
            elif scene_name == "waveform":
                scene_mood = "energetic"

            beat_intensity = get_beat_intensity(current_time, scene_mood)

            # Create scene context
            scene_time = current_time - director.scene_start_time
            context = SceneContext(
                console_width=width,
                console_height=height,
                song_time=current_time,
                scene_time=scene_time,
                beat_intensity=beat_intensity,
                is_transitioning=director.next_scene_name is not None
            )

            # Update director
            director.state.current_time = current_time
            director.check_scene_triggers(current_time)
            director.update_lyric(current_time)

            # Update visualizer
            if not is_paused:
                visualizer.update(FRAME_TIME, beat_intensity)

            # Update scenes
            if not is_paused:
                director.update_scenes(FRAME_TIME, context)

            # Get lyric text
            lyric_text = None
            if director.state.current_lyric:
                lyric_text = director.state.current_lyric.text

            # Build and render frame
            frame_content = build_frame(
                renderer=renderer,
                director=director,
                visualizer=visualizer,
                lyric_text=lyric_text,
                beat_intensity=beat_intensity,
                width=width,
                height=height
            )

            # Update Live display
            renderer.update_display(frame_content)

            # Frame timing
            frame_time = time.time() - frame_start
            sleep_time = FRAME_TIME - frame_time
            if sleep_time > 0:
                time.sleep(sleep_time)

            frame_count += 1

    except KeyboardInterrupt:
        # Clean exit on Ctrl+C
        pass
    except Exception as e:
        console.print(f"[red]Error during experience: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Stop Live display
        renderer.stop_live()

        # Stop audio
        if audio_manager:
            audio_manager.stop()

    return experience_complete


def run_finale_sequence(renderer: Renderer, console: Console, lyric_map: Optional[LyricMap]) -> None:
    """
    Run the finale sequence with closing message.

    Shows a static version of SceneFinale - same message, same aesthetic,
    with "Press Enter to exit" prompt. This feels like the animation
    "settles" into the final screen.

    Args:
        renderer: Renderer instance
        console: Rich Console
        lyric_map: LyricMap containing finale_message
    """
    from rich.align import Align
    from rich.text import Text
    from rich.panel import Panel

    # Get finale message
    finale_message = "Forever yours,\nAhsan ♥"
    if lyric_map and hasattr(lyric_map, 'finale_message'):
        finale_message = lyric_map.finale_message

    # Stop Live first
    renderer.stop_live()

    # Build the finale text
    finale_text = Text()
    finale_text.append("♥ ♥ ♥", style="pink1")
    finale_text.append("\n\n")
    for line in finale_message.split('\n'):
        finale_text.append(line, style="pink1")
        finale_text.append("\n")

    # Center everything using Align
    centered_finale = Align.center(finale_text, vertical="middle")

    # Build prompt
    prompt = Align.center(Text("Press Enter to exit...", style="dim"))

    # Build "made by" credit
    credit = Align.center(Text("made by ahsan", style="dim"))

    # Clear and print
    console.clear()
    console.print(centered_finale)
    console.print()
    console.print(prompt)
    console.print(credit)

    # Wait for Enter
    try:
        input()
    except (KeyboardInterrupt, EOFError):
        pass


def main(lyrics_path: Optional[Path] = None, audio_path: Optional[Path] = None) -> int:
    """
    Main entry point for Nina's Beats.

    Args:
        lyrics_path: Optional path to lyrics.json
        audio_path: Optional path to audio.mp3

    Returns:
        Exit code (0 = success, 1 = error)
    """
    # Resolve paths
    lyrics_path = lyrics_path or DEFAULT_LYRICS_PATH
    audio_path = audio_path or DEFAULT_AUDIO_PATH

    # Initialize console
    console = Console()

    # Load assets
    lyric_map, resolved_audio_path = load_assets(lyrics_path, audio_path)
    if lyric_map is None:
        return 1

    # Initialize components
    try:
        director = Director(lyric_map)
        renderer = Renderer()
        visualizer = SpectrumVisualizer()
        input_handler = NonBlockingInput()

        # Register all scenes
        director.register_scene("intro", SceneIntro)
        director.register_scene("starfield", SceneStarfield)
        director.register_scene("matrix_rain", SceneMatrixRain)
        director.register_scene("fireworks", SceneFireworks)
        director.register_scene("heartbeat", SceneHeartbeat)
        director.register_scene("waveform", SceneWaveform)
        director.register_scene("finale", SceneFinale)

    except Exception as e:
        console.print(f"[red]Failed to initialize: {e}[/red]")
        import traceback
        traceback.print_exc()
        return 1

    # Create audio manager
    audio_manager = None
    if resolved_audio_path:
        try:
            audio_manager = AudioManager(resolved_audio_path)
        except Exception as e:
            console.print(f"[yellow]Could not initialize audio: {e}[/yellow]")

    # Run main loop
    experience_complete = run_main_loop(
        director=director,
        audio_manager=audio_manager,
        renderer=renderer,
        visualizer=visualizer,
        console=console,
        input_handler=input_handler
    )

    # Run finale
    if experience_complete:
        run_finale_sequence(renderer, console, lyric_map)

    # Cleanup
    console.clear()
    return 0


def cli_entry_point() -> None:
    """
    CLI entry point for the ninas-beats command.

    Parses command-line arguments and starts the experience.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Nina's Beats (Symphony Edition) - A terminal audio-visual love experience"
    )
    parser.add_argument(
        "--lyrics",
        type=Path,
        default=None,
        help="Path to lyrics.json file (default: assets/lyrics.json)"
    )
    parser.add_argument(
        "--audio",
        type=Path,
        default=None,
        help="Path to audio.mp3 file (default: assets/audio.mp3)"
    )

    args = parser.parse_args()

    # Run main
    sys.exit(main(lyrics_path=args.lyrics, audio_path=args.audio))


if __name__ == "__main__":
    cli_entry_point()
