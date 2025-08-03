"""
Unit tests for logging_config module
"""

import unittest
import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from django_mercury.python_bindings.logging_config import (
    get_log_level,
    get_log_config,
    get_logger,
    DEFAULT_LOG_FORMAT,
    DETAILED_LOG_FORMAT
)


class TestLoggingConfigConstants(unittest.TestCase):
    """Test cases for logging configuration constants."""

    def test_default_log_format_defined(self):
        """Test that default log format is properly defined."""
        self.assertIsInstance(DEFAULT_LOG_FORMAT, str)
        self.assertIn('%(asctime)s', DEFAULT_LOG_FORMAT)
        self.assertIn('%(name)s', DEFAULT_LOG_FORMAT)
        self.assertIn('%(levelname)s', DEFAULT_LOG_FORMAT)
        self.assertIn('%(message)s', DEFAULT_LOG_FORMAT)

    def test_detailed_log_format_defined(self):
        """Test that detailed log format is properly defined."""
        self.assertIsInstance(DETAILED_LOG_FORMAT, str)
        self.assertIn('%(asctime)s', DETAILED_LOG_FORMAT)
        self.assertIn('%(name)s', DETAILED_LOG_FORMAT)
        self.assertIn('%(levelname)s', DETAILED_LOG_FORMAT)
        self.assertIn('%(message)s', DETAILED_LOG_FORMAT)
        self.assertIn('%(filename)s', DETAILED_LOG_FORMAT)
        self.assertIn('%(lineno)d', DETAILED_LOG_FORMAT)
        self.assertIn('%(funcName)s', DETAILED_LOG_FORMAT)

    def test_detailed_format_more_detailed_than_default(self):
        """Test that detailed format contains more information than default."""
        # Detailed format should be longer and contain more fields
        self.assertGreater(len(DETAILED_LOG_FORMAT), len(DEFAULT_LOG_FORMAT))
        self.assertIn('filename', DETAILED_LOG_FORMAT)
        self.assertIn('lineno', DETAILED_LOG_FORMAT)
        self.assertIn('funcName', DETAILED_LOG_FORMAT)


class TestGetLogLevel(unittest.TestCase):
    """Test cases for get_log_level function."""

    def test_get_log_level_default(self):
        """Test get_log_level returns INFO by default."""
        with patch.dict(os.environ, {}, clear=True):
            log_level = get_log_level()
            self.assertEqual(log_level, 'INFO')

    def test_get_log_level_from_environment(self):
        """Test get_log_level reads from MERCURY_LOG_LEVEL environment variable."""
        test_cases = [
            ('DEBUG', 'DEBUG'),
            ('info', 'INFO'),  # Should be uppercased
            ('Warning', 'WARNING'),  # Should be uppercased
            ('error', 'ERROR'),
            ('critical', 'CRITICAL')
        ]
        
        for env_value, expected_result in test_cases:
            with self.subTest(env_value=env_value):
                with patch.dict(os.environ, {'MERCURY_LOG_LEVEL': env_value}):
                    log_level = get_log_level()
                    self.assertEqual(log_level, expected_result)

    def test_get_log_level_case_insensitive(self):
        """Test get_log_level handles case conversion correctly."""
        with patch.dict(os.environ, {'MERCURY_LOG_LEVEL': 'debug'}):
            log_level = get_log_level()
            self.assertEqual(log_level, 'DEBUG')

    def test_get_log_level_with_whitespace(self):
        """Test get_log_level handles whitespace correctly."""
        with patch.dict(os.environ, {'MERCURY_LOG_LEVEL': '  INFO  '}):
            log_level = get_log_level()
            self.assertEqual(log_level, '  INFO  ')  # upper() doesn't strip whitespace


