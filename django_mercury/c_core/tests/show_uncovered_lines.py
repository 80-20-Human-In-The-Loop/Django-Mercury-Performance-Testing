#!/usr/bin/env python3
"""Show random uncovered lines from each source file."""

import os
import random
import re

# ANSI color codes
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RESET = "\033[0m"


def find_uncovered_lines(gcov_file):
    """Find all uncovered lines in a gcov file."""
    uncovered = []
    with open(gcov_file, "r") as f:
        for line in f:
            # Lines marked with ##### are never executed
            if line.strip().startswith("#####:"):
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    line_num = parts[1].strip()
                    code = parts[2].rstrip()
                    # Skip empty lines, braces, and comments
                    if code.strip() and not code.strip() in ["{", "}", "/*", "*/", "*/"]:
                        uncovered.append((int(line_num), code))
    return uncovered


def strip_ansi_codes(text):
    """Remove ANSI escape codes from text."""
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


def get_coverage_percentage(coverage_file, source_file):
    """Extract coverage percentage from coverage summary."""
    try:
        with open(coverage_file, "r") as f:
            content = f.read()
            # Strip ANSI codes for parsing
            clean_content = strip_ansi_codes(content)
            # Look for the file and its coverage
            pattern = f"File '{source_file}'.*?Lines executed:([0-9.]+)%"
            match = re.search(pattern, clean_content, re.DOTALL)
            if match:
                return float(match.group(1))
    except:
        pass
    return None


def get_color(percentage):
    """Get color based on coverage percentage."""
    if percentage < 50:
        return RED
    elif percentage < 80:
        return YELLOW
    else:
        return GREEN


def main():
    coverage_dir = os.path.join(os.path.dirname(__file__), "coverage")
    source_files = [
        "common.c",
        "query_analyzer.c",
        "metrics_engine.c",
        "test_orchestrator.c",
        "performance_monitor.c",
    ]

    for source in source_files:
        gcov_file = os.path.join(coverage_dir, f"{source}.gcov")
        if os.path.exists(gcov_file):
            coverage = get_coverage_percentage(
                os.path.join(coverage_dir, "coverage_summary.txt"), source
            )

            if coverage is not None and coverage < 100:
                uncovered = find_uncovered_lines(gcov_file)
                if uncovered:
                    # Pick a random uncovered line
                    line_num, code = random.choice(uncovered)
                    color = get_color(coverage)
                    print(
                        f"📍 {source} ({color}{coverage:.1f}%{RESET} covered) - Sample uncovered line:"
                    )
                    print(f"   Line {line_num}:{code}")
                    print()


if __name__ == "__main__":
    main()
