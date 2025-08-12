"""
Unit tests for colors module
"""

import unittest
import os
import sys
from unittest.mock import patch, MagicMock

from django_mercury.python_bindings.colors import (
    EduLiteColorScheme,
    ColorMode,
    PerformanceColors,
    colors,
    get_status_icon
)


class TestEduLiteColorScheme(unittest.TestCase):
    """Test cases for the EduLiteColorScheme class."""

    def test_color_scheme_has_required_colors(self) -> None:
        """Test that color scheme defines all required colors."""
        required_colors = [
            'EXCELLENT', 'GOOD', 'ACCEPTABLE', 'WARNING', 'SLOW', 'CRITICAL',
            'SUCCESS', 'INFO', 'OPTIMIZATION', 'HINT', 'BACKGROUND', 'TEXT',
            'FADE', 'BORDER', 'ACCENT', 'SECONDARY'
        ]
        
        for color in required_colors:
            self.assertTrue(hasattr(EduLiteColorScheme, color))
            color_value = getattr(EduLiteColorScheme, color)
            self.assertIsInstance(color_value, str)
            self.assertTrue(color_value.startswith('#'))
            self.assertEqual(len(color_value), 7)  # #RRGGBB format

    def test_memory_specific_colors(self) -> None:
        """Test memory-specific color definitions."""
        memory_colors = ['MEMORY_EXCELLENT', 'MEMORY_GOOD', 'MEMORY_WARNING', 'MEMORY_CRITICAL']
        
        for color in memory_colors:
            self.assertTrue(hasattr(EduLiteColorScheme, color))
            color_value = getattr(EduLiteColorScheme, color)
            self.assertIsInstance(color_value, str)
            self.assertTrue(color_value.startswith('#'))

    def test_query_specific_colors(self) -> None:
        """Test query-specific color definitions."""
        query_colors = ['QUERY_EFFICIENT', 'QUERY_ACCEPTABLE', 'QUERY_INEFFICIENT', 'QUERY_PROBLEMATIC']
        
        for color in query_colors:
            self.assertTrue(hasattr(EduLiteColorScheme, color))
            color_value = getattr(EduLiteColorScheme, color)
            self.assertIsInstance(color_value, str)
            self.assertTrue(color_value.startswith('#'))

    def test_trend_colors(self) -> None:
        """Test trend indicator colors."""
        trend_colors = ['TRENDING_UP', 'TRENDING_DOWN', 'TRENDING_STABLE']
        
        for color in trend_colors:
            self.assertTrue(hasattr(EduLiteColorScheme, color))
            color_value = getattr(EduLiteColorScheme, color)
            self.assertIsInstance(color_value, str)
            self.assertTrue(color_value.startswith('#'))


class TestColorMode(unittest.TestCase):
    """Test cases for the ColorMode enum."""

    def test_color_mode_values(self) -> None:
        """Test that ColorMode enum has all required values."""
        expected_modes = ['auto', 'always', 'never', 'rich']
        
        for mode_name in ['AUTO', 'ALWAYS', 'NEVER', 'RICH']:
            mode = getattr(ColorMode, mode_name)
            self.assertIn(mode.value, expected_modes)

    def test_color_mode_enum_consistency(self) -> None:
        """Test ColorMode enum consistency."""
        self.assertEqual(ColorMode.AUTO.value, 'auto')
        self.assertEqual(ColorMode.ALWAYS.value, 'always')
        self.assertEqual(ColorMode.NEVER.value, 'never')
        self.assertEqual(ColorMode.RICH.value, 'rich')


