#!/usr/bin/env python
"""
Mercury Test Runner - Plugin-Based Console Script for Educational Testing

This module provides a modular, plugin-based command-line tool for running Django tests
with Mercury's educational mode enabled automatically.

Architecture:
    - Small core: Minimal main function that orchestrates plugins
    - Plugin system: Each feature is a self-contained plugin
    - Extensible: Easy to add new features without modifying core

Usage:
    mercury-test                    # Run all tests with educational mode
    mercury-test app.tests          # Run specific app tests
    mercury-test --level advanced   # Set education level
    mercury-test --help            # Show help
"""

import os
import sys
import argparse
import time
import logging
import signal
from pathlib import Path

# Plugin system imports
from .plugins import PluginManager

# Config system imports
from .config import MercuryConfigManager

# Configure logging
logging.basicConfig(level=logging.WARNING)


def find_manage_py(args=None):
    """Find manage.py in current, subdirectories, or one parent directory.

    Args:
        args: Optional parsed arguments (for plugin compatibility)
    """
    # IMPORTANT: Use os.getcwd() to get the actual directory where the user ran the command
    # Path.cwd() might be affected by imports or package location
    current = Path(os.getcwd())

    print(f"🔍 Searching for manage.py starting from: {current}")

    # 1. Check current directory
    manage_path = current / "manage.py"
    if manage_path.exists():
        # Validate this is a Django project by checking for Django indicators
        if _is_valid_django_project(current):
            print(f"✅ Found Django project at: {manage_path}")
            return str(manage_path)
        else:
            print(f"⚠️  Found manage.py at {manage_path} but doesn't look like a Django project")

    # 2. Check immediate subdirectories (one level deep)
    print(f"   Checking subdirectories in: {current}")
    for subdir in current.iterdir():
        if subdir.is_dir():
            manage_path = subdir / "manage.py"
            if manage_path.exists():
                # Validate this is a Django project by checking for Django indicators
                if _is_valid_django_project(subdir):
                    print(f"✅ Found Django project at: {manage_path}")
                    return str(manage_path)
                else:
                    print(
                        f"⚠️  Found manage.py at {manage_path} but doesn't look like a Django project"
                    )

    # 3. Check one parent directory only
    parent = current.parent
    if parent != current:  # Don't check if we're at root
        print(f"   Checking parent: {parent}")
        manage_path = parent / "manage.py"
        if manage_path.exists():
            # Validate this is a Django project by checking for Django indicators
            if _is_valid_django_project(parent):
                print(f"✅ Found Django project at: {manage_path}")
                return str(manage_path)
            else:
                print(f"⚠️  Found manage.py at {manage_path} but doesn't look like a Django project")

    print(f"❌ No Django project found in current, subdirectories, or parent directory")
    return None


def _is_valid_django_project(project_dir):
    """Check if a directory contains a valid Django project.

    Args:
        project_dir: Path to check

    Returns:
        bool: True if it looks like a Django project
    """
    project_path = Path(project_dir)

    # Must have manage.py
    if not (project_path / "manage.py").exists():
        return False

    # Look for Django project indicators
    django_indicators = [
        # Common Django files/directories
        "settings.py",
        "urls.py",
        "wsgi.py",
        "asgi.py",
        # Common app directories
        "apps",
        "requirements.txt",
        "requirements",
        # Virtual environment indicators (suggests development project)
        "venv",
        "env",
        ".venv",
        # Django-specific files
        "db.sqlite3",
        ".env",
        # Python project files
        "pyproject.toml",
        "setup.py",
    ]

    # Check if any Django indicators exist
    for indicator in django_indicators:
        if (project_path / indicator).exists():
            return True

    # Check if there are any Python apps (directories with __init__.py)
    for item in project_path.iterdir():
        if item.is_dir() and (item / "__init__.py").exists():
            # Check if it looks like a Django app (has models.py, views.py, etc.)
            django_app_files = ["models.py", "views.py", "admin.py", "apps.py"]
            if any((item / app_file).exists() for app_file in django_app_files):
                return True

    return False


def _show_profile_help(config_manager):
    """Show helpful information about profiles when --profile is used without a value."""
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.text import Text
        from rich.table import Table
        from rich import box

        rich_available = True
        console = Console()
    except ImportError:
        rich_available = False
        console = None

    if rich_available:
        _show_profile_help_rich(config_manager, console)
    else:
        _show_profile_help_basic(config_manager)


