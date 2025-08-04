#!/usr/bin/env python3
"""Colorize gcov output based on coverage percentages."""

import sys
import re

# ANSI color codes
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RESET = "\033[0m"
BOLD = "\033[1m"


def get_color(percentage):
    """Get color based on coverage percentage."""
    if percentage < 50:
        return RED
    elif percentage < 80:
        return YELLOW
    else:
        return GREEN


def colorize_line(line):
    """Add color to lines containing coverage percentages."""
    # Match "Lines executed:XX.XX% of YYY"
    match = re.search(r"Lines executed:(\d+\.\d+)%", line)
    if match:
        percentage = float(match.group(1))
        color = get_color(percentage)
        # Replace the percentage with colored version
        colored_percentage = f"{color}{match.group(1)}%{RESET}"
        return line.replace(f"{match.group(1)}%", colored_percentage)

    # Match "Branches executed:XX.XX% of YYY"
    match = re.search(r"Branches executed:(\d+\.\d+)%", line)
    if match:
        percentage = float(match.group(1))
        color = get_color(percentage)
        colored_percentage = f"{color}{match.group(1)}%{RESET}"
        return line.replace(f"{match.group(1)}%", colored_percentage)

    # Match "Taken at least once:XX.XX% of YYY"
    match = re.search(r"Taken at least once:(\d+\.\d+)%", line)
    if match:
        percentage = float(match.group(1))
        color = get_color(percentage)
        colored_percentage = f"{color}{match.group(1)}%{RESET}"
        return line.replace(f"{match.group(1)}%", colored_percentage)

    # Match "Calls executed:XX.XX% of YYY"
    match = re.search(r"Calls executed:(\d+\.\d+)%", line)
    if match:
        percentage = float(match.group(1))
        color = get_color(percentage)
        colored_percentage = f"{color}{match.group(1)}%{RESET}"
        return line.replace(f"{match.group(1)}%", colored_percentage)

    # Highlight file names
    if line.startswith("File '") and line.endswith("'"):
        return f"{BOLD}{line}{RESET}"

    return line


def main():
    """Read from stdin and colorize output."""
    for line in sys.stdin:
        print(colorize_line(line.rstrip()))


if __name__ == "__main__":
    main()
