"""
Lyric synchronization module for Nina's Beats.

Handles loading lyrics from JSON and looking up the current lyric
based on playback time.
"""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List


@dataclass
class LyricEntry:
    """A single lyric with timestamp and optional scene trigger."""

    time: float  # Time in seconds when this lyric appears
    text: str  # Lyric text to display (empty string for scene-only triggers)
    scene: Optional[str]  # Scene class name to trigger (e.g., "fireworks", None = no change)

    def __post_init__(self):
        if self.time < 0:
            raise ValueError("Lyric time cannot be negative")


class LyricMap:
    """Sorted collection of lyrics with binary search lookup."""

    def __init__(self, entries: List[LyricEntry], duration: float = 180.0, finale_message: str = "Forever yours,\nAhsan ♥"):
        """
        Initialize with a list of lyric entries.

        Args:
            entries: List of LyricEntry objects (will be sorted by time)
            duration: Song duration in seconds (default 3 minutes)
            finale_message: Closing message displayed at the end
        """
        # Sort by time to enable efficient lookup
        self.entries = sorted(entries, key=lambda e: e.time)
        self.duration = duration
        self.finale_message = finale_message

    @classmethod
    def from_json(cls, path: Path) -> "LyricMap":
        """
        Load lyrics from a JSON file.

        Args:
            path: Path to lyrics.json file

        Returns:
            LyricMap with loaded entries
        """
        with open(path, "r") as f:
            data = json.load(f)

        entries = []
        for item in data.get("lyrics", []):
            entries.append(LyricEntry(
                time=item["time"],
                text=item["text"],
                scene=item.get("scene")
            ))

        duration = data.get("duration_seconds", 180.0)
        finale_message = data.get("finale_message", "Forever yours,\nAhsan ♥")

        return cls(entries, duration=duration, finale_message=finale_message)

    def get_lyric_at(self, time: float) -> Optional[LyricEntry]:
        """
        Return the active lyric at given time (exact or most recent past).

        Args:
            time: Current playback time in seconds

        Returns:
            The most recent LyricEntry, or None if time is before first lyric
        """
        # Find the most recent lyric whose time <= current time
        for i, entry in enumerate(self.entries):
            if entry.time > time:
                # Previous entry is the active one
                return self.entries[i - 1] if i > 0 else None
        # If we didn't exceed any time, return the last entry
        return self.entries[-1] if self.entries else None

    def get_scene_trigger(self, time: float) -> Optional[str]:
        """
        Return the most recent scene trigger that should have fired by this time.

        Unlike get_lyric_at() which returns the active lyric, this returns a scene
        ONLY when we've crossed a new scene boundary (to avoid re-triggering).

        Args:
            time: Current playback time in seconds

        Returns:
            Scene name if we've crossed a new scene trigger, None otherwise
        """
        # Track which scene we last triggered to avoid re-triggering
        if not hasattr(self, '_last_triggered_scene_time'):
            self._last_triggered_scene_time = -1.0

        for entry in reversed(self.entries):  # Check from most recent to oldest
            if entry.scene and entry.time <= time:
                # We found a scene trigger that we've passed
                # Only return it if we haven't already triggered it
                if entry.time > self._last_triggered_scene_time:
                    self._last_triggered_scene_time = entry.time
                    return entry.scene
                break  # Found the most recent, no need to check older ones

        return None

    def get_finale_message(self) -> str:
        """
        Get the finale message from the loaded lyrics.

        Returns:
            The finale message string
        """
        return self.finale_message
