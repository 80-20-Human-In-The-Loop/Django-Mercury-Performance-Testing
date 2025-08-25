"""
Wizard Plugin for Mercury-Test CLI

Interactive test selection wizard for beginners learning Django testing.
Provides a menu-driven interface to guide users through test configuration.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from argparse import ArgumentParser, Namespace
from typing import List, Tuple, Optional, Dict, Any
import random

from django_mercury.cli.plugins.base import MercuryPlugin

# Try to import rich for beautiful UI
try:
    from rich.console import Console
    from rich.prompt import Prompt, Confirm
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class WizardPlugin(MercuryPlugin):
    """Interactive test selection wizard for beginners."""

    name = "wizard"
    description = "Interactive test selection wizard"
    priority = 20
    version = "1.0.0"

    # Audience targeting
    audiences = ["student", "expert"]  # Good for both learning and teams
    complexity_level = 2  # Moderate complexity
    requires_capabilities = ["rich"]  # Better with rich, but works without

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register wizard-related arguments."""
        parser.add_argument(
            "--wizard",
            action="store_true",
            help="Launch interactive test wizard for guided test selection",
        )

    def can_handle(self, args: Namespace) -> bool:
        """Check if wizard should handle this request."""
        return args.wizard

    def execute(self, args: Namespace) -> int:
        """Launch the test wizard."""
        wizard = TestWizard()
        return wizard.run(args)