def _show_profile_help_rich(config_manager, console):
    """Show profile help with rich formatting."""
    from rich.text import Text
    from rich.table import Table
    from rich import box

    # Header
    header = Text("🎯 Django Mercury Audience Profiles", style="bold cyan")
    console.print(header)
    console.print("=" * 40, style="dim")

    # Current profile info
    if config_manager:
        try:
            current_profile = config_manager.get_profile()
            config_path = getattr(config_manager, "config_path", "mercury_config.toml")

            # Color current profile based on type
            profile_colors = {"student": "green", "expert": "blue", "agent": "purple"}
            profile_color = profile_colors.get(current_profile, "white")

            console.print(
                f"📋 Current Profile: [bold {profile_color}]{current_profile.title()}[/bold {profile_color}]"
            )
            console.print(f"📁 Config File: [dim]{config_path}[/dim]")
        except Exception:
            console.print("📋 Current Profile: [red]Unknown (no config file)[/red]")
    else:
        console.print("📋 Current Profile: [red]Unknown (no config file)[/red]")

    console.print()

    # Create profiles table
    table = Table(show_header=False, box=box.SIMPLE, padding=(0, 1))
    table.add_column("Profile", style="bold", min_width=20)
    table.add_column("Description", min_width=50)

    # Student profile
    table.add_row(
        "[bold green]🎓 student[/bold green]\n[dim]Educational & Learning[/dim]",
        "[green]• Detailed explanations and tips during tests\n"
        "• Learning suggestions after every test run\n"
        "• Performance guidance and educational content\n"
        "• Slower but teaches Django best practices\n"
        "• Plugins: discovery, wizard, learn, hints[/green]",
    )

    # Expert profile
    table.add_row(
        "[bold blue]⚡ expert[/bold blue]\n[dim]Professional & Efficient[/dim]",
        "[blue]• Fast, concise output focused on results\n"
        "• Minimal educational content\n"
        "• Quick fixes for trivial issues\n"
        "• Optimized for experienced developers\n"
        "• Plugins: discovery, wizard[/blue]",
    )

    # Agent profile
    table.add_row(
        "[bold purple]🤖 agent[/bold purple]\n[dim]AI/Automation[/dim]",
        "[purple]• Structured JSON output for automation\n"
        "• Preserves human decision points\n"
        "• Designed for CI/CD and AI integration\n"
        "• Minimal plugins for automation efficiency[/purple]",
    )

    console.print(table)

    # Usage examples
    console.print("\n💡 [bold yellow]Usage:[/bold yellow]")
    console.print("  [green]mercury-test --profile student[/green]    # Switch to student mode")
    console.print("  [blue]mercury-test --profile expert[/blue]     # Switch to expert mode")
    console.print("  [purple]mercury-test --profile agent[/purple]      # Switch to agent mode")

    # Philosophy
    console.print("\n📚 [bold cyan]80-20 Philosophy:[/bold cyan]")
    console.print("  [bold]80%[/bold] automation handles the [dim]mundane tasks[/dim]")
    console.print(
        "  [bold]20%[/bold] human insight preserves the [bright_yellow]meaningful decisions[/bright_yellow]"
    )


