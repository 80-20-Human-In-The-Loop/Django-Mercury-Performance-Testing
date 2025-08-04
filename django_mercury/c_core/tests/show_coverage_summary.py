#!/usr/bin/env python3
"""Show colored coverage summary for source files."""

import os
import re
import sys

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


def strip_ansi_codes(text):
    """Remove ANSI escape codes from text."""
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


def parse_coverage_summary(coverage_file):
    """Parse coverage summary and extract file coverage data."""
    coverage_data = []

    try:
        with open(coverage_file, "r") as f:
            content = f.read()

        # Strip ANSI codes for parsing
        clean_content = strip_ansi_codes(content)

        # Find all source file coverage entries
        source_files = [
            "common.c",
            "query_analyzer.c",
            "metrics_engine.c",
            "test_orchestrator.c",
            "performance_monitor.c",
        ]

        for source in source_files:
            # Look for pattern: File 'filename.c'\nLines executed:XX.XX% of YYY
            pattern = f"File '{source}'.*?Lines executed:([0-9.]+)% of ([0-9]+)"
            match = re.search(pattern, clean_content, re.DOTALL)

            if match:
                percentage = float(match.group(1))
                total_lines = int(match.group(2))
                covered_lines = int(total_lines * percentage / 100)
                coverage_data.append(
                    {
                        "file": source,
                        "percentage": percentage,
                        "covered": covered_lines,
                        "total": total_lines,
                    }
                )
    except Exception as e:
        print(f"Error reading coverage summary: {e}", file=sys.stderr)
        return []

    return coverage_data


def print_colored_summary(coverage_data):
    """Print coverage summary with colors."""
    if not coverage_data:
        print("No coverage data found")
        return

    # Calculate maximum filename length for alignment
    max_filename_len = max(len(item["file"]) for item in coverage_data)

    for item in coverage_data:
        file_name = item["file"].ljust(max_filename_len + 2)
        percentage = item["percentage"]
        color = get_color(percentage)

        # Format the output with color
        print(
            f"File '{file_name}' {color}{percentage:6.2f}%{RESET} ({item['covered']}/{item['total']} lines)"
        )


def main():
    coverage_dir = os.path.join(os.path.dirname(__file__), "coverage")
    coverage_file = os.path.join(coverage_dir, "coverage_summary.txt")

    if not os.path.exists(coverage_file):
        print("Coverage summary file not found. Run 'make coverage' first.")
        return 1

    coverage_data = parse_coverage_summary(coverage_file)
    print_colored_summary(coverage_data)

    # Print summary statistics
    if coverage_data:
        print()
        total_lines = sum(item["total"] for item in coverage_data)
        covered_lines = sum(item["covered"] for item in coverage_data)
        overall_percentage = (covered_lines / total_lines * 100) if total_lines > 0 else 0

        color = get_color(overall_percentage)
        print(
            f"{BOLD}Overall Coverage: {color}{overall_percentage:.1f}%{RESET} ({covered_lines}/{total_lines} lines)"
        )

        # Count files by coverage level
        excellent = sum(1 for item in coverage_data if item["percentage"] >= 80)
        good = sum(1 for item in coverage_data if 50 <= item["percentage"] < 80)
        poor = sum(1 for item in coverage_data if item["percentage"] < 50)

        if excellent > 0:
            print(f"  {GREEN}Excellent (≥80%):{RESET} {excellent} files")
        if good > 0:
            print(f"  {YELLOW}Good (50-79%):{RESET} {good} files")
        if poor > 0:
            print(f"  {RED}Needs Work (<50%):{RESET} {poor} files")

    return 0


if __name__ == "__main__":
    sys.exit(main())
