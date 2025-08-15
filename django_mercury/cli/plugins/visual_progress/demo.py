"""
Visual Progress Demo Mode

Shows an interactive demonstration of the visual test runner.
"""

import random
import time

from .display import MercuryVisualDisplay

try:
    from rich.console import Console

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = object


def show_visual_demo():
    """Show an interactive demo of the visual testing display."""
    if not RICH_AVAILABLE:
        print("Error: Rich library is not installed.")
        print("Please install it with: pip install rich")
        return

    console = Console()
    display = MercuryVisualDisplay(console)

    # Print intro
    console.print(
        "\n[bold cyan]🚀 Django Mercury Visual Testing - Demo Mode[/bold cyan]\n"
    )
    console.print("This is a demonstration of the visual test runner.")
    console.print(
        "When running actual tests, use: [bold]mercury-test --visual [test_path][/bold]\n"
    )

    # Simulate test discovery
    display.start_live_display()
    display.on_discovery_start()
    time.sleep(1)

    # Simulate finding tests
    test_count = 25
    display.on_discovery_complete(test_count)
    time.sleep(1)

    # Simulate running tests
    test_names = [
        ("tests.api.TestUserAPI.test_create", True),
        ("tests.api.TestUserAPI.test_update", True),
        ("tests.api.TestUserAPI.test_delete", True),
        ("tests.models.TestUserModel.test_validation", False),
        ("tests.models.TestUserModel.test_save", False),
        ("tests.views.TestHomeView.test_get", True),
        ("tests.views.TestHomeView.test_post", True),
        ("tests.utils.TestHelpers.test_format_date", False),
        ("tests.utils.TestHelpers.test_parse_json", False),
        ("tests.performance.TestBulkOps.test_bulk_create", True),
        ("tests.performance.TestBulkOps.test_bulk_update", True),
        ("tests.performance.TestCaching.test_cache_hit", True),
        ("tests.auth.TestLogin.test_valid_credentials", False),
        ("tests.auth.TestLogin.test_invalid_password", False),
        ("tests.api.TestProductAPI.test_list", True),
        ("tests.api.TestProductAPI.test_search", True),
        ("tests.api.TestOrderAPI.test_create_order", True),
        ("tests.api.TestOrderAPI.test_cancel_order", True),
        ("tests.models.TestProduct.test_price_calculation", False),
        ("tests.models.TestInventory.test_stock_update", False),
        ("tests.serializers.TestUserSerializer.test_validation", False),
        ("tests.serializers.TestProductSerializer.test_nested", False),
        ("tests.middleware.TestAuthMiddleware.test_token_validation", False),
        ("tests.signals.TestUserSignals.test_post_save", False),
        ("tests.tasks.TestEmailTask.test_send_notification", False),
    ]

    # Run through tests with varying speeds
    for i, (test_name, is_mercury) in enumerate(test_names[:test_count]):
        # Start test
        display.on_test_start(test_name, is_mercury)

        # Simulate test execution with varying duration
        duration = random.uniform(0.05, 0.5)
        time.sleep(duration)

        # Create Mercury metrics for Mercury tests
        mercury_metrics = None
        if is_mercury:
            mercury_metrics = {
                "response_time_ms": random.uniform(20, 200),
                "query_count": random.randint(1, 50),
                "memory_usage_mb": random.uniform(10, 50),
                "grade": random.choice(["S", "A", "A", "B", "B", "B", "C"]),
                "n_plus_one_detected": random.random() < 0.2,  # 20% chance
            }

        # Complete test
        display.on_test_complete(test_name, duration, mercury_metrics)

        # Determine test outcome
        outcome = random.choices(
            ["pass", "fail", "error", "skip"],
            weights=[85, 10, 3, 2],  # 85% pass, 10% fail, 3% error, 2% skip
        )[0]

        if outcome == "pass":
            display.on_test_success(test_name)
        elif outcome == "fail":
            display.on_test_failure(test_name, None)
        elif outcome == "error":
            display.on_test_error(test_name, None)
        else:
            display.on_test_skip(test_name, "Skipped for demo")

        # Add some variation in speed
        if i % 5 == 0:
            time.sleep(0.2)  # Pause occasionally

    # Show final summary
    failures = display.stats["failed"] + display.stats["errors"]
    display.show_final_summary(failures)

    # Print additional info
    console.print("\n[bold green]Demo complete![/bold green]")
    console.print("\nTo run actual tests with visual output:")
    console.print(
        "  [bold]mercury-test --visual[/bold]              # Run all tests"
    )
    console.print(
        "  [bold]mercury-test --visual tests.api[/bold]   # Run specific tests"
    )
    console.print(
        "  [bold]mercury-test --visual --parallel[/bold]  # Run tests in parallel"
    )
    console.print("\nFor more options: [bold]mercury-test --help[/bold]\n")