def _show_profile_help_basic(config_manager):
    """Show profile help with basic ANSI colors."""
    # ANSI color codes
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    DIM = "\033[2m"
    RESET = "\033[0m"

    print(f"{CYAN}{BOLD}🎯 Django Mercury Audience Profiles{RESET}")
    print("=" * 40)

    # Show current profile
    if config_manager:
        try:
            current_profile = config_manager.get_profile()
            config_path = getattr(config_manager, "config_path", "mercury_config.toml")

            # Color current profile based on type
            profile_colors = {"student": GREEN, "expert": BLUE, "agent": PURPLE}
            profile_color = profile_colors.get(current_profile, "")

            print(f"📋 Current Profile: {profile_color}{BOLD}{current_profile.title()}{RESET}")
            print(f"📁 Config File: {DIM}{config_path}{RESET}")
        except Exception:
            print(f"📋 Current Profile: {RED}Unknown (no config file){RESET}")
    else:
        print(f"📋 Current Profile: {RED}Unknown (no config file){RESET}")

    print(f"\n{BOLD}🎓 Available Profiles:{RESET}")

    print(f"\n  {GREEN}{BOLD}🎓 student{RESET} - {DIM}Educational & Learning Mode{RESET}")
    print(f"    {GREEN}• Detailed explanations and tips during tests{RESET}")
    print(f"    {GREEN}• Learning suggestions after every test run{RESET}")
    print(f"    {GREEN}• Performance guidance and educational content{RESET}")
    print(f"    {GREEN}• Slower but teaches Django best practices{RESET}")
    print(f"    {GREEN}• Plugins: discovery, wizard, learn, hints{RESET}")

    print(f"\n  {BLUE}{BOLD}⚡ expert{RESET} - {DIM}Professional & Efficient Mode{RESET}")
    print(f"    {BLUE}• Fast, concise output focused on results{RESET}")
    print(f"    {BLUE}• Minimal educational content{RESET}")
    print(f"    {BLUE}• Quick fixes for trivial issues{RESET}")
    print(f"    {BLUE}• Optimized for experienced developers{RESET}")
    print(f"    {BLUE}• Plugins: discovery, wizard{RESET}")

    print(f"\n  {PURPLE}{BOLD}🤖 agent{RESET} - {DIM}AI/Automation Mode{RESET}")
    print(f"    {PURPLE}• Structured JSON output for automation{RESET}")
    print(f"    {PURPLE}• Preserves human decision points{RESET}")
    print(f"    {PURPLE}• Designed for CI/CD and AI integration{RESET}")
    print(f"    {PURPLE}• Minimal plugins for automation efficiency{RESET}")

    print(f"\n{YELLOW}{BOLD}💡 Usage:{RESET}")
    print(f"  {GREEN}mercury-test --profile student{RESET}    # Switch to student mode")
    print(f"  {BLUE}mercury-test --profile expert{RESET}     # Switch to expert mode")
    print(f"  {PURPLE}mercury-test --profile agent{RESET}      # Switch to agent mode")

    print(f"\n{CYAN}{BOLD}📚 80-20 Philosophy:{RESET}")
    print(f"  {BOLD}80%{RESET} automation handles the {DIM}mundane tasks{RESET}")
    print(f"  {BOLD}20%{RESET} human insight preserves the {YELLOW}meaningful decisions{RESET}")