class TestGetLogConfig(unittest.TestCase):
    """Test cases for get_log_config function."""

    def test_get_log_config_structure(self):
        """Test get_log_config returns properly structured configuration."""
        config = get_log_config()
        
        # Check top-level structure
        self.assertIsInstance(config, dict)
        self.assertIn('version', config)
        self.assertIn('disable_existing_loggers', config)
        self.assertIn('formatters', config)
        self.assertIn('handlers', config)
        self.assertIn('loggers', config)
        self.assertIn('root', config)

    def test_get_log_config_version(self):
        """Test log config has correct version."""
        config = get_log_config()
        self.assertEqual(config['version'], 1)

    def test_get_log_config_disable_existing_loggers(self):
        """Test log config preserves existing loggers."""
        config = get_log_config()
        self.assertFalse(config['disable_existing_loggers'])

    def test_get_log_config_formatters(self):
        """Test log config defines required formatters."""
        config = get_log_config()
        formatters = config['formatters']
        
        required_formatters = ['default', 'detailed', 'colored']
        for formatter_name in required_formatters:
            self.assertIn(formatter_name, formatters)
            self.assertIsInstance(formatters[formatter_name], dict)

    def test_get_log_config_formatters_content(self):
        """Test formatter configurations are correct."""
        config = get_log_config()
        formatters = config['formatters']
        
        # Test default formatter
        default_formatter = formatters['default']
        self.assertEqual(default_formatter['format'], DEFAULT_LOG_FORMAT)
        self.assertIn('datefmt', default_formatter)
        
        # Test detailed formatter
        detailed_formatter = formatters['detailed']
        self.assertEqual(detailed_formatter['format'], DETAILED_LOG_FORMAT)
        self.assertIn('datefmt', detailed_formatter)
        
        # Test colored formatter
        colored_formatter = formatters['colored']
        self.assertIn('()', colored_formatter)
        self.assertIn('format', colored_formatter)
        self.assertIn('log_colors', colored_formatter)

    def test_get_log_config_handlers(self):
        """Test log config defines required handlers."""
        config = get_log_config()
        handlers = config['handlers']
        
        required_handlers = ['console', 'file', 'error_file']
        for handler_name in required_handlers:
            self.assertIn(handler_name, handlers)
            self.assertIsInstance(handlers[handler_name], dict)

    def test_get_log_config_handlers_content(self):
        """Test handler configurations are correct."""
        config = get_log_config()
        handlers = config['handlers']
        
        # Test console handler
        console_handler = handlers['console']
        self.assertEqual(console_handler['class'], 'logging.StreamHandler')
        self.assertIn('formatter', console_handler)
        self.assertIn('level', console_handler)
        
        # Test file handler
        file_handler = handlers['file']
        self.assertEqual(file_handler['class'], 'logging.handlers.RotatingFileHandler')
        self.assertIn('filename', file_handler)
        self.assertIn('formatter', file_handler)
        self.assertIn('maxBytes', file_handler)
        self.assertIn('backupCount', file_handler)
        
        # Test error file handler
        error_handler = handlers['error_file']
        self.assertEqual(error_handler['class'], 'logging.handlers.RotatingFileHandler')
        self.assertIn('filename', error_handler)
        self.assertEqual(error_handler['level'], 'ERROR')

    def test_get_log_config_loggers(self):
        """Test log config defines performance testing loggers."""
        config = get_log_config()
        loggers = config['loggers']
        
        # Should have performance_testing logger
        self.assertIn('performance_testing', loggers)
        pt_logger = loggers['performance_testing']
        self.assertIn('handlers', pt_logger)
        self.assertIn('level', pt_logger)
        
        # Should not propagate to avoid double logging
        self.assertFalse(pt_logger.get('propagate', True))

    def test_get_log_config_root_logger(self):
        """Test root logger configuration."""
        config = get_log_config()
        root_config = config['root']
        
        self.assertIn('handlers', root_config)
        self.assertIn('level', root_config)
        self.assertIsInstance(root_config['handlers'], list)

    @patch('pathlib.Path.mkdir')
    def test_get_log_config_creates_log_directory(self, mock_mkdir):
        """Test that get_log_config creates log directory."""
        get_log_config()
        
        # Should call mkdir with parents=True, exist_ok=True
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_get_log_config_log_file_paths(self):
        """Test that log file paths are correctly constructed."""
        config = get_log_config()
        handlers = config['handlers']
        
        # Check that file paths exist and are strings
        file_handler = handlers['file']
        error_handler = handlers['error_file']
        
        self.assertIn('filename', file_handler)
        self.assertIn('filename', error_handler)
        self.assertIsInstance(file_handler['filename'], str)
        self.assertIsInstance(error_handler['filename'], str)
        
        # Paths should end with appropriate file names
        self.assertTrue(file_handler['filename'].endswith('performance_testing.log'))
        self.assertTrue(error_handler['filename'].endswith('performance_testing_errors.log'))

    def test_get_log_config_colored_formatter_colors(self):
        """Test colored formatter defines all required log level colors."""
        config = get_log_config()
        colored_formatter = config['formatters']['colored']
        log_colors = colored_formatter['log_colors']
        
        required_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        for level in required_levels:
            self.assertIn(level, log_colors)
            self.assertIsInstance(log_colors[level], str)

    def test_get_log_config_file_handler_rotation(self):
        """Test file handlers have rotation configured."""
        config = get_log_config()
        handlers = config['handlers']
        
        file_handler = handlers['file']
        error_handler = handlers['error_file']
        
        # Both should have rotation settings
        for handler in [file_handler, error_handler]:
            self.assertIn('maxBytes', handler)
            self.assertIn('backupCount', handler)
            self.assertIsInstance(handler['maxBytes'], int)
            self.assertIsInstance(handler['backupCount'], int)
            self.assertGreater(handler['maxBytes'], 0)
            self.assertGreater(handler['backupCount'], 0)


