"""
Visual Progress Plugin for Mercury-Test CLI

Main plugin entry point that orchestrates visual test execution.
"""

import logging
import os
import re
import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

from django_mercury.cli.plugins.base import MercuryPlugin

from .demo import show_visual_demo
from .display import RICH_AVAILABLE, MercuryVisualDisplay
from .output_capture import show_suppressed_logs, start_early_capture
from .test_runner import DJANGO_AVAILABLE, MercuryVisualTestRunner

try:
    from rich.console import Console
except ImportError:
    Console = object


class VisualProgressPlugin(MercuryPlugin):
    """Plugin for enhanced visual progress during test execution."""

    name = "visual_progress"
    description = "Rich visual feedback during test execution"
    priority = 50  # Medium priority
    version = "2.0.0"  # Bumped version for refactored architecture

    # Audience targeting
    audiences = ["student", "expert"]  # Visual feedback helps both audiences
    complexity_level = 2  # Moderate - requires understanding of progress bars
    requires_capabilities = ["rich", "django"]  # Needs rich library and Django

    def __init__(self):
        super().__init__()
        self.console = Console() if RICH_AVAILABLE else None

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register visual progress arguments."""
        parser.add_argument(
            "--visual",
            action="store_true",
            help="Enable rich visual progress display",
        )

        parser.add_argument(
            "--no-visual",
            action="store_true",
            help="Disable visual progress (use simple output)",
        )

        parser.add_argument(
            "--visual-theme",
            choices=["default", "minimal", "detailed"],
            default="default",
            help="Visual progress theme",
        )

        parser.add_argument(
            "--visual-refresh",
            type=int,
            default=100,
            help="Visual refresh rate in milliseconds (default: 100)",
        )

        parser.add_argument(
            "--show-logs",
            action="store_true",
            help="Show suppressed logs after visual tests complete",
        )

        parser.add_argument(
            "--save-logs",
            action="store_true",
            help="Save suppressed logs to test_output.log file",
        )

    def can_handle(self, args: Namespace) -> bool:
        """Check if this plugin should handle the request."""
        # Handle --visual when test labels are provided (run tests with visual mode)
        # OR when --visual is used alone (demo mode)
        if getattr(args, "visual", False):
            # Check if any test labels were provided
            has_test_labels = (
                hasattr(args, "test_labels")
                and args.test_labels
                and len(args.test_labels) > 0
            )
            # Check if any other command flags are present
            has_other_commands = any(
                [
                    getattr(args, "ext", False),
                    getattr(args, "list_plugins", False),
                    getattr(args, "version", False),
                ]
            )

            # Handle if --visual is specified and either:
            # 1. Test labels are provided (run tests)
            # 2. No test labels and no other commands (demo mode)
            if has_test_labels or (
                not has_test_labels and not has_other_commands
            ):
                return True

        return False

    def execute(self, args: Namespace) -> int:
        """Execute visual tests or demo based on arguments."""
        if not RICH_AVAILABLE:
            print("Error: Rich library is not installed.")
            print("Please install it with: pip install rich")
            return 1

        # Check if we have test labels to run
        has_test_labels = (
            hasattr(args, "test_labels")
            and args.test_labels
            and len(args.test_labels) > 0
        )

        if has_test_labels:
            # Run actual tests with visual mode
            return self.run_visual_tests(args)
        else:
            # Show interactive demo when no test labels
            show_visual_demo()
            return 0

    def run_visual_tests(self, args: Namespace) -> int:
        """Run Django tests with visual output directly (no subprocess)."""
        # Start capturing output immediately
        save_logs = getattr(args, "save_logs", False)
        capture = start_early_capture(save_to_file=save_logs)

        # Check Django availability
        if not DJANGO_AVAILABLE:
            capture.stop_capture()
            print("❌ Error: Django is not available")
            print("   Please ensure Django is installed: pip install django")
            return 1

        # Starting visual test runner

        # Find manage.py path
        manage_py = self._find_manage_py(args)
        if not manage_py:
            capture.stop_capture()
            print("❌ Error: Could not find manage.py")
            print("   Please run from a Django project directory")
            return 1

        manage_py_path = Path(manage_py)
        manage_py_dir = manage_py_path.parent

        # Store current directory to restore later
        original_cwd = os.getcwd()

        try:
            # Change to manage.py directory
            os.chdir(manage_py_dir)

            # Detect settings module from manage.py
            settings_module = self._detect_settings_module(manage_py_path)
            if not settings_module:
                capture.stop_capture()
                print("❌ Error: Could not detect Django settings module.")
                print(
                    "   Please set DJANGO_SETTINGS_MODULE environment variable."
                )
                return 1

            # Set up Django environment
            sys.path.insert(0, str(manage_py_dir))
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)

            # Set test mode flag for settings to detect
            os.environ["DJANGO_TEST_MODE"] = "1"

            # Completely silence Django logging in visual mode
            self._silence_django_logging()

            # Import Django and setup
            import django

            django.setup()

            # Create visual display with proper config
            console = Console()
            
            # Load Mercury config to check for hints plugin and profile
            hints_enabled = False
            profile = 'expert'
            try:
                from django_mercury.cli.config.config_manager import MercuryConfigManager
                config_manager = MercuryConfigManager()
                config_manager.load_config()
                hints_enabled = 'hints' in config_manager.get_enabled_plugins()
                profile = config_manager.get_profile()
            except Exception:
                # If config loading fails, default to no hints and expert profile
                pass
            
            visual_display = MercuryVisualDisplay(console, hints_enabled=hints_enabled, profile=profile)

            # Hand off any captured output to the visual display
            capture.handoff_to_display(visual_display)

            # Create visual test runner with proper configuration
            runner = MercuryVisualTestRunner(
                verbosity=0,  # Quiet Django's default output
                interactive=False,
                failfast=getattr(args, "failfast", False),
                keepdb=getattr(args, "keepdb", False),
                parallel=getattr(args, "parallel", None)
                or 0,  # Handle None properly
            )
            
            # Set the visual display we created with proper config
            runner.visual_display = visual_display

            # Run tests with visual feedback
            test_labels = (
                args.test_labels if hasattr(args, "test_labels") else []
            )
            failures = runner.run_tests(test_labels)

            # Show suppressed logs if requested
            if getattr(args, "show_logs", False):
                capture.stop_capture()
                show_suppressed_logs(limit=100)

            return failures

        except ImportError as e:
            capture.stop_capture()
            print(f"❌ Error setting up Django environment: {e}")
            print("   Make sure you're in a Django project directory.")
            return 1
        except Exception as e:
            capture.stop_capture()
            print(f"❌ Error running visual tests: {e}")
            import traceback

            traceback.print_exc()
            return 1
        finally:
            # Always restore original working directory
            os.chdir(original_cwd)

    def _find_manage_py(self, args: Namespace) -> str | None:
        """Find manage.py file in project."""
        # Check if user specified manage.py path
        if hasattr(args, "manage_py") and args.manage_py:
            if Path(args.manage_py).exists():
                return str(Path(args.manage_py))

        # Check if user specified project directory
        if hasattr(args, "project_dir") and args.project_dir:
            project_dir = Path(args.project_dir)
            manage_py = project_dir / "manage.py"
            if manage_py.exists():
                return str(manage_py)

        # Search in current and parent directories
        current = Path.cwd()
        for _ in range(4):  # Check up to 3 parent directories
            manage_py = current / "manage.py"
            if manage_py.exists():
                return str(manage_py)

            if current == current.parent:
                break
            current = current.parent

        return None

    def _silence_django_logging(self):
        """
        Completely silence all Django logging in visual mode.
        This prevents any warnings or errors from appearing during visual tests.
        """

        # Create a NullHandler that discards everything
        class SilentHandler(logging.Handler):
            def emit(self, record):
                pass  # Discard all log records

        # Get the root logger and clear existing handlers
        root_logger = logging.getLogger()
        root_logger.handlers = []
        root_logger.addHandler(SilentHandler())
        root_logger.setLevel(logging.CRITICAL + 1)  # Higher than CRITICAL

        # Silence all Django-related loggers
        django_loggers = [
            "django",
            "django.request",
            "django.db",
            "django.db.backends",
            "django.db.backends.schema",
            "django.security",
            "django.security.csrf",
            "django.template",
            "django.utils.autoreload",
            "django.server",
            "django.contrib",
            "django.contrib.sessions",
            "django.contrib.staticfiles",
            "rest_framework",
            "rest_framework.request",
        ]

        for logger_name in django_loggers:
            logger = logging.getLogger(logger_name)
            logger.handlers = []
            logger.addHandler(SilentHandler())
            logger.setLevel(logging.CRITICAL + 1)
            logger.propagate = False

        # Also silence warnings module
        import warnings

        warnings.filterwarnings("ignore")

        # Disable Django's default logging configuration
        os.environ["DJANGO_LOG_LEVEL"] = "CRITICAL"
        logging.disable(logging.CRITICAL)

    def _detect_settings_module(self, manage_py_path: Path) -> str | None:
        """Detect Django settings module from manage.py."""
        if manage_py_path.exists():
            with open(manage_py_path) as f:
                content = f.read()
                # Look for os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xxx')
                match = re.search(
                    r"os\.environ\.setdefault\(['\"]DJANGO_SETTINGS_MODULE['\"],\s*['\"]([^'\"]+)['\"]",
                    content,
                )
                if match:
                    return match.group(1)

        # Try common patterns
        project_name = manage_py_path.parent.name
        for pattern in [
            f"{project_name}.settings",
            "config.settings",
            "settings",
        ]:
            try:
                __import__(pattern)
                return pattern
            except ImportError:
                continue

        return None

    def pre_test_hook(self, args: Namespace) -> None:
        """Setup visual progress before tests start."""
        # Skip hooks if using --visual with test labels (new runner handles it)
        if (
            getattr(args, "visual", False)
            and hasattr(args, "test_labels")
            and args.test_labels
            and len(args.test_labels) > 0
        ):
            return  # Let the new visual test runner handle this

    def post_test_hook(
        self, args: Namespace, result: int, elapsed_time: float
    ) -> None:
        """Cleanup visual progress after tests complete."""
        # Skip hooks if using --visual with test labels (new runner handles it)
        if (
            getattr(args, "visual", False)
            and hasattr(args, "test_labels")
            and args.test_labels
            and len(args.test_labels) > 0
        ):
            return  # Let the new visual test runner handle this