def create_base_parser():
    """Create the base argument parser with core options."""
    parser = argparse.ArgumentParser(
        description="Run Django tests with Mercury Educational Mode (Plugin-Based)",
        prog="mercury-test",
        epilog="Examples:\n"
        "  mercury-test                  # Run all tests\n"
        "  mercury-test users.tests      # Run specific tests\n"
        "  mercury-test --init           # Interactive config setup\n"
        "  mercury-test --profile expert # Switch to expert mode\n"
        "  mercury-test --list-plugins   # Show available plugins",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Test labels (positional arguments)
    parser.add_argument(
        "test_labels", nargs="*", help="Test labels to run (e.g., app.tests.TestCase)"
    )

    # Educational options
    parser.add_argument(
        "--no-pause", action="store_true", help="Disable interactive pauses (useful for CI)"
    )

    # Django test options (pass-through)
    parser.add_argument("--failfast", action="store_true", help="Stop on first test failure")

    parser.add_argument("--keepdb", action="store_true", help="Preserve test database between runs")

    parser.add_argument("--parallel", type=int, metavar="N", help="Run tests in parallel")

    parser.add_argument(
        "--verbosity", type=int, choices=[0, 1, 2, 3], default=1, help="Verbosity level"
    )

    parser.add_argument("--settings", help="Settings module to use")

    parser.add_argument(
        "--project-dir",
        help="Django project directory (where manage.py is located)",
        type=str,
        metavar="DIR",
    )

    parser.add_argument(
        "--manage-py",
        help="Path to manage.py file (overrides auto-discovery)",
        type=str,
        metavar="PATH",
    )

    # Config management arguments
    parser.add_argument(
        "--init", action="store_true", help="Initialize mercury_config.toml with interactive setup"
    )

    parser.add_argument(
        "--profile",
        nargs="?",
        const="help",
        choices=["student", "expert", "agent", "help"],
        help="Switch to audience profile: student (educational), expert (efficient), agent (automation). Use --profile without argument to see details.",
    )

    parser.add_argument(
        "--enable-plugin",
        action="append",
        default=[],
        help="Enable specific plugin (can be used multiple times)",
    )

    parser.add_argument(
        "--disable-plugin",
        action="append",
        default=[],
        help="Disable specific plugin (can be used multiple times)",
    )

    parser.add_argument("--no-config", action="store_true", help="Skip loading mercury_config.toml")

    return parser


def main():
    """Plugin-orchestrated entry point for mercury-test command."""
    # 1. First find the Django project (needed for config)
    manage_py = find_manage_py()
    project_root = Path(manage_py).parent if manage_py else None

    # 2. Create a temporary parser to get basic args (for --init, --no-config, etc)
    temp_parser = create_base_parser()
    temp_args, _ = temp_parser.parse_known_args()

    # 3. Handle config initialization if requested
    if temp_args.init:
        if not project_root:
            print("❌ Error: Could not find Django project (no manage.py found)")
            print("   Please run from your Django project directory")
            return 1

        config_manager = MercuryConfigManager(project_root)
        config_manager.create_config(interactive=True)
        print("\n✅ Configuration complete! Run 'mercury-test' to start testing.")
        return 0

    # 4. Load or create config (unless --no-config)
    config = None
    config_manager = None

    if not temp_args.no_config:
        if project_root:
            config_manager = MercuryConfigManager(project_root)
            try:
                config = config_manager.load_or_create()
                print(
                    f"📋 Using config: mercury_config.toml (profile: {config.get('mercury', {}).get('profile', 'unknown')})"
                )
            except Exception as e:
                logging.warning(f"Could not load config: {e}")
                print("⚠️  Running without config file (limited plugin functionality)")
        else:
            print("⚠️  No Django project found - running without config")

    # 5. Create plugin manager with config (or without)
    # Always enable basic plugins like 'learn' even without config
    if config is None:
        # Create minimal config for essential plugins when no Django project found
        minimal_config = {"plugins": {"enabled": ["learn"]}}  # Always enable learning functionality
        plugin_manager = PluginManager(config=minimal_config, auto_discover=False)
    else:
        plugin_manager = PluginManager(config=config, auto_discover=False)

    # 6. Create final parser and let loaded plugins register their arguments
    parser = create_base_parser()
    plugin_manager.register_all_arguments(parser)

    # 7. Parse all arguments
    args = parser.parse_args()

    # 8. Handle profile switching
    if args.profile:
        if args.profile == "help":
            # User ran --profile without specifying which profile
            _show_profile_help(config_manager)
            return 0
        elif config_manager:
            config_manager.set_profile(args.profile)
            print(f"✅ Switched to '{args.profile}' profile")
            print("   Run 'mercury-test' again to use the new profile")
            return 0

    # 9. Handle plugin enable/disable
    if args.enable_plugin and config_manager:
        for plugin_name in args.enable_plugin:
            try:
                config_manager.enable_plugin(plugin_name)
            except ValueError as e:
                print(f"❌ Error: {e}")
                return 1
        return 0

    if args.disable_plugin and config_manager:
        for plugin_name in args.disable_plugin:
            try:
                config_manager.disable_plugin(plugin_name)
            except ValueError as e:
                print(f"❌ Error: {e}")
                return 1
        return 0

    # 10. Handle special plugin commands
    if hasattr(args, "list_plugins") and args.list_plugins:
        current_profile = (
            config.get("mercury", {}).get("profile", "unknown") if config else "unknown"
        )
        print(plugin_manager.list_plugins(current_profile, config))
        return 0

    # 11. Check if any plugin can handle this request completely
    handler_plugins = plugin_manager.get_handler_plugins(args)
    if handler_plugins:
        # Use the first handler plugin (they're sorted by priority)
        plugin = handler_plugins[0]
        logging.debug(f"Plugin {plugin.name} handling request")
        # Execute the plugin
        return plugin.execute(args, plugin_manager)

    # 12. Default Django test execution with plugin enhancements
    return run_enhanced_django_tests(args, plugin_manager)


def run_enhanced_django_tests(args, plugin_manager):
    """Run Django tests with plugin enhancements."""
    # Store original working directory (where user ran the command)
    original_cwd = Path(os.getcwd())

    # Set up Mercury educational environment
    setup_educational_environment(args)

    # Check if user explicitly provided manage.py path or project directory
    if hasattr(args, "manage_py") and args.manage_py:
        manage_py = args.manage_py
        if not Path(manage_py).exists():
            print(f"Error: Specified manage.py not found: {manage_py}")
            return 1
        print(f"📋 Using specified manage.py: {manage_py}")
    elif hasattr(args, "project_dir") and args.project_dir:
        project_dir = Path(args.project_dir)
        manage_py = str(project_dir / "manage.py")
        if not Path(manage_py).exists():
            print(f"Error: No manage.py found in specified directory: {args.project_dir}")
            return 1
        print(f"📋 Using manage.py from specified project directory: {manage_py}")
    else:
        # Enhanced manage.py discovery using plugins
        discover_func = plugin_manager.enhance_discovery(find_manage_py)
        manage_py = discover_func(args)

        if not manage_py:
            print("Error: Could not find manage.py in current directory or parent directories.")
            print("\nOptions:")
            print("  1. Run mercury-test from your Django project directory")
            print("  2. Use --project-dir to specify the project location:")
            print("     mercury-test --project-dir /path/to/project")
            print("  3. Use --manage-py to specify the exact manage.py path:")
            print("     mercury-test --manage-py /path/to/manage.py")
            print("  4. Try: mercury-test --search-deep (searches more directories)")
            return 1

    # Handle working directory mismatch
    manage_py_path = Path(manage_py)
    manage_py_dir = manage_py_path.parent
    adjusted_args = handle_working_directory_mismatch(args, original_cwd, manage_py_dir)

    # Build Django test command
    cmd_args = build_django_command(adjusted_args, manage_py)

    # Show educational mode banner
    show_educational_banner(adjusted_args, cmd_args)

    # Run pre-test hooks from plugins
    plugin_manager.run_pre_test_hooks(adjusted_args)

    # Execute Django tests with timing
    start_time = time.time()

    # Note: Visual mode is now handled entirely by the plugin system
    # This keeps the core small and delegates features to plugins

    # Use standard Django test execution
    result = execute_django_tests(adjusted_args, cmd_args, manage_py_dir)

    elapsed_time = time.time() - start_time

    # Run post-test hooks from plugins
    plugin_manager.run_post_test_hooks(adjusted_args, result, elapsed_time)

    # Show database tips if there were failures
    if result > 0:
        show_database_tips_if_needed()

    return result


def handle_working_directory_mismatch(args, original_cwd, manage_py_dir):
    """Handle cases where manage.py is in a different directory than where user ran command.

    Args:
        args: Parsed command line arguments
        original_cwd: Directory where user ran mercury-test
        manage_py_dir: Directory where manage.py is located

    Returns:
        Modified args with adjusted test labels if needed
    """
    # If manage.py is in the same directory, no adjustment needed
    if original_cwd == manage_py_dir:
        return args

    # Check if manage.py is in a subdirectory of original_cwd
    try:
        relative_path = manage_py_dir.relative_to(original_cwd)
        # If no test labels specified, Django will auto-discover from current dir
        # We need to find test modules in the original directory
        if not args.test_labels:
            # Create a copy of args to avoid modifying original
            import copy

            adjusted_args = copy.copy(args)

            # Find test modules in original directory
            test_modules = find_test_modules_in_directory(original_cwd, manage_py_dir)

            if test_modules:
                adjusted_args.test_labels = test_modules
                print(f"📂 Found manage.py in subdirectory: {relative_path}")
                print(f"🔍 Discovered tests in original directory: {', '.join(test_modules)}")
            else:
                # Fallback: look for any Python files in original directory
                adjusted_args.test_labels = [str(original_cwd.relative_to(manage_py_dir))]
                print(f"📂 Found manage.py in subdirectory: {relative_path}")
                print(
                    f"🔍 Adjusting test discovery to look in: {original_cwd.relative_to(manage_py_dir)}"
                )

            return adjusted_args

    except ValueError:
        # manage.py is not in a subdirectory of original_cwd
        pass

    return args


def find_test_modules_in_directory(target_dir, from_dir):
    """Find test modules in target directory, returning paths relative to from_dir.

    Args:
        target_dir: Directory to search for tests
        from_dir: Directory to calculate relative paths from (where manage.py is)

    Returns:
        List of test module paths suitable for Django test discovery
    """
    test_modules = []

    try:
        relative_base = target_dir.relative_to(from_dir)

        # Look for common test patterns
        test_patterns = [
            "**/test*.py",
            "**/tests.py",
            "**/tests/",
        ]

        for pattern in test_patterns:
            for test_path in target_dir.glob(pattern):
                if test_path.is_file() and test_path.suffix == ".py":
                    # Convert file path to module path
                    rel_path = test_path.relative_to(from_dir)
                    module_path = str(rel_path.with_suffix("")).replace("/", ".")
                    test_modules.append(module_path)
                elif test_path.is_dir() and (test_path / "__init__.py").exists():
                    # It's a test package
                    rel_path = test_path.relative_to(from_dir)
                    module_path = str(rel_path).replace("/", ".")
                    test_modules.append(module_path)

        # Remove duplicates and sort
        return sorted(list(set(test_modules)))

    except Exception:
        # Fallback: just return the relative directory path
        try:
            rel_path = target_dir.relative_to(from_dir)
            return [str(rel_path).replace("/", ".")]
        except ValueError:
            return []


def setup_educational_environment(args):
    """Set up Mercury educational environment variables."""
    os.environ["MERCURY_EDU"] = "1"
    os.environ["MERCURY_EDUCATIONAL_MODE"] = "true"
    # Profile determines level now, not a separate --level flag

    if args.no_pause:
        os.environ["MERCURY_NON_INTERACTIVE"] = "1"
    else:
        # Explicitly set interactive mode
        os.environ["MERCURY_INTERACTIVE"] = "1"
        # Make sure non-interactive is not set
        if "MERCURY_NON_INTERACTIVE" in os.environ:
            del os.environ["MERCURY_NON_INTERACTIVE"]


def build_django_command(args, manage_py):
    """Build the Django test command arguments."""
    cmd_args = [sys.executable, manage_py, "test"]

    # Add test labels
    if args.test_labels:
        cmd_args.extend(args.test_labels)

    # Add Django options
    if args.failfast:
        cmd_args.append("--failfast")

    if args.keepdb:
        cmd_args.append("--keepdb")

    if args.parallel:
        cmd_args.extend(["--parallel", str(args.parallel)])

    if args.verbosity is not None:
        cmd_args.extend(["--verbosity", str(args.verbosity)])

    if args.settings:
        cmd_args.extend(["--settings", args.settings])

    return cmd_args


def show_educational_banner(args, cmd_args):
    """Show the educational mode banner."""
    print("=" * 60)
    print("🎓 Django Mercury Testing Framework")
    print("=" * 60)
    # Profile is shown earlier when config is loaded
    print(f"Interactive: {'No' if args.no_pause else 'Yes'}")
    print(f"Running: {' '.join(cmd_args)}")
    print("=" * 60)
    print()


def show_database_tips_if_needed():
    """Show database configuration tips if database errors were detected."""
    # Check if we've seen database errors (this is set by visual test runner)
    if os.environ.get("MERCURY_DB_ERROR_DETECTED"):
        print("\n" + "=" * 70)
        print("💡 Database Permission Error Detected!")
        print("=" * 70)
        print("\n🔧 Quick Fix:")
        print("  1. Run this in your project directory:")
        print("     ./fix_test_db.sh")
        print("\n  2. Or manually fix permissions:")
        print("     rm -f test_*.sqlite3")
        print("     chmod 755 .")
        print("\n⚡ For Faster Tests, add to your settings.py:")
        print("  import sys")
        print("  if 'test' in sys.argv:")
        print("      DATABASES['default']['NAME'] = ':memory:'")
        print("\n📚 Learn more: mercury-test --learn database_optimization")
        print("=" * 70 + "\n")
        # Clear the flag
        del os.environ["MERCURY_DB_ERROR_DETECTED"]


# Note: Visual test execution functions have been removed
# This follows the "small core, large plugin ecosystem" architecture


def execute_django_tests(args, cmd_args, manage_py_dir):
    """Execute the Django test command."""
    import subprocess

    # Store current directory to restore later
    original_cwd = os.getcwd()

    try:
        # Change to manage.py directory for proper Django execution
        os.chdir(manage_py_dir)

        # For interactive mode, we need to preserve TTY
        if not args.no_pause:
            # Pass through stdin/stdout/stderr to preserve TTY
            result = subprocess.run(cmd_args, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
        else:
            # Non-interactive mode, normal subprocess
            result = subprocess.run(cmd_args)

        return result.returncode

    finally:
        # Always restore original working directory
        os.chdir(original_cwd)


if __name__ == "__main__":
    main()