class CommandStorage:
    """Manages saved test commands in project-local JSON file."""

    def __init__(self, project_root: Path):
        """Initialize with project root directory."""
        self.project_root = project_root
        self.command_file = project_root / "mercury_test_commands.json"
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Create command file if it doesn't exist."""
        if not self.command_file.exists():
            initial_data = {"version": "1.0", "project": self.project_root.name, "commands": []}
            self.command_file.write_text(json.dumps(initial_data, indent=2))

    def get_author_name(self) -> str:
        """Get author name from git config."""
        try:
            # Try git config first
            result = subprocess.run(
                ["git", "config", "user.name"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except:
            pass

        # Fallback to environment variable
        return os.environ.get("USER", os.environ.get("USERNAME", "anonymous"))

    def save_command(
        self, name: str, command: str, description: str = "", tags: List[str] = None
    ) -> bool:
        """Save a command with author attribution."""
        try:
            data = self.load_data()
            author = self.get_author_name()

            # Check if command with same name exists
            existing_index = None
            for i, cmd in enumerate(data["commands"]):
                if cmd["name"] == name:
                    existing_index = i
                    break

            new_command = {
                "name": name,
                "command": command,
                "description": description,
                "author": author,
                "created": datetime.now().isoformat(),
                "tags": tags or [],
                "stats": {
                    "last_used": datetime.now().isoformat(),
                    "use_count": 0,
                    "avg_duration": None,
                },
            }

            if existing_index is not None:
                # Update existing command
                old_stats = data["commands"][existing_index].get("stats", {})
                new_command["stats"]["use_count"] = old_stats.get("use_count", 0)
                new_command["stats"]["avg_duration"] = old_stats.get("avg_duration")
                data["commands"][existing_index] = new_command
            else:
                # Add new command
                data["commands"].append(new_command)

            self.command_file.write_text(json.dumps(data, indent=2))
            return True
        except Exception as e:
            print(f"Error saving command: {e}")
            return False

    def load_data(self) -> Dict:
        """Load all command data."""
        try:
            return json.loads(self.command_file.read_text())
        except:
            return {"version": "1.0", "project": self.project_root.name, "commands": []}

    def get_commands(self) -> List[Dict]:
        """Get list of saved commands."""
        data = self.load_data()
        return data.get("commands", [])

    def get_recent_command(self) -> Optional[Dict]:
        """Get most recently used command."""
        commands = self.get_commands()
        if not commands:
            return None

        # Sort by last_used
        sorted_cmds = sorted(
            commands, key=lambda x: x.get("stats", {}).get("last_used", ""), reverse=True
        )
        return sorted_cmds[0] if sorted_cmds else None

    def update_command_stats(self, name: str, duration: float = None):
        """Update usage statistics for a command."""
        try:
            data = self.load_data()
            for cmd in data["commands"]:
                if cmd["name"] == name:
                    stats = cmd.get("stats", {})
                    stats["last_used"] = datetime.now().isoformat()
                    stats["use_count"] = stats.get("use_count", 0) + 1

                    # Update average duration
                    if duration:
                        avg = stats.get("avg_duration")
                        if avg:
                            # Running average
                            count = stats["use_count"]
                            stats["avg_duration"] = ((avg * (count - 1)) + duration) / count
                        else:
                            stats["avg_duration"] = duration

                    cmd["stats"] = stats
                    break

            self.command_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            print(f"Error updating stats: {e}")

    def delete_command(self, name: str) -> bool:
        """Delete a saved command."""
        try:
            data = self.load_data()
            data["commands"] = [cmd for cmd in data["commands"] if cmd["name"] != name]
            self.command_file.write_text(json.dumps(data, indent=2))
            return True
        except:
            return False


class MenuSystem:
    """Handles interactive menus with rich/fallback support."""

    def __init__(self):
        """Initialize menu system."""
        self.use_rich = RICH_AVAILABLE
        self.console = Console() if RICH_AVAILABLE else None
        self.history = []  # For potential back navigation

    def select_option(
        self, title: str, options: List[Tuple[str, str, str]], allow_back: bool = True
    ) -> Optional[str]:
        """
        Display menu and get user selection.

        Args:
            title: Menu title
            options: List of (value, label, description) tuples
            allow_back: Show back option

        Returns:
            Selected value, 'back', or None for cancel
        """
        if self.use_rich:
            return self._rich_menu(title, options, allow_back)
        else:
            return self._simple_menu(title, options, allow_back)

    def _rich_menu(
        self, title: str, options: List[Tuple[str, str, str]], allow_back: bool
    ) -> Optional[str]:
        """Rich terminal menu display."""
        self.console.print()
        self.console.print(f"[bold blue]{title}[/bold blue]")
        self.console.print("═" * 40)
        self.console.print()

        # Build choice map
        choice_map = {}
        valid_choices = []

        for i, (value, label, desc) in enumerate(options, 1):
            self.console.print(f"[cyan]{i}.[/cyan] [white]{label}[/white]")
            if desc:
                self.console.print(f"   [dim]{desc}[/dim]")
            self.console.print()

            choice_map[str(i)] = value
            valid_choices.append(str(i))

        if allow_back:
            self.console.print("[cyan]b.[/cyan] [dim]← Back[/dim]")
            self.console.print()
            valid_choices.append("b")

        self.console.print("[cyan]q.[/cyan] [dim]Quit wizard[/dim]")
        self.console.print()
        valid_choices.append("q")

        # Get user choice
        choice = Prompt.ask(
            "[yellow]Your choice[/yellow]", choices=valid_choices, show_choices=False
        )

        if choice == "q":
            return None
        elif choice == "b":
            return "back"
        else:
            return choice_map[choice]

    def _simple_menu(
        self, title: str, options: List[Tuple[str, str, str]], allow_back: bool
    ) -> Optional[str]:
        """Simple terminal menu display."""
        print()
        print(title)
        print("=" * 40)
        print()

        choice_map = {}

        for i, (value, label, desc) in enumerate(options, 1):
            print(f"{i}. {label}")
            if desc:
                print(f"   {desc}")
            print()
            choice_map[str(i)] = value

        if allow_back:
            print("b. ← Back")
            print()

        print("q. Quit wizard")
        print()

        while True:
            choice = input("Your choice: ").strip().lower()

            if choice == "q":
                return None
            elif choice == "b" and allow_back:
                return "back"
            elif choice in choice_map:
                return choice_map[choice]
            else:
                print("Invalid choice. Please try again.")

    def confirm(self, message: str, default: bool = True) -> bool:
        """Get yes/no confirmation."""
        if self.use_rich:
            return Confirm.ask(message, default=default)
        else:
            default_str = "Y/n" if default else "y/N"
            response = input(f"{message} [{default_str}]: ").strip().lower()
            if not response:
                return default
            return response in ["y", "yes"]


class TestDiscovery:
    """Discovers and analyzes available tests."""

    def __init__(self, project_root: Path = None):
        """Initialize with project root directory."""
        self.project_root = project_root or Path.cwd()

    def get_apps_with_tests(self) -> List[Dict[str, Any]]:
        """
        Find all Django apps with tests.

        Returns:
            List of dicts with app info
        """
        apps = []

        # First try to get from Django's INSTALLED_APPS
        installed_apps = self._get_installed_apps()

        if installed_apps:
            # Use Django's app registry
            for app_name in installed_apps:
                if self._is_local_app(app_name):
                    # Try multiple path strategies
                    app_short_name = app_name.split(".")[-1]
                    possible_paths = [
                        self.project_root / app_short_name,
                        self.project_root / app_name.replace(".", "/"),
                        self.project_root.parent / app_short_name,  # Check parent dir too
                    ]

                    app_path = None
                    for path in possible_paths:
                        if path.exists() and path.is_dir():
                            app_path = path
                            break

                    if app_path:
                        test_files = self._find_test_files(app_path)
                        test_count = self._estimate_test_count(test_files) if test_files else 0

                        # Include app even if no tests found
                        apps.append(
                            {
                                "name": app_short_name,
                                "path": str(app_path),
                                "test_count": test_count,
                                "test_files": [f.name for f in test_files] if test_files else [],
                                "estimated_time": test_count * 2 if test_count > 0 else 0,
                                "has_tests": len(test_files) > 0,
                            }
                        )
        else:
            # Fallback: scan project directory
            for path in self.project_root.iterdir():
                if path.is_dir() and not path.name.startswith("."):
                    # Check if it looks like a Django app
                    if self._looks_like_django_app(path):
                        test_files = self._find_test_files(path)
                        test_count = self._estimate_test_count(test_files) if test_files else 0

                        # Include app even if no tests found
                        apps.append(
                            {
                                "name": path.name,
                                "path": str(path),
                                "test_count": test_count,
                                "test_files": [f.name for f in test_files] if test_files else [],
                                "estimated_time": test_count * 2 if test_count > 0 else 0,
                                "has_tests": len(test_files) > 0,
                            }
                        )

        return sorted(apps, key=lambda x: x["name"])

    def _get_installed_apps(self) -> Optional[List[str]]:
        """Try to get INSTALLED_APPS from Django settings."""
        try:
            # Try to set up Django environment
            import django
            from django.conf import settings

            # Check if Django is already configured
            if settings.configured:
                return [
                    app
                    for app in settings.INSTALLED_APPS
                    if not app.startswith("django.") and not app.startswith("rest_framework")
                ]
            else:
                # Try to find and use settings module
                settings_module = os.environ.get("DJANGO_SETTINGS_MODULE")
                if not settings_module:
                    # Look for common settings patterns
                    for pattern in ["settings", "config.settings", "project.settings"]:
                        settings_path = self.project_root / pattern.replace(".", "/")
                        if settings_path.with_suffix(".py").exists():
                            os.environ["DJANGO_SETTINGS_MODULE"] = pattern
                            break

                # Try to setup Django
                try:
                    django.setup()
                    return [
                        app
                        for app in settings.INSTALLED_APPS
                        if not app.startswith("django.") and not app.startswith("rest_framework")
                    ]
                except:
                    pass
        except:
            pass

        return None

    def _is_local_app(self, app_name: str) -> bool:
        """Check if app is local (not third-party)."""
        # Skip known third-party apps
        third_party = [
            "django",
            "rest_framework",
            "corsheaders",
            "debug_toolbar",
            "crispy_forms",
            "allauth",
            "channels",
            "celery",
        ]
        return not any(app_name.startswith(tp) for tp in third_party)

    def _looks_like_django_app(self, path: Path) -> bool:
        """Check if directory looks like a Django app."""
        # Check for common Django app files
        indicators = ["models.py", "views.py", "urls.py", "apps.py", "admin.py"]
        return any((path / indicator).exists() for indicator in indicators)

    def _find_test_files(self, app_path: Path) -> List[Path]:
        """Find test files in an app directory."""
        test_files = []

        # Look for test files in app root
        for pattern in ["test*.py", "tests.py", "*_test.py", "*_tests.py"]:
            test_files.extend(app_path.glob(pattern))

        # Check tests/ subdirectory more thoroughly
        tests_dir = app_path / "tests"
        if tests_dir.exists() and tests_dir.is_dir():
            # Get all Python files in tests/ (excluding __init__.py)
            for py_file in tests_dir.glob("**/*.py"):
                if py_file.name != "__init__.py":
                    # Check if file contains test code
                    try:
                        content = py_file.read_text()
                        # Look for test indicators
                        if any(
                            indicator in content
                            for indicator in ["TestCase", "def test_", "class Test", "@pytest"]
                        ):
                            test_files.append(py_file)
                    except:
                        # If can't read, include it anyway to be safe
                        test_files.append(py_file)

        # Also check for test.py or test directories at app root
        test_dir = app_path / "test"
        if test_dir.exists() and test_dir.is_dir():
            for py_file in test_dir.glob("**/*.py"):
                if py_file.name != "__init__.py":
                    test_files.append(py_file)

        return test_files

    def search_for_tests(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for test classes and methods containing the query.

        Args:
            query: Search term to look for in test names

        Returns:
            List of dicts with test info: {'path': str, 'name': str, 'type': str, 'app': str}
        """
        if not query:
            return []

        query_lower = query.lower()
        found_tests = []

        # Get all apps with tests
        apps = self.get_apps_with_tests()

        for app in apps:
            app_name = app["name"]
            app_path = Path(app["path"])

            # Get all test files in the app
            test_files = self._find_test_files(app_path)

            for test_file in test_files:
                try:
                    # Read the test file content
                    content = test_file.read_text()
                    lines = content.split("\n")

                    # Parse for test classes and methods
                    current_class = None

                    for line_num, line in enumerate(lines, 1):
                        stripped = line.strip()

                        # Look for test classes
                        if stripped.startswith("class ") and (
                            "Test" in stripped or "test" in stripped.lower()
                        ):
                            class_match = stripped.split("(")[0].replace("class ", "").strip()
                            if query_lower in class_match.lower():
                                # Build module path from file path
                                rel_path = test_file.relative_to(app_path)
                                module_path = str(rel_path.with_suffix("")).replace("/", ".")
                                full_path = f"{app_name}.{module_path}.{class_match}"

                                found_tests.append(
                                    {
                                        "path": full_path,
                                        "name": class_match,
                                        "type": "class",
                                        "app": app_name,
                                        "file": str(test_file.name),
                                        "line": line_num,
                                    }
                                )
                            current_class = class_match

                        # Look for test methods
                        elif stripped.startswith("def test_") or stripped.startswith("def test "):
                            method_match = stripped.split("(")[0].replace("def ", "").strip()
                            if query_lower in method_match.lower() and current_class:
                                # Build full test path
                                rel_path = test_file.relative_to(app_path)
                                module_path = str(rel_path.with_suffix("")).replace("/", ".")
                                full_path = (
                                    f"{app_name}.{module_path}.{current_class}.{method_match}"
                                )

                                found_tests.append(
                                    {
                                        "path": full_path,
                                        "name": f"{current_class}.{method_match}",
                                        "type": "method",
                                        "app": app_name,
                                        "file": str(test_file.name),
                                        "line": line_num,
                                    }
                                )
                except Exception:
                    # Skip files that can't be read
                    continue

        return found_tests

    def _estimate_test_count(self, test_files: List[Path]) -> int:
        """Estimate number of tests in files."""
        count = 0
        for file in test_files:
            try:
                content = file.read_text()
                # Count test methods (rough estimate)
                count += content.count("def test_")
            except:
                # If can't read, estimate 5 tests per file
                count += 5

        return max(count, 1)

    def get_test_structure_in_app(self, app_name: str) -> Dict[str, Any]:
        """Get hierarchical test structure in an app.

        Returns:
            Dict with 'subdirs' (dict of subdir->files) and 'root_files' (list)
        """
        app_path = self.project_root / app_name
        if not app_path.exists():
            return {"subdirs": {}, "root_files": []}

        test_files = self._find_test_files(app_path)
        structure = {"subdirs": {}, "root_files": []}

        for test_file in test_files:
            try:
                rel_path = test_file.relative_to(app_path)
                parts = rel_path.parts

                # Check if file is in a subdirectory
                if len(parts) > 1:  # Has subdirectories
                    subdir = parts[0]
                    # Skip if it's the main tests directory
                    if subdir in ["tests", "test"]:
                        if len(parts) > 2:  # tests/subdir/file.py
                            actual_subdir = parts[1]
                            if actual_subdir not in structure["subdirs"]:
                                structure["subdirs"][actual_subdir] = []
                            # Add the relative module path from app root
                            module_path = str(rel_path.with_suffix("")).replace(os.sep, ".")
                            structure["subdirs"][actual_subdir].append(module_path)
                        else:  # tests/file.py
                            module_path = str(rel_path.with_suffix("")).replace(os.sep, ".")
                            structure["root_files"].append(module_path)
                    else:
                        # File in other subdirectory structure
                        if subdir not in structure["subdirs"]:
                            structure["subdirs"][subdir] = []
                        module_path = str(rel_path.with_suffix("")).replace(os.sep, ".")
                        structure["subdirs"][subdir].append(module_path)
                else:
                    # File directly in app root
                    module_path = str(rel_path.with_suffix("")).replace(os.sep, ".")
                    structure["root_files"].append(module_path)

            except ValueError:
                continue

        return structure

    def get_test_files_in_app(self, app_name: str) -> List[str]:
        """Get list of test files in an app as module paths."""
        app_path = self.project_root / app_name
        if not app_path.exists():
            return []

        test_files = self._find_test_files(app_path)
        module_paths = []

        for test_file in test_files:
            # Get relative path from app directory
            try:
                rel_path = test_file.relative_to(app_path)
                # Convert to module path (replace / with . and remove .py)
                module_path = str(rel_path.with_suffix("")).replace(os.sep, ".")
                module_paths.append(module_path)
            except ValueError:
                # If file is not relative to app_path, use just the stem
                module_paths.append(test_file.stem)

        return module_paths


class WizardEducation:
    """Educational content and tips for the wizard."""

    @staticmethod
    def get_random_tip() -> str:
        """Get a random helpful tip."""
        tips = [
            "💡 Start with testing a single app to learn faster",
            "💡 Use --failfast to stop on the first failure",
            "💡 Tests run faster with --keepdb if you run them often",
            "💡 Verbose output helps you understand what's being tested",
            "💡 Good tests are isolated and don't depend on each other",
            "💡 Write tests before fixing bugs to ensure they don't come back",
            "💡 Test the behavior, not the implementation",
        ]
        return random.choice(tips)

    @staticmethod
    def explain_option(option: str) -> str:
        """Get explanation for an option."""
        explanations = {
            "all_tests": "This runs every test in your Django project. Good for final checks before deployment.",
            "app_tests": "Test a specific Django app. This is usually the best place to start.",
            "file_tests": "Run tests from a single file. Useful when working on specific features.",
            "function_tests": "Run just one test function. Perfect for debugging a failing test.",
            "verbosity": "Controls how much output you see during tests.",
            "keepdb": "Preserves the test database between runs, making tests faster.",
            "parallel": "Run tests simultaneously using multiple CPU cores.",
            "failfast": "Stop immediately when a test fails instead of running all tests.",
        }
        return explanations.get(option, "")


class TestWizard:
    """Main wizard flow controller."""

    def __init__(self):
        """Initialize the wizard."""
        self.menu = MenuSystem()
        self.discovery = None  # Will be set after finding project
        self.education = WizardEducation()
        self.command_storage = None  # Will be set after finding project
        self.selections = {}
        self.project_root = None
        self.manage_py_path = None
        self.author_name = None

    def run(self, original_args: Namespace) -> int:
        """Run the wizard flow."""
        try:
            # First, find the Django project
            if not self.find_django_project(original_args):
                return 1

            # Initialize components with project root
            self.discovery = TestDiscovery(self.project_root)
            self.command_storage = CommandStorage(self.project_root)
            self.author_name = self.command_storage.get_author_name()

            # Personalized greeting
            if self.menu.use_rich:
                self.menu.console.print("[bold green]🧙 Django Mercury Test Wizard[/bold green]")
                if self.author_name and self.author_name != "anonymous":
                    self.menu.console.print(f"Hello, {self.author_name}! 👋")
                self.menu.console.print("[dim]Let's make testing easy![/dim]")
            else:
                print("🧙 Django Mercury Test Wizard")
                if self.author_name and self.author_name != "anonymous":
                    print(f"Hello, {self.author_name}! 👋")
                print("Let's make testing easy!")

            # Show where we found the project
            self.show_project_info()

            # Now run the wizard flow
            return self.run_wizard_flow(original_args)

        except KeyboardInterrupt:
            # Graceful Ctrl+C handling
            if self.menu.use_rich:
                self.menu.console.print("\n\n[yellow]Wizard cancelled.[/yellow]")
            else:
                print("\n\nWizard cancelled.")
            return 0

    def find_django_project(self, args: Namespace) -> bool:
        """Use discovery plugin to find Django project."""
        if self.menu.use_rich:
            self.menu.console.print("\n[dim]🔍 Looking for Django project...[/dim]")
        else:
            print("\n🔍 Looking for Django project...")

        # Use the discovery utility to find manage.py
        from django_mercury.cli.plugins.discovery_utils import find_manage_py

        manage_py = find_manage_py(args)

        if not manage_py:
            # Can't find Django project
            if self.menu.use_rich:
                self.menu.console.print("[red]❌ Could not find Django project![/red]")
                self.menu.console.print(
                    "[dim]Try running from your project directory or use --search-deep[/dim]"
                )
            else:
                print("❌ Could not find Django project!")
                print("Try running from your project directory or use --search-deep")
            return False

        self.manage_py_path = Path(manage_py)
        self.project_root = self.manage_py_path.parent
        return True

    def show_project_info(self):
        """Show where we found the Django project."""
        if self.menu.use_rich:
            self.menu.console.print(f"[green]✅ Found Django project:[/green] {self.project_root}")
            self.menu.console.print()
        else:
            print(f"✅ Found Django project: {self.project_root}")
            print()

    def run_wizard_flow(self, original_args: Namespace) -> int:
        """Run the main wizard flow after finding project."""
        try:
            # Step 1: Main action selection
            action = self.select_action()
            if not action:
                return 0  # User quit

            # Step 2: Target selection based on action
            target = self.select_target(action)
            if target == "back":
                return self.run_wizard_flow(original_args)  # Restart flow
            elif target and target.startswith("run_saved:"):
                # Run a saved command directly
                command = target.replace("run_saved:", "")
                command_args = command.split() if command else []
                return self.execute_tests(command_args)
            elif not target and action not in ["all_tests", "saved_commands"]:
                return 0  # User quit
            elif action == "saved_commands":
                # If we handled saved commands and got back, restart
                return self.run_wizard_flow(original_args)

            # Step 3: Test options
            options = self.select_test_options()
            if options == "back":
                return self.run_wizard_flow(original_args)  # Restart flow
            elif not options:
                return 0  # User quit

            # Step 4: Build and confirm command
            command_args = self.build_command(action, target, options)
            result = self.confirm_execution(command_args)
            if result == "run":
                return self.execute_tests(command_args)
            elif result == "saved":
                # Command was saved, ask if they want to run it
                if self.menu.confirm("Run the saved command now?", default=True):
                    return self.execute_tests(command_args)
                else:
                    return self.run_wizard_flow(original_args)

            return 0

        except KeyboardInterrupt:
            # User pressed Ctrl+C during flow
            return 0

    def select_action(self) -> Optional[str]:
        """Step 1: Main action selection."""
        # Show recent command if available
        recent = self.command_storage.get_recent_command()
        if recent:
            if self.menu.use_rich:
                author = recent.get("author", "unknown")
                cmd = recent.get("command", "")
                name = recent.get("name", "")
                self.menu.console.print(f'\n[dim]💫 Recent: "{name}" by {author}[/dim]')
                self.menu.console.print(f"[dim]   {cmd}[/dim]\n")
            else:
                name = recent.get("name", "")
                print(f"\n💫 Recent: {name}\n")

        options = [
            ("all_tests", "🌍 Run all tests", "Test everything (might take a while)"),
            ("app_tests", "📦 Test specific app", "Choose which app to test"),
            ("file_tests", "📄 Test single file", "Test one specific test file"),
            ("function_tests", "🎯 Test specific function", "Run a single test function"),
        ]

        # Add search option if we have rich
        if self.menu.use_rich:
            options.append(("search", "🔍 Search for tests", "Find tests by name"))

        # Add saved commands option
        saved_count = len(self.command_storage.get_commands())
        if saved_count > 0:
            options.append(
                (
                    "saved_commands",
                    f"📚 Saved commands ({saved_count} in project)",
                    "Run or manage saved test configs",
                )
            )
        else:
            options.append(
                (
                    "saved_commands",
                    "📚 No saved commands yet",
                    "Save your first command after building it",
                )
            )

        return self.menu.select_option("What would you like to test?", options, allow_back=False)

    def select_target(self, action: str) -> Optional[str]:
        """Step 2: Select test target based on action."""
        if action == "all_tests":
            return None  # No target needed

        elif action == "app_tests":
            app = self.select_app()
            if not app or app == "back":
                return app

            # Check if app has test subdirectories and offer module selection
            modules = self.select_test_modules(app)

            if modules == "back":
                return self.select_target(action)  # Try again
            elif modules is None:
                # Run all tests in app (no subdirs or user selected all)
                return app
            else:
                # Return space-separated list of module paths
                return " ".join(modules)

        elif action == "file_tests":
            return self.select_test_file()

        elif action == "function_tests":
            return self.select_test_function()

        elif action == "search":
            return self.search_tests()

        elif action == "saved_commands":
            return self.handle_saved_commands()

        return None

    def handle_saved_commands(self) -> Optional[str]:
        """Handle saved commands menu."""
        commands = self.command_storage.get_commands()

        if not commands:
            if self.menu.use_rich:
                self.menu.console.print("[yellow]No saved commands yet![/yellow]")
                self.menu.console.print(
                    "[dim]Build and save your first command to get started.[/dim]"
                )
            else:
                print("No saved commands yet!")
                print("Build and save your first command to get started.")
            return "back"

        # Display saved commands
        if self.menu.use_rich:
            self.menu.console.print("\n[bold blue]📚 Project Test Commands[/bold blue]")
            self.menu.console.print("═" * 40)
            self.menu.console.print()

            for i, cmd in enumerate(commands, 1):
                name = cmd.get("name", "Unnamed")
                author = cmd.get("author", "unknown")
                command = cmd.get("command", "")
                desc = cmd.get("description", "")
                stats = cmd.get("stats", {})
                use_count = stats.get("use_count", 0)
                avg_duration = stats.get("avg_duration")

                self.menu.console.print(f"[cyan]{i}.[/cyan] [bold]{name}[/bold]")
                self.menu.console.print(f"   by {author} • mercury-test {command}")
                if desc:
                    self.menu.console.print(f'   [dim]"{desc}"[/dim]')

                stats_str = f"   Used {use_count} times"
                if avg_duration:
                    stats_str += f" • Avg: {avg_duration:.1f}s"
                self.menu.console.print(f"   [dim]{stats_str}[/dim]")
                self.menu.console.print()
        else:
            print("\n📚 Project Test Commands")
            print("=" * 40)
            for i, cmd in enumerate(commands, 1):
                name = cmd.get("name", "Unnamed")
                command = cmd.get("command", "")
                print(f"{i}. {name}")
                print(f"   mercury-test {command}")
                print()

        # Get user choice
        choices = [str(i) for i in range(1, len(commands) + 1)]
        choices.extend(["d", "b"])

        if self.menu.use_rich:
            self.menu.console.print("[yellow]Options:[/yellow]")
            self.menu.console.print("[1-{}] Run command".format(len(commands)))
            self.menu.console.print("[D] Delete a command")
            self.menu.console.print("[B] Back to main menu")
            self.menu.console.print()

            choice = Prompt.ask("Your choice", choices=choices, show_choices=False)
        else:
            print("Options:")
            print(f"[1-{len(commands)}] Run command")
            print("[D] Delete a command")
            print("[B] Back to main menu")
            print()

            choice = input("Your choice: ").strip().lower()

        if choice == "b":
            return "back"
        elif choice == "d":
            return self.delete_saved_command(commands)
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(commands):
                # Return the command to run
                cmd = commands[idx]
                self.command_storage.update_command_stats(cmd["name"])
                return "run_saved:" + cmd.get("command", "")

        return "back"

    def delete_saved_command(self, commands: List[Dict]) -> str:
        """Delete a saved command."""
        if self.menu.use_rich:
            self.menu.console.print("\n[yellow]Which command to delete?[/yellow]")
            for i, cmd in enumerate(commands, 1):
                self.menu.console.print(f"[cyan]{i}.[/cyan] {cmd.get('name', 'Unnamed')}")
            self.menu.console.print("[cyan]c.[/cyan] Cancel")

            choices = [str(i) for i in range(1, len(commands) + 1)]
            choices.append("c")
            choice = Prompt.ask("Delete", choices=choices, show_choices=False)
        else:
            print("\nWhich command to delete?")
            for i, cmd in enumerate(commands, 1):
                print(f"{i}. {cmd.get('name', 'Unnamed')}")
            print("c. Cancel")
            choice = input("Delete: ").strip().lower()

        if choice != "c" and choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(commands):
                cmd_name = commands[idx].get("name", "Unnamed")
                if self.command_storage.delete_command(cmd_name):
                    if self.menu.use_rich:
                        self.menu.console.print(f"[green]✅ Deleted '{cmd_name}'[/green]")
                    else:
                        print(f"✅ Deleted '{cmd_name}'")

        return "back"

    def parse_module_selection(self, input_str: str, num_modules: int) -> List[int]:
        """Parse module selection input like '1,3,5' or '1-3' or '*'.

        Returns list of selected indices (0-based).
        """
        input_str = input_str.strip()

        # Handle 'all' or '*' or empty
        if not input_str or input_str in ["*", "all"]:
            return list(range(num_modules))

        selected = set()
        parts = input_str.replace(" ", "").split(",")

        for part in parts:
            if "-" in part:
                # Handle range like '1-3'
                try:
                    start, end = part.split("-", 1)
                    start_idx = int(start) - 1  # Convert to 0-based
                    end_idx = int(end) - 1
                    # Add all indices in range (inclusive)
                    for i in range(start_idx, end_idx + 1):
                        if 0 <= i < num_modules:
                            selected.add(i)
                except (ValueError, IndexError):
                    continue
            else:
                # Handle single number
                try:
                    idx = int(part) - 1  # Convert to 0-based
                    if 0 <= idx < num_modules:
                        selected.add(idx)
                except ValueError:
                    continue

        return sorted(list(selected))

    def select_test_modules(self, app: str) -> Optional[List[str]]:
        """Select which test modules to run in an app.

        Returns:
            List of module paths to test, or None if cancelled/back
        """
        # Get test structure
        structure = self.discovery.get_test_structure_in_app(app)

        # If no subdirectories, return None to indicate run all
        if not structure["subdirs"]:
            return None

        # Build list of available modules
        modules = []
        module_info = []

        for subdir, files in sorted(structure["subdirs"].items()):
            module_path = f"tests.{subdir}"
            modules.append(module_path)
            test_count = len(files)
            module_info.append((subdir, test_count))

        # Display available modules
        if self.menu.use_rich:
            self.menu.console.print(f"\n📦 Test modules in {app}:")
            self.menu.console.print("=" * 40)
            self.menu.console.print("\nAvailable modules:")
            for i, (subdir, count) in enumerate(module_info, 1):
                self.menu.console.print(
                    f"  {i}. {subdir} ({count} test{'s' if count != 1 else ''})"
                )
            self.menu.console.print()

            # Get selection
            from rich.prompt import Prompt

            selection = Prompt.ask(
                "Enter module numbers to test (e.g., 1,3,5 or * for all)", default="*"
            )
        else:
            print(f"\n📦 Test modules in {app}:")
            print("=" * 40)
            print("\nAvailable modules:")
            for i, (subdir, count) in enumerate(module_info, 1):
                print(f"  {i}. {subdir} ({count} test{'s' if count != 1 else ''})")
            print()

            # Get selection
            selection = input("Enter module numbers to test (e.g., 1,3,5 or * for all) (*): ")
            if not selection:
                selection = "*"

        # Handle back/quit
        if selection.lower() in ["b", "back"]:
            return "back"
        if selection.lower() in ["q", "quit"]:
            return None

        # Parse selection
        selected_indices = self.parse_module_selection(selection, len(modules))

        if not selected_indices:
            # No valid selection, run all
            return None

        # Build list of selected module paths
        selected_modules = []
        total_tests = 0

        sorted_subdirs = sorted(structure["subdirs"].keys())
        for idx in selected_indices:
            subdir = sorted_subdirs[idx]
            # Build module path for the subdirectory (not individual files)
            selected_modules.append(f"{app}.tests.{subdir}")
            total_tests += len(structure["subdirs"][subdir])

        # Show what will be tested
        if self.menu.use_rich:
            self.menu.console.print("\n[green]This will test:[/green]")
            for idx in selected_indices:
                subdir, count = module_info[idx]
                self.menu.console.print(
                    f"  • {app}.tests.{subdir} ({count} test{'s' if count != 1 else ''})"
                )
            self.menu.console.print(
                f"[dim]Total: {total_tests} test{'s' if total_tests != 1 else ''}[/dim]\n"
            )
        else:
            print("\nThis will test:")
            for idx in selected_indices:
                subdir, count = module_info[idx]
                print(f"  • {app}.tests.{subdir} ({count} test{'s' if count != 1 else ''})")
            print(f"Total: {total_tests} test{'s' if total_tests != 1 else ''}\n")

        return selected_modules if selected_modules else None

    def select_app(self) -> Optional[str]:
        """Select a Django app to test."""
        apps = self.discovery.get_apps_with_tests()

        if not apps:
            if self.menu.use_rich:
                self.menu.console.print("[red]No apps with tests found![/red]")
            else:
                print("No apps with tests found!")
            return None

        options = []
        for app in apps:
            label = app["name"]
            if app.get("has_tests", True):  # Default to True for backward compatibility
                if app["test_count"] > 0:
                    desc = f"{app['test_count']} tests, ~{app['estimated_time']}s"
                else:
                    desc = "Tests found (count unknown)"
            else:
                desc = "⚠️ No tests found"
            options.append((app["name"], label, desc))

        # Show a tip
        tip = self.education.get_random_tip()
        if self.menu.use_rich:
            self.menu.console.print(f"\n{tip}\n", style="dim")
        else:
            print(f"\n{tip}\n")

        return self.menu.select_option("📦 Select an app to test:", options, allow_back=True)

    def select_test_subdirectory(self, app: str, structure: Dict[str, Any]) -> Optional[str]:
        """Select a test subdirectory or show all files.

        Returns:
            - subdirectory name
            - 'all' to show all files
            - 'back' to go back
            - None if cancelled
        """
        options = []

        # Add subdirectory options
        for subdir, files in sorted(structure["subdirs"].items()):
            count = len(files)
            label = f"📁 {subdir}/"
            desc = f"{count} test file{'s' if count != 1 else ''}"
            options.append((subdir, label, desc))

        # Add root files if any
        if structure["root_files"]:
            count = len(structure["root_files"])
            options.append(
                ("root", f"📄 Root level tests", f"{count} file{'s' if count != 1 else ''}")
            )

        # Add option to show all files
        total_files = sum(len(files) for files in structure["subdirs"].values()) + len(
            structure["root_files"]
        )
        options.append(("all", f"📋 Show all files", f"{total_files} files total"))

        return self.menu.select_option(
            f"📂 Select test category in {app}:", options, allow_back=True
        )

    def select_test_file(self) -> Optional[str]:
        """Select a test file with hierarchical navigation."""
        # First select app
        app = self.select_app()
        if not app or app == "back":
            return app

        # Get test structure
        structure = self.discovery.get_test_structure_in_app(app)

        # Check if there are any test files
        total_files = sum(len(files) for files in structure["subdirs"].values()) + len(
            structure["root_files"]
        )
        if total_files == 0:
            if self.menu.use_rich:
                self.menu.console.print(f"[red]No test files found in {app}![/red]")
            else:
                print(f"No test files found in {app}!")
            return None

        # Initialize subdir_choice
        subdir_choice = None

        # If there are subdirectories, offer hierarchical navigation
        if structure["subdirs"] and total_files > 10:  # Only use hierarchy for 10+ files
            subdir_choice = self.select_test_subdirectory(app, structure)

            if not subdir_choice or subdir_choice == "back":
                return self.select_test_file()  # Recurse to start over

            # Determine which files to show
            if subdir_choice == "all":
                # Show all files (flat list)
                files = self.discovery.get_test_files_in_app(app)
            elif subdir_choice == "root":
                # Show only root level files
                files = structure["root_files"]
            else:
                # Show files from selected subdirectory
                files = structure["subdirs"].get(subdir_choice, [])

            if not files:
                if self.menu.use_rich:
                    self.menu.console.print(f"[yellow]No test files in this category![/yellow]")
                else:
                    print("No test files in this category!")
                return self.select_test_file()  # Try again
        else:
            # For small number of files or no subdirs, show flat list
            files = self.discovery.get_test_files_in_app(app)

        # Build options with friendly display names
        options = []
        for f in files:
            full_path = f"{app}.{f}"
            # Create a more readable display name
            if "." in f:
                parts = f.split(".")
                if len(parts) > 2:  # e.g., tests.models.test_user
                    display_name = f"{parts[-2]}/{parts[-1]}"
                else:
                    display_name = parts[-1]
            else:
                display_name = f
            options.append((full_path, display_name, ""))

        # Sort options by display name for easier navigation
        options.sort(key=lambda x: x[1])

        title = f"📄 Select a test file from {app}"
        if subdir_choice and subdir_choice not in ["all", "root"]:
            title += f" > {subdir_choice}"

        return self.menu.select_option(title + ":", options, allow_back=True)

    def select_test_function(self) -> Optional[str]:
        """Select a specific test function."""
        try:
            # For simplicity, just get input
            if self.menu.use_rich:
                self.menu.console.print("\n[yellow]Enter the full test path:[/yellow]")
                self.menu.console.print(
                    "[dim]Example: users.tests.test_models.TestUser.test_creation[/dim]"
                )
                self.menu.console.print("[dim]Press Ctrl+C to go back[/dim]\n")
                test_path = Prompt.ask("Test path")
            else:
                print("\nEnter the full test path:")
                print("Example: users.tests.test_models.TestUser.test_creation")
                print("Press Ctrl+C to go back\n")
                test_path = input("Test path: ").strip()

            return test_path if test_path else None
        except KeyboardInterrupt:
            # User wants to go back
            return "back"

    def search_tests(self) -> Optional[str]:
        """Search for tests by name."""
        try:
            if self.menu.use_rich:
                self.menu.console.print("[dim]Press Ctrl+C to go back[/dim]\n")
                query = Prompt.ask("[yellow]Search for tests containing[/yellow]")
            else:
                print("Press Ctrl+C to go back\n")
                query = input("Search for tests containing: ").strip()

            if not query:
                return None

            # Perform actual search
            found_tests = self.discovery.search_for_tests(query)

            if not found_tests:
                if self.menu.use_rich:
                    self.menu.console.print(f"[red]❌ No tests found containing '{query}'[/red]")
                else:
                    print(f"❌ No tests found containing '{query}'")
                return None

            # Show search results and let user select
            return self._handle_search_results(found_tests, query)

        except KeyboardInterrupt:
            return "back"

    def _handle_search_results(
        self, found_tests: List[Dict[str, Any]], query: str
    ) -> Optional[str]:
        """Handle search results - display and let user select tests to run."""
        if self.menu.use_rich:
            self.menu.console.print(
                f"\n[green]🔍 Found {len(found_tests)} test{'s' if len(found_tests) != 1 else ''} matching '{query}':[/green]"
            )
            self.menu.console.print("═" * 50)

            # Group results by app for better display
            by_app = {}
            for test in found_tests:
                app = test["app"]
                if app not in by_app:
                    by_app[app] = []
                by_app[app].append(test)

            # Display grouped results
            for app_name, app_tests in by_app.items():
                self.menu.console.print(f"\n[cyan]{app_name}:[/cyan]")
                for test in app_tests:
                    icon = "🏷️" if test["type"] == "class" else "🔹"
                    self.menu.console.print(f"  {icon} {test['name']} [dim]({test['file']})[/dim]")

            self.menu.console.print("\nOptions:")
            self.menu.console.print("1. [green]Run all found tests[/green]")
            self.menu.console.print("2. [yellow]Select specific tests[/yellow]")
            self.menu.console.print("b. [dim]← Back[/dim]")

            from rich.prompt import Prompt

            choice = Prompt.ask("Your choice", choices=["1", "2", "b"], default="1")

            if choice == "b":
                return "back"
            elif choice == "1":
                # Run all found tests
                test_paths = [test["path"] for test in found_tests]
                return " ".join(test_paths)
            else:
                # Let user select specific tests
                return self._select_specific_search_results(found_tests)
        else:
            # Simple text version
            print(
                f"\n🔍 Found {len(found_tests)} test{'s' if len(found_tests) != 1 else ''} matching '{query}':"
            )
            print("=" * 50)

            for i, test in enumerate(found_tests, 1):
                icon = "[Class]" if test["type"] == "class" else "[Method]"
                print(f"  {i}. {icon} {test['name']} ({test['app']}/{test['file']})")

            print("\nOptions:")
            print("1. Run all found tests")
            print("2. Select specific tests")
            print("b. ← Back")

            choice = input("Your choice [1/2/b]: ").strip().lower()

            if choice == "b":
                return "back"
            elif choice in ["", "1"]:
                # Run all found tests
                test_paths = [test["path"] for test in found_tests]
                return " ".join(test_paths)
            else:
                # Let user select specific tests
                return self._select_specific_search_results(found_tests)

    def _select_specific_search_results(self, found_tests: List[Dict[str, Any]]) -> Optional[str]:
        """Let user select specific tests from search results."""
        if self.menu.use_rich:
            self.menu.console.print("\n[bold]Select tests to run:[/bold]")
            for i, test in enumerate(found_tests, 1):
                icon = "🏷️" if test["type"] == "class" else "🔹"
                self.menu.console.print(
                    f"  {i}. {icon} [bold]{test['name']}[/bold] [dim]({test['app']}/{test['file']})[/dim]"
                )

            from rich.prompt import Prompt

            selection = Prompt.ask(
                "\n[yellow]Enter test numbers to run (e.g., 1,3,5 or * for all)[/yellow]",
                default="*",
            )
        else:
            print("\nSelect tests to run:")
            for i, test in enumerate(found_tests, 1):
                icon = "[Class]" if test["type"] == "class" else "[Method]"
                print(f"  {i}. {icon} {test['name']} ({test['app']}/{test['file']})")

            selection = input("\nEnter test numbers to run (e.g., 1,3,5 or * for all) (*): ")
            if not selection:
                selection = "*"

        # Handle back/quit
        if selection.lower() in ["b", "back"]:
            return "back"

        # Parse selection
        selected_indices = self.parse_module_selection(selection, len(found_tests))

        if not selected_indices:
            # No valid selection or all selected
            test_paths = [test["path"] for test in found_tests]
            return " ".join(test_paths)

        # Get selected test paths
        selected_paths = []
        for idx in selected_indices:
            selected_paths.append(found_tests[idx]["path"])

        return " ".join(selected_paths) if selected_paths else None

    def select_test_options(self) -> Optional[Dict[str, Any]]:
        """Step 3: Select test execution options."""
        options = {}

        # Simple options selection
        if self.menu.use_rich:
            self.menu.console.print("\n[bold blue]⚙️ Test Options[/bold blue]")
            self.menu.console.print("═" * 40)
            self.menu.console.print()

            # Verbosity
            verbosity = Prompt.ask(
                "Verbosity level", choices=["0", "1", "2", "3"], default="1", show_choices=True
            )
            options["verbosity"] = int(verbosity)

            # Other options
            options["keepdb"] = Confirm.ask("Keep test database?", default=False)
            options["parallel"] = Confirm.ask("Run tests in parallel?", default=False)
            if options["parallel"]:
                cores = Prompt.ask("Number of parallel processes", default="4")
                options["parallel"] = int(cores)
            options["failfast"] = Confirm.ask("Stop on first failure?", default=False)

        else:
            print("\n⚙️ Test Options")
            print("=" * 40)
            print()

            # Simplified for non-rich
            print("Using default options (verbosity=1)")
            options = {"verbosity": 1, "keepdb": False, "parallel": False, "failfast": False}

        return options

    def build_command(
        self, action: str, target: Optional[str], options: Dict[str, Any]
    ) -> List[str]:
        """Build the command arguments."""
        args = []

        # Add target(s)
        if target:
            # Check if target contains multiple modules (space-separated)
            if " " in target:
                # Multiple test modules
                args.extend(target.split())
            else:
                # Single target
                args.append(target)

        # Add options
        if options.get("verbosity") != 1:
            args.extend(["--verbosity", str(options["verbosity"])])

        if options.get("keepdb"):
            args.append("--keepdb")

        if options.get("parallel"):
            if isinstance(options["parallel"], int) and options["parallel"] > 1:
                args.extend(["--parallel", str(options["parallel"])])
            elif options["parallel"] is True:
                args.extend(["--parallel", "4"])

        if options.get("failfast"):
            args.append("--failfast")

        return args

    def confirm_execution(self, command_args: List[str]) -> str:
        """Step 4: Show command and confirm execution with save option."""
        cmd_str = "mercury-test " + " ".join(command_args) if command_args else "mercury-test"

        if self.menu.use_rich:
            self.menu.console.print("\n[bold blue]📋 Ready to run tests![/bold blue]")
            self.menu.console.print("═" * 40)
            self.menu.console.print()

            self.menu.console.print(f"[yellow]Command:[/yellow] {cmd_str}")
            self.menu.console.print()

            # Explain what will happen
            self.menu.console.print("[dim]This will:[/dim]")
            if not command_args:
                self.menu.console.print("[dim]• Test everything in your project[/dim]")
            else:
                # Get all test targets (before option flags)
                test_targets = []
                for arg in command_args:
                    if arg.startswith("--"):
                        break
                    test_targets.append(arg)

                if len(test_targets) == 1:
                    # Single target
                    target = test_targets[0]
                    if target.count(".") == 0:
                        self.menu.console.print(f"[dim]• Test the '{target}' app[/dim]")
                    elif ".tests." in target:
                        # Module path
                        self.menu.console.print(f"[dim]• Test module: {target}[/dim]")
                    else:
                        self.menu.console.print(f"[dim]• Test {target}[/dim]")
                else:
                    # Multiple targets
                    self.menu.console.print(f"[dim]• Test {len(test_targets)} modules:[/dim]")
                    for target in test_targets[:5]:  # Show first 5
                        self.menu.console.print(f"[dim]  - {target}[/dim]")
                    if len(test_targets) > 5:
                        self.menu.console.print(
                            f"[dim]  ... and {len(test_targets) - 5} more[/dim]"
                        )

            if "--parallel" in command_args:
                self.menu.console.print("[dim]• Use parallel execution for speed[/dim]")
            if "--failfast" in command_args:
                self.menu.console.print("[dim]• Stop on first failure[/dim]")

            self.menu.console.print()
            self.menu.console.print("[bold]Options:[/bold]")
            self.menu.console.print("[cyan]R[/cyan] - Run tests")
            self.menu.console.print("[cyan]S[/cyan] - Save this command")
            self.menu.console.print("[cyan]C[/cyan] - Cancel")
            self.menu.console.print()

            choice = Prompt.ask("Your choice", choices=["r", "s", "c"], default="r")

            if choice.lower() == "s":
                # Save the command
                if self.save_current_command(cmd_str):
                    return "saved"
                else:
                    return "cancel"
            elif choice.lower() == "r":
                return "run"
            else:
                return "cancel"

        else:
            print("\n📋 Ready to run tests!")
            print("=" * 40)
            print()

            print(f"Command: {cmd_str}")
            print()

            print("Options:")
            print("[R] Run tests")
            print("[S] Save this command")
            print("[C] Cancel")
            print()

            choice = input("Your choice [R/s/c]: ").strip().lower()

            if choice == "s":
                if self.save_current_command(cmd_str):
                    return "saved"
                else:
                    return "cancel"
            elif choice in ["", "r"]:
                return "run"
            else:
                return "cancel"

    def save_current_command(self, cmd_str: str) -> bool:
        """Save the current command with user input."""
        # Extract just the arguments part (remove 'mercury-test ')
        command = cmd_str.replace("mercury-test ", "")

        if self.menu.use_rich:
            self.menu.console.print("\n[bold yellow]💾 Save Command[/bold yellow]")
            self.menu.console.print("═" * 40)

            name = Prompt.ask("Name this command")
            if not name:
                return False

            description = Prompt.ask("Add description (optional)", default="")

            # Suggest tags based on command
            suggested_tags = []
            if "--parallel" in command:
                suggested_tags.append("parallel")
            if "--failfast" in command:
                suggested_tags.append("fast")
            if "." in command.split()[0] if command else "":
                suggested_tags.append("specific")
            else:
                suggested_tags.append("app")

            tags_str = Prompt.ask(
                f"Tags (comma-separated, suggested: {', '.join(suggested_tags)})",
                default=", ".join(suggested_tags),
            )
            tags = [t.strip() for t in tags_str.split(",") if t.strip()]

        else:
            print("\n💾 Save Command")
            print("=" * 40)

            name = input("Name this command: ").strip()
            if not name:
                return False

            description = input("Add description (optional): ").strip()
            tags = []

        # Save the command
        if self.command_storage.save_command(name, command, description, tags):
            if self.menu.use_rich:
                self.menu.console.print(f'\n[green]✅ Command saved as "{name}"![/green]')
            else:
                print(f'\n✅ Command saved as "{name}"!')
            return True
        else:
            if self.menu.use_rich:
                self.menu.console.print("[red]❌ Failed to save command[/red]")
            else:
                print("❌ Failed to save command")
            return False

    def execute_tests(self, command_args: List[str]) -> int:
        """Execute the tests with the built command."""
        import subprocess

        # Show starting message
        if self.menu.use_rich:
            self.menu.console.print("\n[bold green]🚀 Starting tests...[/bold green]\n")
        else:
            print("\n🚀 Starting tests...\n")

        # Build full command
        cmd = [sys.executable, "-m", "django_mercury.cli.mercury_test"] + command_args

        # Execute
        result = subprocess.run(cmd)

        # Show completion
        if result.returncode == 0:
            if self.menu.use_rich:
                self.menu.console.print(
                    "\n[bold green]✅ Tests completed successfully![/bold green]"
                )
            else:
                print("\n✅ Tests completed successfully!")
        else:
            if self.menu.use_rich:
                self.menu.console.print("\n[bold red]❌ Some tests failed.[/bold red]")
                self.menu.console.print("[dim]Don't worry - failing tests help you learn![/dim]")
            else:
                print("\n❌ Some tests failed.")
                print("Don't worry - failing tests help you learn!")

        return result.returncode
