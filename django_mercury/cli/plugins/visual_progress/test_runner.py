"""
Mercury Visual Test Runner

Django test runner with proper database setup and visual output.
"""

import logging
import os
import signal
import sys
import unittest

try:
    from django.test.runner import DiscoverRunner

    DJANGO_AVAILABLE = True
except ImportError:
    DJANGO_AVAILABLE = False
    DiscoverRunner = object

from .display import RICH_AVAILABLE, MercuryVisualDisplay
from .monitor_hook import disable_mercury_hook, enable_mercury_hook
from .test_result import MercuryVisualTestResult

# Try to import Rich console
try:
    from rich.console import Console
except ImportError:
    Console = object


class MercuryVisualTestRunner(DiscoverRunner):
    """
    Django test runner with Mercury visual output and proper database setup.
    """

    def __init__(self, **kwargs):
        # Ensure complete silence in visual mode
        self._ensure_silence()

        # Set up interrupt handling
        self.interrupted = False
        self.original_sigint_handler = signal.signal(signal.SIGINT, self._handle_interrupt)

        # Check if Rich is available
        if not RICH_AVAILABLE:
            # Fall back to standard runner silently
            super().__init__(**kwargs)
            self.visual_display = None
            return

        # Force non-interactive and quiet mode for visual runner
        kwargs["interactive"] = False
        kwargs["verbosity"] = 0
        # Configure Django test runner

        try:
            super().__init__(**kwargs)
            # Django DiscoverRunner initialized
        except Exception:
            # Failed to initialize Django DiscoverRunner
            raise

        # Initialize visual display to None - it will be set by the plugin
        self.visual_display = None

    def _handle_interrupt(self, signum, frame):
        """Handle Ctrl+C gracefully."""
        self.interrupted = True
        print("\n\n⚠️  Test execution interrupted by user (Ctrl+C)")

        if self.visual_display and self.visual_display.live:
            # Stop the live display cleanly
            try:
                self.visual_display.live.stop()
            except:
                pass

        # Show summary of what was completed
        if hasattr(self.visual_display, "stats"):
            stats = self.visual_display.stats
            completed = stats["passed"] + stats["failed"] + stats["errors"] + stats["skipped"]
            print(f"\n📊 Tests completed before interruption: {completed}/{stats['total']}")
            if stats["passed"] > 0:
                print(f"✅ Passed: {stats['passed']}")
            if stats["failed"] > 0:
                print(f"❌ Failed: {stats['failed']}")
            if stats["errors"] > 0:
                print(f"💥 Errors: {stats['errors']}")
            if stats["skipped"] > 0:
                print(f"⏭️  Skipped: {stats['skipped']}")

        print("\nUse 'mercury-test --visual [specific_test]' to run individual tests.")

        # Restore original handler and re-raise to exit
        signal.signal(signal.SIGINT, self.original_sigint_handler)
        raise KeyboardInterrupt()

    def run_tests(self, test_labels, **kwargs):
        """
        Run tests with proper database setup and visual output.

        This properly follows Django's test flow:
        1. Setup test environment
        2. Build test suite
        3. Setup databases (CRITICAL!)
        4. Run tests with visual display
        5. Teardown databases
        6. Teardown test environment
        """
        # Ensure logging is completely silenced again
        self._ensure_silence()

        # Clear screen for clean visual display
        os.system("clear" if os.name == "posix" else "cls")

        # If no visual display, fall back to standard runner
        if not self.visual_display:
            # Fall back silently to standard runner
            return super().run_tests(test_labels, **kwargs)

        # Using visual display for test execution

        # Force Django to keep query logging enabled
        try:
            from django.conf import settings

            settings.DEBUG = True
        except:
            pass

        # Enable Mercury monitoring hook to capture metrics
        enable_mercury_hook()

        # 1. Setup test environment
        # Setup test environment
        self.setup_test_environment()

        # 2. Build test suite
        # Build test suite
        self.visual_display.start_live_display()
        self.visual_display.on_discovery_start()

        suite = self.build_suite(test_labels)
        test_count = suite.countTestCases()

        # Discovered tests
        self.visual_display.on_discovery_complete(test_count)

        # 3. CRITICAL: Setup databases - this was missing!
        # Setup test databases
        old_config = None
        try:
            # Get databases needed for this test suite
            databases = self.get_databases(suite)
            # Databases to setup

            # Setup the test databases
            old_config = self.setup_databases(
                aliases=databases,
                serialized_aliases=getattr(suite, "serialized_aliases", set()),
            )
            # Test databases setup complete

            # 4. Run checks after database setup
            # Run Django system checks
            self.run_checks(databases)
            # System checks passed

            # 5. Run the actual tests with visual display
            # Run test suite with visual display
            result = self._run_visual_suite(suite)

            # Check if we were interrupted
            if self.interrupted:
                return 1  # Return error code for interruption

            # Calculate failures
            failures = len(result.failures) + len(result.errors)

            # Show final summary
            self.visual_display.show_final_summary(failures)

            return failures

        except KeyboardInterrupt:
            # Handle interruption during test execution
            if self.visual_display:
                self.visual_display.add_to_log_buffer("⚠️ Test interrupted")
            return 1
        except Exception as e:
            # Handle unexpected errors
            # Unexpected error during test execution
            if self.visual_display:
                self.visual_display.add_to_log_buffer(f"❌ Error: {str(e)[:40]}")
            if self.visual_display and self.visual_display.live:
                try:
                    self.visual_display.live.stop()
                except:
                    pass
            return 1
        finally:
            # 6. CRITICAL: Always teardown databases and test environment
            # Cleaning up

            # Disable and clear Mercury monitoring hook
            from .monitor_hook import get_mercury_hook

            get_mercury_hook().clear()  # Clear all data before disabling
            disable_mercury_hook()

            if old_config:
                try:
                    # Tearing down test databases
                    self.teardown_databases(old_config)
                    # Databases torn down
                except Exception:
                    # Error tearing down databases
                    pass

            try:
                # Tearing down test environment
                self.teardown_test_environment()
                # Test environment torn down
            except Exception:
                # Error tearing down test environment
                pass

            # Ensure signal handler is restored
            if hasattr(self, "original_sigint_handler"):
                signal.signal(signal.SIGINT, self.original_sigint_handler)

    def _ensure_silence(self):
        """
        Ensure complete silence of all logging and warnings.
        Called multiple times to catch any loggers created after initial setup.
        """
        import warnings

        # Silence warnings
        warnings.filterwarnings("ignore")
        warnings.simplefilter("ignore")

        # Disable all logging
        logging.disable(logging.CRITICAL + 1)

        # Set all existing loggers to maximum level
        for name in list(logging.root.manager.loggerDict.keys()):
            logger = logging.getLogger(name)
            logger.setLevel(logging.CRITICAL + 1)
            logger.propagate = False
            # Clear handlers
            logger.handlers = []

        # Ensure root logger is silenced
        root = logging.getLogger()
        root.setLevel(logging.CRITICAL + 1)
        root.handlers = []

    def _run_visual_suite(self, suite):
        """Run the test suite with visual display."""
        # Ensure silence before running tests
        self._ensure_silence()

        # Create visual result factory that captures visual_display
        visual_display = self.visual_display

        def create_visual_result(stream=None, descriptions=None, verbosity=None):
            return MercuryVisualTestResult(
                stream=stream,
                descriptions=descriptions,
                verbosity=verbosity,
                visual_display=visual_display,
            )

        # Create custom runner with our visual result factory
        runner = unittest.TextTestRunner(
            resultclass=create_visual_result, stream=sys.stderr, verbosity=0
        )

        # Run the test suite
        return runner.run(suite)

    def get_databases(self, suite):
        """
        Get the set of databases required to run this test suite.

        This is a method from Django 4.0+ that we need to handle for older versions.
        """
        if hasattr(super(), "get_databases"):
            # Django 4.0+ has this method
            return super().get_databases(suite)
        else:
            # For older Django versions, return all database aliases
            from django.db import connections

            return set(connections)
