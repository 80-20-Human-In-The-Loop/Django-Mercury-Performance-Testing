"""Comprehensive tests for Django Mercury CLI module.

This test module ensures full coverage of the CLI functionality including
educational mode, agent mode, and progress tracking.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, mock_open, call

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from django_mercury.python_bindings.cli import MercuryEducationalCLI, main
from django_mercury.python_bindings.educational_guidance import EduLiteColorScheme


class TestMercuryEducationalCLI(unittest.TestCase):
    """Test the MercuryEducationalCLI class."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.progress_file = Path(self.temp_dir) / ".django_mercury" / "progress.json"
        
    def tearDown(self) -> None:
        """Clean up after tests."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_cli_initialization_without_rich(self) -> None:
        """Test CLI initialization when Rich is not available."""
        with patch('django_mercury.python_bindings.cli.RICH_AVAILABLE', False):
            cli = MercuryEducationalCLI()
            self.assertIsNone(cli.console)
            self.assertIsInstance(cli.color_scheme, EduLiteColorScheme)
            self.assertFalse(cli.educational_mode)
            self.assertFalse(cli.agent_mode)
            
    def test_cli_initialization_with_rich(self) -> None:
        """Test CLI initialization when Rich is available."""
        with patch('django_mercury.python_bindings.cli.RICH_AVAILABLE', True):
            with patch('django_mercury.python_bindings.cli.Console') as MockConsole:
                cli = MercuryEducationalCLI()
                self.assertIsNotNone(cli.console)
                MockConsole.assert_called_once()
                
    def test_load_progress_no_file(self) -> None:
        """Test loading progress when no file exists."""
        with patch.object(Path, 'exists', return_value=False):
            cli = MercuryEducationalCLI()
            expected_progress = {
                "concepts_learned": [],
                "quiz_scores": {},
                "optimization_attempts": 0,
                "level": "beginner",
            }
            self.assertEqual(cli.progress_data, expected_progress)
            
    def test_load_progress_with_file(self) -> None:
        """Test loading progress from existing file."""
        progress_data = {
            "concepts_learned": ["n_plus_one", "caching"],
            "quiz_scores": {"quiz1": 80, "quiz2": 90},
            "optimization_attempts": 5,
            "level": "intermediate",
        }
        
        with patch.object(Path, 'exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=json.dumps(progress_data))):
                cli = MercuryEducationalCLI()
                self.assertEqual(cli.progress_data, progress_data)
                
    def test_load_progress_corrupted_file(self) -> None:
        """Test loading progress with corrupted JSON file."""
        with patch.object(Path, 'exists', return_value=True):
            with patch('builtins.open', mock_open(read_data="invalid json")):
                cli = MercuryEducationalCLI()
                # Should return default progress on JSON error
                self.assertEqual(cli.progress_data["level"], "beginner")
                
    def test_save_progress(self) -> None:
        """Test saving progress to file."""
        cli = MercuryEducationalCLI()
        cli.progress_file = Path(self.temp_dir) / "test_progress.json"
        cli.progress_data = {
            "concepts_learned": ["test_concept"],
            "quiz_scores": {"test": 100},
            "optimization_attempts": 1,
            "level": "expert",
        }
        
        cli._save_progress()
        
        # Verify file was created and contains correct data
        self.assertTrue(cli.progress_file.exists())
        with open(cli.progress_file) as f:
            saved_data = json.load(f)
        self.assertEqual(saved_data, cli.progress_data)
        
    def test_display_welcome_without_console(self) -> None:
        """Test welcome display without Rich console."""
        cli = MercuryEducationalCLI()
        cli.console = None
        
        with patch('builtins.print') as mock_print:
            cli.display_welcome()
            mock_print.assert_called()
            # Check that basic welcome message was printed
            calls = mock_print.call_args_list
            self.assertTrue(any("Django Mercury Educational Mode" in str(call) for call in calls))
            
    def test_display_welcome_with_console(self) -> None:
        """Test welcome display with Rich console."""
        cli = MercuryEducationalCLI()
        cli.console = Mock()
        
        cli.display_welcome()
        cli.console.print.assert_called_once()
        
    @patch('builtins.__import__', side_effect=ImportError("Django not installed"))
    def test_run_educational_test_django_not_configured(self, mock_import) -> None:
        """Test running educational test when Django is not configured."""
        cli = MercuryEducationalCLI()
        cli.console = Mock()
        
        result = cli.run_educational_test()
        self.assertEqual(result, 1)  # Should return error code
        
    def test_run_educational_test_success(self) -> None:
        """Test successful educational test run."""
        # Create proper mock hierarchy
        mock_django = MagicMock()
        mock_settings = MagicMock()
        
        # Create a proper test runner class that can be instantiated
        class MockTestRunner:
            def __init__(self, *args, **kwargs) -> None:
                self.verbosity = kwargs.get('verbosity', 2)
                self.interactive = kwargs.get('interactive', True)
                self.cli_instance = kwargs.get('cli_instance')
                
            def setup_test_environment(self, **kwargs):
                pass
                
            def run_tests(self, test_labels):
                return 0  # No failures
        
        # Mock get_runner to return our MockTestRunner class
        mock_get_runner = Mock(return_value=MockTestRunner)
        
        # Apply patches
        with patch.dict('sys.modules', {
            'django': mock_django,
            'django.conf': Mock(settings=mock_settings),
            'django.test.utils': Mock(get_runner=mock_get_runner)
        }):
            cli = MercuryEducationalCLI()
            cli.console = Mock()
            cli._save_progress = Mock()
            cli._show_learning_summary = Mock()
            
            result = cli.run_educational_test("test_path")
            
            self.assertEqual(result, 0)  # Success
            cli._save_progress.assert_called_once()
            cli._show_learning_summary.assert_called_once()
        
    def test_show_learning_summary_without_console(self) -> None:
        """Test learning summary without console."""
        cli = MercuryEducationalCLI()
        cli.console = None
        
        # Should not raise any errors
        cli._show_learning_summary()
        
    def test_show_learning_summary_with_console(self) -> None:
        """Test learning summary with Rich console."""
        cli = MercuryEducationalCLI()
        cli.console = Mock()
        cli.progress_data = {
            "concepts_learned": ["n_plus_one", "caching"],
            "quiz_scores": {"quiz1": 80, "quiz2": 90},
            "optimization_attempts": 3,
            "level": "intermediate",
        }
        
        cli._show_learning_summary()
        cli.console.print.assert_called_once()
        
    def test_run_agent_mode(self) -> None:
        """Test agent mode with JSON output."""
        # Create proper mock hierarchy
        mock_django = MagicMock()
        mock_settings = MagicMock()
        
        # Create a proper test runner class
        class MockTestRunner:
            def __init__(self, *args, **kwargs) -> None:
                self.verbosity = kwargs.get('verbosity', 2)
                self.interactive = kwargs.get('interactive', True)
                self.cli_instance = kwargs.get('cli_instance')
                
            def setup_test_environment(self, **kwargs):
                pass
                
            def run_tests(self, test_labels):
                return 0  # No failures
        
        # Mock get_runner to return our MockTestRunner class
        mock_get_runner = Mock(return_value=MockTestRunner)
        
        with patch.dict('sys.modules', {
            'django': mock_django,
            'django.conf': Mock(settings=mock_settings),
            'django.test.utils': Mock(get_runner=mock_get_runner)
        }):
            cli = MercuryEducationalCLI()
            cli._save_progress = Mock()
            
            with patch('builtins.print') as mock_print:
                result = cli.run_agent_mode("test_path")
                
            self.assertEqual(result, 0)
            self.assertTrue(cli.agent_mode)
            self.assertEqual(os.environ.get("MERCURY_AGENT_MODE"), "true")
            
            # Verify JSON output was printed
            mock_print.assert_called()
            output = mock_print.call_args[0][0]
            parsed_output = json.loads(output)
            self.assertIn("version", parsed_output)
            self.assertEqual(parsed_output["mode"], "agent")
            self.assertTrue(parsed_output["success"])


class TestCLIMain(unittest.TestCase):
    """Test the main entry point of the CLI."""
    
    @patch('sys.argv', ['mercury-analyze', '--version'])
    @patch('django_mercury.python_bindings.cli.VERSION', '1.0.0')
    def test_main_version(self) -> None:
        """Test --version flag."""
        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stdout', new_callable=Mock) as mock_stdout:
                main()
        # argparse exits with 0 for --version
        self.assertEqual(cm.exception.code, 0)
        
    @patch('sys.argv', ['mercury-analyze', '--reset-progress'])
    @patch('django_mercury.python_bindings.cli.MercuryEducationalCLI')
    def test_main_reset_progress(self, MockCLI) -> None:
        """Test --reset-progress flag."""
        mock_cli_instance = Mock()
        mock_cli_instance.console = Mock()
        MockCLI.return_value = mock_cli_instance
        
        main()
        
        mock_cli_instance._save_progress.assert_called_once()
        # Verify progress was reset
        self.assertEqual(mock_cli_instance.progress_data["level"], "beginner")
        
    @patch('sys.argv', ['mercury-analyze', '--edu'])
    @patch('django_mercury.python_bindings.cli.MercuryEducationalCLI')
    def test_main_educational_mode(self, MockCLI) -> None:
        """Test --edu flag."""
        mock_cli_instance = Mock()
        mock_cli_instance.run_educational_test.return_value = 0
        MockCLI.return_value = mock_cli_instance
        
        with self.assertRaises(SystemExit) as cm:
            main()
            
        self.assertEqual(cm.exception.code, 0)
        self.assertTrue(mock_cli_instance.educational_mode)
        mock_cli_instance.run_educational_test.assert_called_once()
        
    @patch('sys.argv', ['mercury-analyze', '--agent'])
    @patch('django_mercury.python_bindings.cli.MercuryEducationalCLI')
    def test_main_agent_mode(self, MockCLI) -> None:
        """Test --agent flag."""
        mock_cli_instance = Mock()
        mock_cli_instance.run_agent_mode.return_value = 0
        MockCLI.return_value = mock_cli_instance
        
        with self.assertRaises(SystemExit) as cm:
            main()
            
        self.assertEqual(cm.exception.code, 0)
        mock_cli_instance.run_agent_mode.assert_called_once()
        
    @patch('sys.argv', ['mercury-analyze', 'myapp.tests'])
    @patch('django_mercury.python_bindings.cli.MercuryEducationalCLI')
    def test_main_with_test_path(self, MockCLI) -> None:
        """Test running with specific test path."""
        mock_cli_instance = Mock()
        mock_cli_instance.console = Mock()
        mock_cli_instance.run_educational_test.return_value = 0
        MockCLI.return_value = mock_cli_instance
        
        with self.assertRaises(SystemExit) as cm:
            main()
            
        self.assertEqual(cm.exception.code, 0)
        mock_cli_instance.run_educational_test.assert_called_with('myapp.tests')
        
    @patch('sys.argv', ['mercury-analyze'])
    @patch('django_mercury.python_bindings.cli.MercuryEducationalCLI')
    def test_main_default_mode(self, MockCLI) -> None:
        """Test default mode without flags."""
        mock_cli_instance = Mock()
        mock_cli_instance.console = None  # Test without Rich
        mock_cli_instance.run_educational_test.return_value = 0
        MockCLI.return_value = mock_cli_instance
        
        with patch('builtins.print') as mock_print:
            with self.assertRaises(SystemExit) as cm:
                main()
                
        self.assertEqual(cm.exception.code, 0)
        # Should show tip about --edu flag
        mock_print.assert_called()
        self.assertTrue(any("--edu" in str(call) for call in mock_print.call_args_list))


class TestEducationalGuidance(unittest.TestCase):
    """Test the educational guidance module."""
    
    def test_color_scheme_initialization(self) -> None:
        """Test EduLiteColorScheme initialization."""
        scheme = EduLiteColorScheme()
        self.assertIn('success', scheme.colors)
        self.assertIn('error', scheme.ansi_colors)
        
    def test_colorize_text(self) -> None:
        """Test text colorization."""
        scheme = EduLiteColorScheme()
        
        # Test basic colorization
        colored = scheme.colorize("Test", "success")
        self.assertIn("Test", colored)
        self.assertIn('\033[32m', colored)  # Green color code
        self.assertIn('\033[0m', colored)   # Reset code
        
        # Test bold colorization
        bold_colored = scheme.colorize("Bold Test", "error", bold=True)
        self.assertIn('\033[1m', bold_colored)  # Bold code
        
        # Test invalid color type
        unchanged = scheme.colorize("Test", "invalid_color")
        self.assertEqual(unchanged, "Test")
        
    def test_get_hex_color(self) -> None:
        """Test getting hex color codes."""
        scheme = EduLiteColorScheme()
        
        # Test valid color
        hex_color = scheme.get_hex_color("success")
        self.assertEqual(hex_color, '#75a743')
        
        # Test invalid color
        no_color = scheme.get_hex_color("invalid")
        self.assertIsNone(no_color)
        
    def test_format_messages(self) -> None:
        """Test message formatting methods."""
        scheme = EduLiteColorScheme()
        
        # Test success message
        success = scheme.format_success_message("Test passed")
        self.assertIn("✅", success)
        self.assertIn("Test passed", success)
        
        # Test warning message
        warning = scheme.format_warning_message("Be careful")
        self.assertIn("⚠️", warning)
        
        # Test error message
        error = scheme.format_error_message("Test failed")
        self.assertIn("❌", error)
        
        # Test info message
        info = scheme.format_info_message("Information")
        self.assertIn("ℹ️", info)
        
    def test_format_quiz_prompt(self) -> None:
        """Test quiz prompt formatting."""
        scheme = EduLiteColorScheme()
        options = ["Option A", "Option B", "Option C"]
        
        prompt = scheme.format_quiz_prompt("What is the answer?", options)
        
        self.assertIn("🤔 Quick Check:", prompt)
        self.assertIn("What is the answer?", prompt)
        self.assertIn("[1] Option A", prompt)
        self.assertIn("[2] Option B", prompt)
        self.assertIn("[3] Option C", prompt)


if __name__ == '__main__':
    unittest.main()