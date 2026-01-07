"""
Audio management for Nina's Beats.

Handles audio playback via mpv subprocess and time tracking for synchronization.
"""
import subprocess
import time
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class AudioState:
    """Current state of audio playback."""
    is_playing: bool = False
    is_paused: bool = False
    current_time: float = 0.0
    duration: float = 0.0
    has_error: bool = False


class AudioManager:
    """Manages audio playback via mpv subprocess."""

    def __init__(self, audio_path: Path):
        """
        Initialize audio manager.

        Args:
            audio_path: Path to audio file (MP3 expected)

        Raises:
            FileNotFoundError: If audio file doesn't exist
        """
        self.audio_path = audio_path
        self.process: Optional[subprocess.Popen] = None
        self.start_time: float = 0.0
        self.pause_start: float = 0.0
        self.total_paused: float = 0.0
        self.state = AudioState()

        # Verify mpv is available
        self._mpv_available = shutil.which("mpv") is not None

    def start(self) -> AudioState:
        """
        Start audio playback.

        Returns:
            AudioState with is_playing=True, current_time=0.0

        Behavior:
        - Launches mpv in subprocess with --no-video --really-quiet
        - Records wall clock start time for time tracking
        - If mpv not found, sets has_error=True but doesn't raise
        """
        if not self._mpv_available:
            self.state.has_error = True
            return self.state

        if not self.audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {self.audio_path}")

        try:
            self.process = subprocess.Popen([
                "mpv",
                "--no-video",
                "--really-quiet",
                "--msg-level=all=error",
                "--pause=no",
                "--loop=no",
                str(self.audio_path)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)

            self.start_time = time.time()
            self.total_paused = 0.0
            self.state.is_playing = True
            self.state.is_paused = False
            self.state.has_error = False

        except Exception as e:
            self.state.has_error = True
            # Log error for debugging
            self._log_error(f"Failed to start mpv: {e}")

        return self.state

    def pause(self) -> AudioState:
        """
        Pause audio playback.

        Returns:
            AudioState with is_paused=True

        Behavior:
        - Sends SIGSTOP to mpv process
        - Records pause start time for drift correction
        - If process not running, no-op
        """
        if self.process and self._mpv_available:
            try:
                self.process.send_signal(18)  # SIGSTOP
                self.pause_start = time.time()
                self.state.is_paused = True
            except Exception:
                pass

        return self.state

    def resume(self) -> AudioState:
        """
        Resume audio playback.

        Returns:
            AudioState with is_paused=False

        Behavior:
        - Sends SIGCONT to mpv process
        - Adds pause duration to total_paused
        - If process not running, no-op
        """
        if self.process and self._mpv_available:
            try:
                self.process.send_signal(19)  # SIGCONT
                if self.pause_start > 0:
                    self.total_paused += time.time() - self.pause_start
                    self.pause_start = 0.0
                self.state.is_paused = False
            except Exception:
                pass

        return self.state

    def stop(self) -> None:
        """
        Stop audio playback and cleanup.

        Behavior:
        - Terminates mpv process gracefully (SIGTERM)
        - Waits up to 1 second for cleanup
        - Force kills (SIGKILL) if still running
        """
        if self.process:
            try:
                self.process.terminate()
                try:
                    self.process.wait(timeout=1.0)
                except subprocess.TimeoutExpired:
                    self.process.kill()
            except Exception:
                pass
            finally:
                self.process = None

        self.state.is_playing = False

    def get_time(self) -> float:
        """
        Get current playback position in seconds.

        Returns:
            Current time in seconds (0.0 to duration)

        Calculation:
            elapsed = wall_time - start_time - total_paused
            If paused, subtract (wall_time - pause_start)
        """
        if self.state.is_paused and self.pause_start > 0:
            # Freeze time during pause
            elapsed = self.pause_start - self.start_time - self.total_paused
        else:
            elapsed = time.time() - self.start_time - self.total_paused

        return max(0.0, elapsed)

    def get_state(self) -> AudioState:
        """
        Get current audio state.

        Returns:
            AudioState with all fields populated
        """
        self.state.current_time = self.get_time()
        return self.state

    def _log_error(self, message: str) -> None:
        """Log error to file for debugging."""
        try:
            log_dir = Path.home() / ".ninas-beats"
            log_dir.mkdir(exist_ok=True)
            with open(log_dir / "errors.log", "a") as f:
                f.write(f"{time.ctime()}: {message}\n")
        except Exception:
            pass
