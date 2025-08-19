#!/usr/bin/env python3
"""
Quick Learn Plugin Test Runner

Simple wrapper to run the learn plugin tests using the existing test infrastructure.
"""

import subprocess
import sys
import os
from pathlib import Path


def main():
    """Run learn plugin tests using pytest with proper environment."""
    project_root = Path(__file__).parent
    venv_python = project_root / "venv" / "bin" / "python"

    # Use venv Python if available, otherwise system Python
    python_cmd = str(venv_python) if venv_python.exists() else sys.executable

    # Set up environment
    env = os.environ.copy()
    env["DJANGO_SETTINGS_MODULE"] = "tests.config.test_settings"

    # Build pytest command
    cmd = [python_cmd, "-m", "pytest", "tests/cli/plugins/", "-v", "--tb=short"]

    # Handle arguments
    if len(sys.argv) > 1:
        if "--coverage" in sys.argv:
            cmd.extend(["--cov=django_mercury.cli.plugins", "--cov-report=term-missing"])
        if "--quiet" in sys.argv:
            cmd = [c for c in cmd if c != "-v"]  # Remove verbose

    print("🎓 Running Learn Plugin Tests")
    print(f"🐍 Python: {python_cmd}")
    print(f"📁 Directory: {project_root}")
    print("=" * 50)

    # Run the tests
    try:
        result = subprocess.run(cmd, cwd=project_root, env=env)
        return result.returncode
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted")
        return 130


if __name__ == "__main__":
    sys.exit(main())
