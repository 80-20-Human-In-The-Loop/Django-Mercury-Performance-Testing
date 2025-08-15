"""
Utility functions for visual progress display.
"""

from collections import deque


def format_time(seconds: float) -> str:
    """Format time in human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.0f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def create_sparkline(data: deque, width: int = 20) -> str:
    """Create a simple ASCII sparkline from data."""
    if not data or len(data) < 2:
        return "—" * width

    # Normalize data to 0-7 range (8 levels)
    min_val = min(data)
    max_val = max(data)
    range_val = max_val - min_val if max_val != min_val else 1

    # Sparkline characters
    chars = "▁▂▃▄▅▆▇█"

    # Sample data if too long
    if len(data) > width:
        step = len(data) // width
        sampled = [data[i] for i in range(0, len(data), step)][:width]
    else:
        sampled = list(data)

    # Convert to sparkline
    sparkline = ""
    for value in sampled:
        normalized = (value - min_val) / range_val
        index = min(int(normalized * 7), 7)
        sparkline += chars[index]

    return sparkline


def show_simple_progress(test_name: str, current: int, total: int):
    """Show simple text-based progress for terminals without rich support."""
    percent = (current / max(total, 1)) * 100
    bar_length = 40
    filled = int(bar_length * current // max(total, 1))
    bar = "█" * filled + "░" * (bar_length - filled)

    # Use carriage return to update the same line
    print(f"\r[{bar}] {percent:.1f}% - {test_name[:30]}", end="", flush=True)