class TestGetLogger(unittest.TestCase):
    """Test cases for get_logger function."""

    def test_get_logger_returns_logger(self):
        """Test get_logger returns a logger instance."""
        logger = get_logger('test_logger')
        
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, 'performance_testing.test_logger')

    def test_get_logger_different_names(self):
        """Test get_logger with different names returns different loggers."""
        logger1 = get_logger('logger1')
        logger2 = get_logger('logger2')
        
        self.assertNotEqual(logger1, logger2)
        self.assertEqual(logger1.name, 'performance_testing.logger1')
        self.assertEqual(logger2.name, 'performance_testing.logger2')

    def test_get_logger_same_name_returns_same_logger(self):
        """Test get_logger with same name returns same logger instance."""
        logger1 = get_logger('same_logger')
        logger2 = get_logger('same_logger')
        
        self.assertEqual(logger1, logger2)
        self.assertEqual(logger1.name, logger2.name)

    def test_get_logger_empty_name(self):
        """Test get_logger with empty name."""
        logger = get_logger('')
        
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, 'performance_testing.')

    def test_get_logger_none_name(self):
        """Test get_logger with None name."""
        logger = get_logger(None)
        
        self.assertIsInstance(logger, logging.Logger)
        # Logger name should be prefixed string representation of None
        self.assertEqual(logger.name, 'performance_testing.None')

    def test_get_logger_same_logger_functionality(self):
        """Test that get_logger sets up logging and returns functional loggers."""
        # This test verifies the logger works without testing implementation details
        logger = get_logger('functional_test')
        
        # Should be a proper logger instance
        self.assertIsInstance(logger, logging.Logger)
        
        # Should be able to log without errors
        try:
            logger.info("Test message")
            logger.debug("Debug message")
        except Exception as e:
            self.fail(f"Logger should work without errors: {e}")

    def test_get_logger_with_performance_testing_prefix(self):
        """Test get_logger with performance_testing module prefix."""
        logger = get_logger('performance_testing.test_module')
        
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, 'performance_testing.test_module')

    def test_get_logger_handles_special_characters(self):
        """Test get_logger handles special characters in logger names."""
        special_names = [
            'logger.with.dots',
            'logger-with-dashes',
            'logger_with_underscores',
            'logger123',
            'Logger.With.Mixed-CASE_123'
        ]
        
        for name in special_names:
            with self.subTest(name=name):
                logger = get_logger(name)
                self.assertIsInstance(logger, logging.Logger)
                self.assertEqual(logger.name, f'performance_testing.{name}')


class TestLoggingConfiguration(unittest.TestCase):
    """Integration tests for logging configuration."""

    def test_logger_can_log_messages(self):
        """Test that created loggers can actually log messages."""
        logger = get_logger('test_integration')
        
        # This should not raise any exceptions
        try:
            logger.debug('Debug message')
            logger.info('Info message')
            logger.warning('Warning message')
            logger.error('Error message')
            logger.critical('Critical message')
        except Exception as e:
            self.fail(f"Logging should not raise exceptions: {e}")

    def test_logger_respects_log_level(self):
        """Test that logger respects configured log level."""
        logger = get_logger('test_level')
        
        # Logger should have some level set
        self.assertIsNotNone(logger.level)
        
        # Effective level should be a valid logging level
        effective_level = logger.getEffectiveLevel()
        valid_levels = [
            logging.DEBUG, logging.INFO, logging.WARNING,
            logging.ERROR, logging.CRITICAL
        ]
        self.assertIn(effective_level, valid_levels)

    def test_multiple_loggers_work_independently(self):
        """Test that multiple loggers work independently."""
        logger1 = get_logger('independent1')
        logger2 = get_logger('independent2')
        
        # Both should be functional
        try:
            logger1.info('Message from logger1')
            logger2.warning('Message from logger2')
        except Exception as e:
            self.fail(f"Independent loggers should work: {e}")

    @patch('django_mercury.python_bindings.logging_config.get_log_level')
    def test_configuration_uses_log_level_function(self, mock_get_log_level):
        """Test that configuration uses get_log_level function."""
        mock_get_log_level.return_value = 'DEBUG'
        
        # This should trigger configuration
        get_logger('test_config_level')
        
        # get_log_level should have been called during configuration
        mock_get_log_level.assert_called()


class TestLoggingEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""

    def test_get_log_config_with_missing_colorlog(self):
        """Test get_log_config handles missing colorlog gracefully."""
        # This test assumes colorlog might not be available
        # The function should still work and return a valid config
        config = get_log_config()
        
        # Should still have all required components
        self.assertIn('formatters', config)
        self.assertIn('colored', config['formatters'])
        
        # Colored formatter should have colorlog configuration
        colored = config['formatters']['colored']
        self.assertIn('()', colored)

    def test_logging_config_directory_creation_failure(self):
        """Test behavior when log directory creation fails."""
        with patch('pathlib.Path.mkdir', side_effect=PermissionError("Cannot create directory")):
            # Should still return configuration even if directory creation fails
            try:
                config = get_log_config()
                self.assertIsInstance(config, dict)
            except PermissionError:
                # It's also acceptable for this to raise an error
                pass

    def test_get_logger_with_numeric_name(self):
        """Test get_logger with numeric name."""
        logger = get_logger(123)
        
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, 'performance_testing.123')


if __name__ == '__main__':
    unittest.main()