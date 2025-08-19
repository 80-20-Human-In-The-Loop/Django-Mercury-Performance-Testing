"""
Smart Discovery Plugin for Mercury-Test CLI

Implements intelligent 3-tier manage.py discovery:
1. Fast search: Current directory + parents (instant)
2. Smart patterns: Sibling app directories (common Django patterns)
3. Deep search: All subdirectories with progress (comprehensive)
"""

import os
import json
from pathlib import Path
from argparse import ArgumentParser, Namespace
from typing import Optional, List

from django_mercury.cli.plugins.base import MercuryPlugin

# Try to import rich for progress bars
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class SmartDiscoveryPlugin(MercuryPlugin):
    """Plugin for intelligent manage.py discovery with caching."""

    name = "discovery"
    description = "Intelligent manage.py discovery with caching"
    priority = 10  # High priority - runs early
    version = "1.0.0"

    # Audience targeting
    audiences = ["student", "expert"]  # Helpful for both audiences
    complexity_level = 1  # Simple to use
    requires_capabilities = []  # No special requirements
    # NOTE: Must be explicitly enabled in config due to cwd constraints

    def __init__(self):
        super().__init__()
        self.cache_dir = Path.home() / ".mercury" / "cache"
        self.cache_file = self.cache_dir / "manage_py_locations.json"
        self.invalid_files_found = []  # Track invalid manage.py files for error reporting
        self._ensure_cache_dir()

    def _ensure_cache_dir(self):
        """Ensure cache directory exists."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register discovery-related arguments."""
        parser.add_argument(
            "--search-deep",
            action="store_true",
            help="Search all subdirectories for manage.py (slower but comprehensive)",
        )

        parser.add_argument(
            "--no-cache", action="store_true", help="Skip location caching for this run"
        )

        parser.add_argument(
            "--clear-cache", action="store_true", help="Clear cached manage.py locations and exit"
        )

        parser.add_argument(
            "--show-search", action="store_true", help="Show detailed search process"
        )

    def can_handle(self, args: Namespace) -> bool:
        """Handle --clear-cache command."""
        return args.clear_cache

    def execute(self, args: Namespace) -> int:
        """Execute cache clearing."""
        if args.clear_cache:
            self._clear_cache()
            print("✅ Cleared manage.py location cache")
            return 0
        return 0

    def enhance_discovery(self, current_search):
        """Replace basic discovery with smart 3-tier search."""

        def smart_discovery(args=None):
            return self.smart_find_manage_py(args)

        return smart_discovery

    def smart_find_manage_py(self, args: Optional[Namespace] = None) -> Optional[str]:
        """Intelligent 3-tier manage.py discovery.

        Args:
            args: Command line arguments (optional)

        Returns:
            Path to manage.py or None if not found
        """
        if args is None:
            # Create minimal args if not provided
            from argparse import Namespace

            args = Namespace(search_deep=False, no_cache=False, show_search=False)

        search_deep = getattr(args, "search_deep", False)
        use_cache = not getattr(args, "no_cache", False)
        show_search = getattr(args, "show_search", False)

        # Reset invalid files tracking for this search
        self.invalid_files_found = []

        current_dir = Path.cwd()

        if show_search and RICH_AVAILABLE:
            console = Console()
            console.print("🔍 Searching for Django project...")
        elif show_search:
            print("🔍 Searching for Django project...")

        # Tier 1: Check cache first
        if use_cache:
            cached_location = self._get_cached_location(current_dir)
            if cached_location and self._verify_manage_py(cached_location):
                if show_search:
                    self._show_search_result("Cache", "✅", cached_location)
                return str(cached_location)
            elif show_search:
                self._show_search_result("Cache", "❌")

        # Tier 2: Fast search (current + parents)
        location = self._search_current_and_parents(current_dir, show_search)
        if location:
            if use_cache:
                self._cache_location(current_dir, location)
            return str(location)

        # Tier 3: Smart patterns (sibling directories)
        location = self._search_sibling_patterns(current_dir, show_search)
        if location:
            if use_cache:
                self._cache_location(current_dir, location)
            return str(location)

        # Tier 4: Deep search (if requested)
        if search_deep:
            location = self._search_children_with_progress(current_dir, show_search)
            if location:
                if use_cache:
                    self._cache_location(current_dir, location)
                return str(location)

        # Not found
        if show_search:
            self._show_not_found_help(search_deep)

        return None

    def _search_current_and_parents(
        self, start_dir: Path, show_search: bool = False
    ) -> Optional[Path]:
        """Search current directory and parents."""
        current = start_dir

        for level in range(5):  # Check up to 5 levels up
            # First check direct manage.py in current directory
            manage_path = current / "manage.py"
            if manage_path.exists():
                if self._verify_manage_py(manage_path):
                    if show_search:
                        location = (
                            "Current directory"
                            if level == 0
                            else f"Parent directory (level {level})"
                        )
                        self._show_search_result(location, "✅", manage_path)
                    return manage_path
                else:
                    # Track invalid manage.py file
                    self.invalid_files_found.append(manage_path)
                    if show_search:
                        location = (
                            "Current directory"
                            if level == 0
                            else f"Parent directory (level {level})"
                        )
                        self._show_search_result(
                            location, "⚠️", f"Invalid manage.py at {manage_path}"
                        )

            # If at level 0 (current directory), also check common Django patterns
            if level == 0:
                pattern_result = self._search_current_directory_patterns(current, show_search)
                if pattern_result:
                    return pattern_result

            current = current.parent
            if current == current.parent:  # Reached root
                break

        if show_search:
            self._show_search_result("Current + parent directories", "❌")

        return None

    def _search_current_directory_patterns(
        self, current_dir: Path, show_search: bool = False
    ) -> Optional[Path]:
        """Search common Django project patterns in current directory."""
        found_any = False

        # First check immediate subdirectories
        try:
            for item in current_dir.iterdir():
                if item.is_dir():
                    manage_path = item / "manage.py"
                    if manage_path.exists():
                        # Ensure this path is actually a child of current_dir
                        try:
                            relative_path = manage_path.relative_to(current_dir)
                            # Additional check: ensure it's only 2 levels deep (subdir/manage.py)
                            if len(relative_path.parts) > 2:
                                continue

                            # Additional check: ensure the parent directory is an immediate child
                            if relative_path.parts[0] != item.name:
                                continue

                        except ValueError:
                            # Path is not relative to current_dir, skip it
                            continue

                        if self._verify_manage_py(manage_path):
                            if show_search:
                                self._show_search_result(
                                    "Current directory subdirectories", "✅", manage_path
                                )
                            return manage_path
                        else:
                            found_any = True
                            self.invalid_files_found.append(manage_path)
                            if show_search:
                                self._show_search_result(
                                    "Current directory subdirectories",
                                    "⚠️",
                                    f"Invalid manage.py at {manage_path}",
                                )
        except (PermissionError, OSError):
            pass

        # Then check specific common patterns (but constrained to current directory)
        common_patterns = [
            "backend/manage.py",
            "src/manage.py",
            "app/manage.py",
            "django_app/manage.py",
            "project/manage.py",
        ]

        for pattern in common_patterns:
            pattern_path = current_dir / pattern
            if pattern_path.exists():
                # Double-check it's actually within current_dir
                try:
                    pattern_path.relative_to(current_dir)
                except ValueError:
                    continue

                if self._verify_manage_py(pattern_path):
                    if show_search:
                        self._show_search_result(
                            f"Current directory pattern ({pattern})", "✅", pattern_path
                        )
                    return pattern_path
                else:
                    found_any = True
                    self.invalid_files_found.append(pattern_path)
                    if show_search:
                        self._show_search_result(
                            f"Current directory pattern ({pattern})",
                            "⚠️",
                            f"Invalid manage.py at {pattern_path}",
                        )

        # Finally check nested backend patterns
        backend_nested_patterns = [
            "backend/*/manage.py",
            "src/*/manage.py",
        ]

        for pattern in backend_nested_patterns:
            try:
                # Use resolve() to ensure we get absolute paths, then check they're within current_dir
                matches = list(current_dir.glob(pattern))
                for match in matches:
                    if match.exists():
                        # Ensure this match is actually within current_dir
                        try:
                            match.relative_to(current_dir)
                        except ValueError:
                            # Skip matches outside current directory
                            continue

                        if self._verify_manage_py(match):
                            if show_search:
                                self._show_search_result(
                                    f"Current directory pattern ({pattern})", "✅", match
                                )
                            return match
                        else:
                            found_any = True
                            self.invalid_files_found.append(match)
                            if show_search:
                                self._show_search_result(
                                    f"Current directory pattern ({pattern})",
                                    "⚠️",
                                    f"Invalid manage.py at {match}",
                                )
            except (PermissionError, OSError):
                continue

        if show_search and not found_any:
            self._show_search_result("Current directory patterns", "❌")

        return None

    def _search_sibling_patterns(
        self, start_dir: Path, show_search: bool = False
    ) -> Optional[Path]:
        """Search common Django app patterns (sibling directories)."""
        parent = start_dir.parent

        # Common patterns where manage.py might be
        patterns = [
            parent,  # One level up
            parent.parent,  # Two levels up
        ]

        # Check sibling directories for Django project structure
        try:
            for sibling in parent.iterdir():
                if sibling.is_dir() and sibling != start_dir:
                    patterns.append(sibling)
        except (PermissionError, OSError):
            pass

        for pattern_dir in patterns:
            if pattern_dir.is_dir():
                manage_path = pattern_dir / "manage.py"
                if manage_path.exists():
                    if self._verify_manage_py(manage_path):
                        if show_search:
                            self._show_search_result("Sibling app directories", "✅", manage_path)
                        return manage_path
                    else:
                        # Track invalid manage.py file
                        self.invalid_files_found.append(manage_path)
                        if show_search:
                            self._show_search_result(
                                "Sibling app directories",
                                "⚠️",
                                f"Invalid manage.py at {manage_path}",
                            )

        if show_search:
            self._show_search_result("Sibling app directories", "❌")

        return None

    def _search_children_with_progress(
        self, start_dir: Path, show_search: bool = False
    ) -> Optional[Path]:
        """Search all child directories with progress indicator."""
        if show_search:
            if RICH_AVAILABLE:
                return self._search_children_rich_progress(start_dir)
            else:
                return self._search_children_simple_progress(start_dir)
        else:
            return self._search_children_no_progress(start_dir)

    def _search_children_rich_progress(self, start_dir: Path) -> Optional[Path]:
        """Search children with rich progress bar."""
        # First, count directories
        dirs_to_search = list(self._get_searchable_dirs(start_dir))

        if not dirs_to_search:
            self._show_search_result("Subdirectories", "❌", "No searchable directories")
            return None

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=Console(),
        ) as progress:

            task = progress.add_task("Searching subdirectories...", total=len(dirs_to_search))

            for i, directory in enumerate(dirs_to_search):
                progress.update(task, description=f"Searching subdirectories... ({directory.name})")

                manage_path = directory / "manage.py"
                if manage_path.exists():
                    if self._verify_manage_py(manage_path):
                        progress.update(task, completed=len(dirs_to_search))
                        self._show_search_result("Subdirectories", "✅", manage_path)
                        return manage_path
                    else:
                        # Track invalid manage.py file but continue searching
                        self.invalid_files_found.append(manage_path)

                progress.advance(task)

        self._show_search_result(
            "Subdirectories", "❌", f"Searched {len(dirs_to_search)} directories"
        )
        return None

    def _search_children_simple_progress(self, start_dir: Path) -> Optional[Path]:
        """Search children with simple text progress."""
        dirs_to_search = list(self._get_searchable_dirs(start_dir))

        if not dirs_to_search:
            self._show_search_result("Subdirectories", "❌", "No searchable directories")
            return None

        total = len(dirs_to_search)

        for i, directory in enumerate(dirs_to_search):
            if i % 10 == 0:  # Update every 10 directories
                percent = (i / total) * 100
                print(f"├─ Searching subdirectories... {percent:.0f}% ({i}/{total})")

            manage_path = directory / "manage.py"
            if manage_path.exists():
                if self._verify_manage_py(manage_path):
                    self._show_search_result("Subdirectories", "✅", manage_path)
                    return manage_path
                else:
                    # Track invalid manage.py file but continue searching
                    self.invalid_files_found.append(manage_path)

        self._show_search_result("Subdirectories", "❌", f"Searched {total} directories")
        return None

    def _search_children_no_progress(self, start_dir: Path) -> Optional[Path]:
        """Search children without progress indicator."""
        for directory in self._get_searchable_dirs(start_dir):
            manage_path = directory / "manage.py"
            if manage_path.exists():
                if self._verify_manage_py(manage_path):
                    return manage_path
                else:
                    # Track invalid manage.py file but continue searching
                    self.invalid_files_found.append(manage_path)

        return None

    def _get_searchable_dirs(self, start_dir: Path):
        """Get all searchable directories (excluding common non-project dirs)."""
        exclude_dirs = {
            ".git",
            ".hg",
            ".svn",
            "__pycache__",
            ".venv",
            "venv",
            "env",
            "node_modules",
            ".tox",
            ".pytest_cache",
            "htmlcov",
            ".coverage",
            ".mypy_cache",
            ".idea",
            ".vscode",
            "build",
            "dist",
            "*.egg-info",
        }

        try:
            for item in start_dir.rglob("*"):
                if (
                    item.is_dir()
                    and item.name not in exclude_dirs
                    and not item.name.startswith(".")
                    and item != start_dir
                ):
                    yield item
        except (PermissionError, OSError):
            # Skip directories we can't access
            pass

    def _verify_manage_py(self, path: Path) -> bool:
        """Verify that the path points to a valid Django manage.py file."""
        if not path.exists():
            return False

        if path.name != "manage.py":
            return False

        try:
            # Read file content
            content = path.read_text(encoding="utf-8", errors="ignore")

            # Check if file is valid Python syntax
            compile(content, str(path), "exec")

            # Check for Django-specific content
            content_lower = content.lower()
            has_django = "django" in content_lower
            has_execute = "execute_from_command_line" in content
            has_settings = "django_settings_module" in content_lower

            return has_django and has_execute and has_settings

        except (OSError, UnicodeError, SyntaxError):
            return False

    def _get_cached_location(self, current_dir: Path) -> Optional[Path]:
        """Get cached manage.py location for current directory."""
        if not self.cache_file.exists():
            return None

        try:
            with open(self.cache_file, "r") as f:
                cache_data = json.load(f)

            cache_key = str(current_dir)
            if cache_key in cache_data:
                cached_path = Path(cache_data[cache_key])
                return cached_path
        except (json.JSONDecodeError, KeyError, OSError):
            pass

        return None

    def _cache_location(self, current_dir: Path, manage_py_path: Path) -> None:
        """Cache the manage.py location for faster future runs."""
        cache_data = {}

        # Load existing cache
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r") as f:
                    cache_data = json.load(f)
            except (json.JSONDecodeError, OSError):
                pass

        # Update cache
        cache_key = str(current_dir)
        cache_data[cache_key] = str(manage_py_path)

        # Save cache
        try:
            with open(self.cache_file, "w") as f:
                json.dump(cache_data, f, indent=2)
        except OSError:
            pass  # Fail silently if can't write cache

    def _clear_cache(self) -> None:
        """Clear the location cache."""
        if self.cache_file.exists():
            self.cache_file.unlink()

    def _show_search_result(self, location: str, status: str, details: str = "") -> None:
        """Show search result in a consistent format."""
        if details:
            if isinstance(details, Path):
                details = f"Found at: {details}"
            print(f"├─ {location}... {status} ({details})")
        else:
            print(f"├─ {location}... {status}")

    def _show_not_found_help(self, searched_deep: bool) -> None:
        """Show helpful message when manage.py not found."""
        print("└─ ❌ Could not find valid manage.py")

        # Show invalid files found, if any
        if self.invalid_files_found:
            print()
            print("⚠️  Found invalid manage.py files:")
            for invalid_file in self.invalid_files_found:
                print(f"   • {invalid_file} (corrupted or not a Django manage.py)")

        print()
        print("💡 Suggestions:")
        print("• Make sure you're in a Django project directory")
        if not searched_deep:
            print("• Try: mercury-test --search-deep (searches all subdirectories)")
        print("• Navigate to your project root and try again")
        if self.invalid_files_found:
            print("• Check/fix the corrupted manage.py files listed above")
        print()
        print("🆘 Need help? Run: mercury-test --list-plugins")