class TestPerformanceColors(unittest.TestCase):
    """Test cases for the PerformanceColors class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.colors_never = PerformanceColors(ColorMode.NEVER)
        self.colors_always = PerformanceColors(ColorMode.ALWAYS)
        self.colors_auto = PerformanceColors(ColorMode.AUTO)

    def test_initialization(self) -> None:
        """Test PerformanceColors initialization."""
        colors_obj = PerformanceColors()
        self.assertIsInstance(colors_obj.mode, ColorMode)
        self.assertIsInstance(colors_obj._supports_color, bool)

    def test_color_detection_never_mode(self) -> None:
        """Test color detection with NEVER mode."""
        self.assertEqual(self.colors_never.mode, ColorMode.NEVER)
        self.assertFalse(self.colors_never._supports_color)

    def test_color_detection_always_mode(self) -> None:
        """Test color detection with ALWAYS mode."""
        self.assertEqual(self.colors_always.mode, ColorMode.ALWAYS)
        self.assertTrue(self.colors_always._supports_color)

    @patch.dict(os.environ, {'NO_COLOR': '1'})
    def test_color_detection_no_color_env_var(self) -> None:
        """Test color detection respects NO_COLOR environment variable."""
        colors_obj = PerformanceColors(ColorMode.AUTO)
        self.assertFalse(colors_obj._supports_color)

    @patch.dict(os.environ, {'FORCE_COLOR': '1'})
    def test_color_detection_force_color_env_var(self) -> None:
        """Test color detection respects FORCE_COLOR environment variable."""
        colors_obj = PerformanceColors(ColorMode.AUTO)
        self.assertTrue(colors_obj._supports_color)

    @patch.dict(os.environ, {'CLICOLOR': '0'})
    def test_color_detection_clicolor_disabled(self) -> None:
        """Test color detection respects CLICOLOR=0."""
        colors_obj = PerformanceColors(ColorMode.AUTO)
        self.assertFalse(colors_obj._supports_color)

    def test_hex_to_rgb_conversion(self) -> None:
        """Test hex to RGB conversion."""
        test_cases = [
            ('#FF0000', (255, 0, 0)),    # Red
            ('#00FF00', (0, 255, 0)),    # Green
            ('#0000FF', (0, 0, 255)),    # Blue
            ('#FFFFFF', (255, 255, 255)), # White
            ('#000000', (0, 0, 0)),      # Black
            ('#73bed3', (115, 190, 211))  # EduLite color
        ]
        
        for hex_color, expected_rgb in test_cases:
            with self.subTest(hex_color=hex_color):
                rgb = self.colors_always._hex_to_rgb(hex_color)
                self.assertEqual(rgb, expected_rgb)

    def test_colorize_no_color_support(self) -> None:
        """Test colorize with no color support returns plain text."""
        text = "test text"
        result = self.colors_never.colorize(text, "#FF0000")
        self.assertEqual(result, text)

    def test_colorize_with_color_support(self) -> None:
        """Test colorize with color support returns colored text."""
        text = "test text"
        result = self.colors_always.colorize(text, "#FF0000")
        self.assertNotEqual(result, text)
        self.assertIn(text, result)  # Original text should be in result

    def test_colorize_with_bold(self) -> None:
        """Test colorize with bold styling."""
        text = "test text"
        result = self.colors_always.colorize(text, "#FF0000", bold=True)
        self.assertNotEqual(result, text)
        self.assertIn(text, result)

    @patch('rich.console.Console')
    def test_colorize_rich_mode(self, mock_console_class) -> None:
        """Test colorize with rich mode."""
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console
        mock_console.capture.return_value.__enter__.return_value.get.return_value = "colored text"
        
        colors_rich = PerformanceColors(ColorMode.RICH)
        result = colors_rich.colorize("test", "#FF0000")
        
        # Should attempt to use rich
        mock_console_class.assert_called()

    def test_colorize_rich_fallback(self) -> None:
        """Test colorize rich mode falls back to ANSI when rich not available."""
        with patch.dict('sys.modules', {'rich.console': None, 'rich.text': None}):
            colors_rich = PerformanceColors(ColorMode.RICH)
            result = colors_rich.colorize("test", "#FF0000")
            # Should fallback to ANSI (result should contain ANSI codes)
            self.assertNotEqual(result, "test")

    def test_status_color_mapping(self) -> None:
        """Test status color mapping."""
        test_cases = [
            ('excellent', EduLiteColorScheme.EXCELLENT),
            ('good', EduLiteColorScheme.GOOD),
            ('critical', EduLiteColorScheme.CRITICAL),
            ('unknown_status', EduLiteColorScheme.TEXT)  # Default fallback
        ]
        
        for status, expected_color in test_cases:
            with self.subTest(status=status):
                color = self.colors_always.status_color(status)
                self.assertEqual(color, expected_color)

    def test_trend_color_mapping(self) -> None:
        """Test trend color mapping."""
        test_cases = [
            ('up', EduLiteColorScheme.TRENDING_UP),
            ('down', EduLiteColorScheme.TRENDING_DOWN),
            ('stable', EduLiteColorScheme.TRENDING_STABLE),
            ('improving', EduLiteColorScheme.TRENDING_DOWN),  # Improving = down trend (good)
            ('degrading', EduLiteColorScheme.TRENDING_UP),    # Degrading = up trend (bad)
            ('unknown', EduLiteColorScheme.TEXT)              # Default fallback
        ]
        
        for trend, expected_color in test_cases:
            with self.subTest(trend=trend):
                color = self.colors_always.trend_color(trend)
                self.assertEqual(color, expected_color)

    def test_memory_color_thresholds(self) -> None:
        """Test memory color based on usage thresholds."""
        test_cases = [
            (10.0, EduLiteColorScheme.MEMORY_EXCELLENT),  # <= 20MB
            (30.0, EduLiteColorScheme.MEMORY_GOOD),       # <= 50MB
            (75.0, EduLiteColorScheme.MEMORY_WARNING),    # <= 100MB
            (150.0, EduLiteColorScheme.MEMORY_CRITICAL)   # > 100MB
        ]
        
        for memory_mb, expected_color in test_cases:
            with self.subTest(memory_mb=memory_mb):
                color = self.colors_always.memory_color(memory_mb)
                self.assertEqual(color, expected_color)

    def test_query_color_thresholds(self) -> None:
        """Test query color based on count thresholds."""
        test_cases = [
            (2, EduLiteColorScheme.QUERY_EFFICIENT),      # <= 3
            (5, EduLiteColorScheme.QUERY_ACCEPTABLE),     # <= 7
            (10, EduLiteColorScheme.QUERY_INEFFICIENT),   # <= 15
            (20, EduLiteColorScheme.QUERY_PROBLEMATIC)    # > 15
        ]
        
        for query_count, expected_color in test_cases:
            with self.subTest(query_count=query_count):
                color = self.colors_always.query_color(query_count)
                self.assertEqual(color, expected_color)

    def test_format_performance_status(self) -> None:
        """Test performance status formatting."""
        result = self.colors_always.format_performance_status("excellent")
        self.assertIn("EXCELLENT", result)  # Should be uppercase
        
        # With NEVER mode, should return plain text
        result_plain = self.colors_never.format_performance_status("excellent")
        self.assertEqual(result_plain, "EXCELLENT")

    def test_format_metric_value_time_units(self) -> None:
        """Test metric value formatting for time units."""
        test_cases = [
            (25.0, 'ms', EduLiteColorScheme.EXCELLENT),    # <= 50ms
            (75.0, 'ms', EduLiteColorScheme.GOOD),         # <= 100ms
            (200.0, 'ms', EduLiteColorScheme.ACCEPTABLE),  # <= 300ms
            (400.0, 'ms', EduLiteColorScheme.SLOW),        # <= 500ms
            (600.0, 'ms', EduLiteColorScheme.CRITICAL)     # > 500ms
        ]
        
        for value, unit, expected_color in test_cases:
            with self.subTest(value=value, unit=unit):
                result = self.colors_always.format_metric_value(value, unit)
                # Check that the result contains the value and unit
                self.assertIn(str(value), result)
                self.assertIn(unit, result)

    def test_format_metric_value_memory_units(self) -> None:
        """Test metric value formatting for memory units."""
        result = self.colors_always.format_metric_value(30.0, 'MB')
        self.assertIn('30.00', result)
        self.assertIn('MB', result)

    def test_format_metric_value_query_units(self) -> None:
        """Test metric value formatting for query units."""
        result = self.colors_always.format_metric_value(5, 'queries')
        self.assertIn('5', result)
        self.assertIn('queries', result)

    def test_format_metric_value_with_threshold(self) -> None:
        """Test metric value formatting with custom threshold."""
        # Value below threshold should be excellent
        result = self.colors_always.format_metric_value(50.0, 'custom', threshold=100.0)
        self.assertIn('50.00', result)
        
        # Value above threshold should be critical
        result = self.colors_always.format_metric_value(150.0, 'custom', threshold=100.0)
        self.assertIn('150.00', result)


class TestGlobalFunctions(unittest.TestCase):
    """Test cases for global functions and instances."""

    def test_global_colors_instance(self) -> None:
        """Test that global colors instance exists and works."""
        self.assertIsInstance(colors, PerformanceColors)
        
        # Test that it can colorize text
        result = colors.colorize("test", "#FF0000")
        self.assertIsInstance(result, str)

    def test_get_status_icon(self) -> None:
        """Test status icon retrieval."""
        test_cases = [
            ('excellent', '🚀'),
            ('good', '✅'),
            ('acceptable', '⚠️'),
            ('warning', '⚠️'),
            ('slow', '🐌'),
            ('critical', '🚨'),
            ('success', '🎯'),
            ('info', '💡'),
            ('optimization', '🔧'),
            ('trending_up', '📈'),
            ('trending_down', '📉'),
            ('trending_stable', '➡️'),
            ('unknown_status', '📊')  # Default fallback
        ]
        
        for status, expected_icon in test_cases:
            with self.subTest(status=status):
                icon = get_status_icon(status)
                self.assertEqual(icon, expected_icon)

    def test_get_status_icon_case_insensitive(self) -> None:
        """Test status icon retrieval is case insensitive."""
        self.assertEqual(get_status_icon('EXCELLENT'), '🚀')
        self.assertEqual(get_status_icon('Excellent'), '🚀')
        self.assertEqual(get_status_icon('excellent'), '🚀')


class TestColorDetection(unittest.TestCase):
    """Test cases for color detection logic."""

    def test_tty_detection(self) -> None:
        """Test TTY detection for auto mode."""
        with patch('sys.stdout') as mock_stdout:
            mock_stdout.isatty.return_value = True
            colors_obj = PerformanceColors(ColorMode.AUTO)
            # Result depends on environment variables, but should not crash
            self.assertIsInstance(colors_obj._supports_color, bool)

    def test_no_tty_detection(self) -> None:
        """Test behavior when not in TTY."""
        with patch('sys.stdout') as mock_stdout:
            mock_stdout.isatty.return_value = False
            with patch.dict(os.environ, {}, clear=True):  # Clear env vars
                colors_obj = PerformanceColors(ColorMode.AUTO)
                # Without TTY and no forcing env vars, should be False
                self.assertFalse(colors_obj._supports_color)

    def test_color_detection_logging(self) -> None:
        """Test that color detection logs appropriately."""
        # This test just ensures logging doesn't crash
        colors_obj = PerformanceColors(ColorMode.NEVER)
        self.assertEqual(colors_obj.mode, ColorMode.NEVER)


if __name__ == '__main__':
    unittest.main()