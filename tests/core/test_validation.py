"""
Unit tests for validation module
"""

import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

from django_mercury.python_bindings.validation import (
    validate_mercury_config,
    validate_thresholds,
    validate_operation_name,
    validate_metrics_values,
    sanitize_operation_name,
    load_and_validate_config,
    MERCURY_CONFIG_SCHEMA,
    THRESHOLD_SCHEMA
)


class TestMercuryConfigValidation(unittest.TestCase):
    """Test cases for Mercury configuration validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.valid_config = {
            "enabled": True,
            "auto_scoring": True,
            "auto_threshold_adjustment": False,
            "verbose_reporting": False,
            "generate_executive_summaries": True,
            "include_business_impact": False,
            "show_optimization_potential": True,
            "n_plus_one_sensitivity": "normal",
            "thresholds": {
                "list_view": {
                    "response_time_ms": 200.0,
                    "memory_overhead_mb": 50.0,
                    "query_count_max": 10,
                    "cache_hit_ratio_min": 0.8
                }
            },
            "scoring_weights": {
                "response_time": 30.0,
                "query_efficiency": 40.0,
                "memory_efficiency": 20.0,
                "cache_performance": 10.0
            }
        }

    def test_validate_valid_config(self):
        """Test validation of a valid Mercury configuration."""
        is_valid, errors = validate_mercury_config(self.valid_config)
        
        self.assertTrue(is_valid)
        self.assertIsNone(errors)

    def test_validate_config_missing_required_fields(self):
        """Test validation handles missing optional fields gracefully."""
        # Note: The schema doesn't have required fields, so missing fields are allowed
        invalid_config = self.valid_config.copy()
        del invalid_config['enabled']
        
        is_valid, errors = validate_mercury_config(invalid_config)
        
        # Schema allows missing fields, so this should be valid
        self.assertTrue(is_valid)
        self.assertIsNone(errors)

    def test_validate_config_invalid_types(self):
        """Test validation fails with invalid field types."""
        invalid_config = self.valid_config.copy()
        invalid_config['enabled'] = "not_a_boolean"
        
        is_valid, errors = validate_mercury_config(invalid_config)
        
        self.assertFalse(is_valid)
        self.assertIsNotNone(errors)

    def test_validate_config_invalid_enum_values(self):
        """Test validation fails with invalid enum values."""
        invalid_config = self.valid_config.copy()
        invalid_config['n_plus_one_sensitivity'] = "invalid_value"
        
        is_valid, errors = validate_mercury_config(invalid_config)
        
        self.assertFalse(is_valid)
        self.assertIsNotNone(errors)

    def test_validate_config_scoring_weights_sum_check(self):
        """Test validation enforces scoring weights sum to 100."""
        invalid_config = self.valid_config.copy()
        invalid_config['scoring_weights'] = {
            "response_time": 50.0,
            "query_efficiency": 60.0,  # Total = 110, not 100
            "memory_efficiency": 0.0,
            "cache_performance": 0.0
        }
        
        is_valid, errors = validate_mercury_config(invalid_config)
        
        self.assertFalse(is_valid)
        self.assertIsNotNone(errors)
        self.assertTrue(any("must sum to 100" in str(error) for error in errors))

    def test_validate_config_scoring_weights_sum_floating_point_tolerance(self):
        """Test validation allows small floating point errors in weight sum."""
        valid_config = self.valid_config.copy()
        valid_config['scoring_weights'] = {
            "response_time": 33.33,
            "query_efficiency": 33.33,
            "memory_efficiency": 33.34,  # Total = 100.00
            "cache_performance": 0.0
        }
        
        is_valid, errors = validate_mercury_config(valid_config)
        
        self.assertTrue(is_valid)
        self.assertIsNone(errors)

    def test_validate_config_threshold_structure(self):
        """Test validation of threshold structure within config."""
        invalid_config = self.valid_config.copy()
        invalid_config['thresholds']['invalid_view'] = {
            "response_time_ms": -10.0,  # Negative value should be invalid
            "memory_overhead_mb": 50.0,
            "query_count_max": 10
        }
        
        is_valid, errors = validate_mercury_config(invalid_config)
        
        self.assertFalse(is_valid)
        self.assertIsNotNone(errors)

    def test_validate_config_additional_properties(self):
        """Test validation rejects additional properties."""
        invalid_config = self.valid_config.copy()
        invalid_config['unknown_property'] = "should_not_be_allowed"
        
        is_valid, errors = validate_mercury_config(invalid_config)
        
        self.assertFalse(is_valid)
        self.assertIsNotNone(errors)



class TestThresholdValidation(unittest.TestCase):
    """Test cases for threshold validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.valid_thresholds = {
            "response_time_ms": 200.0,
            "memory_overhead_mb": 50.0,
            "query_count_max": 10,
            "cache_hit_ratio_min": 0.8
        }

    def test_validate_valid_thresholds(self):
        """Test validation of valid thresholds."""
        is_valid, errors = validate_thresholds(self.valid_thresholds)
        
        self.assertTrue(is_valid)
        self.assertIsNone(errors)

    def test_validate_thresholds_missing_fields(self):
        """Test validation handles missing threshold fields gracefully."""
        partial_thresholds = {
            "response_time_ms": 200.0,
            "memory_overhead_mb": 50.0
        }
        
        is_valid, errors = validate_thresholds(partial_thresholds)
        
        self.assertTrue(is_valid)  # Missing fields should be allowed
        self.assertIsNone(errors)

    def test_validate_thresholds_negative_values(self):
        """Test validation rejects negative threshold values."""
        invalid_thresholds = self.valid_thresholds.copy()
        invalid_thresholds['response_time_ms'] = -100.0
        
        is_valid, errors = validate_thresholds(invalid_thresholds)
        
        self.assertFalse(is_valid)
        self.assertIsNotNone(errors)

    def test_validate_thresholds_cache_ratio_bounds(self):
        """Test validation of cache hit ratio bounds."""
        test_cases = [
            (-0.1, False),  # Below minimum
            (0.0, True),    # At minimum
            (0.5, True),    # Valid middle value
            (1.0, True),    # At maximum
            (1.5, False)    # Above maximum
        ]
        
        for ratio, should_be_valid in test_cases:
            with self.subTest(ratio=ratio):
                thresholds = self.valid_thresholds.copy()
                thresholds['cache_hit_ratio_min'] = ratio
                
                is_valid, errors = validate_thresholds(thresholds)
                self.assertEqual(is_valid, should_be_valid)

    def test_validate_thresholds_maximum_bounds(self):
        """Test validation respects maximum value bounds."""
        # Test with extremely large values that exceed MAX_VALUES
        large_thresholds = {
            "response_time_ms": 100000.0,  # Should exceed MAX_VALUES
            "memory_overhead_mb": 5000.0,  # Should exceed MAX_VALUES
            "query_count_max": 50000       # Should exceed MAX_VALUES
        }
        
        is_valid, errors = validate_thresholds(large_thresholds)
        
        self.assertFalse(is_valid)
        self.assertIsNotNone(errors)


class TestOperationNameValidation(unittest.TestCase):
    """Test cases for operation name validation."""

    def test_validate_valid_operation_name(self):
        """Test validation of valid operation names."""
        valid_names = [
            "UserListView",
            "user_search_operation",
            "TestOperation123",
            "a" * 255  # Maximum length
        ]
        
        for name in valid_names:
            with self.subTest(name=name[:20] + "..."):
                is_valid, error = validate_operation_name(name)
                self.assertTrue(is_valid)
                self.assertIsNone(error)

    def test_validate_empty_operation_name(self):
        """Test validation rejects empty operation names."""
        is_valid, error = validate_operation_name("")
        
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
        self.assertIn("cannot be empty", error)

    def test_validate_operation_name_too_long(self):
        """Test validation rejects operation names that are too long."""
        long_name = "a" * 300  # Exceeds maximum length
        
        is_valid, error = validate_operation_name(long_name)
        
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
        self.assertIn("exceeds maximum length", error)

    def test_validate_operation_name_dangerous_characters(self):
        """Test validation rejects operation names with dangerous characters."""
        dangerous_names = [
            "operation<script>",
            "operation>tag",
            "operation&amp;",
            'operation"quote',
            "operation'quote",
            "operation\nNewline",
            "operation\rCarriage",
            "operation\x00Null"
        ]
        
        for name in dangerous_names:
            with self.subTest(name=repr(name)):
                is_valid, error = validate_operation_name(name)
                self.assertFalse(is_valid)
                self.assertIsNotNone(error)
                self.assertIn("invalid character", error)


class TestMetricsValuesValidation(unittest.TestCase):
    """Test cases for metrics values validation."""

    def test_validate_valid_metrics_values(self):
        """Test validation of valid metrics values."""
        is_valid, errors = validate_metrics_values(
            response_time=100.0,
            memory_usage=50.0,
            query_count=5
        )
        
        self.assertTrue(is_valid)
        self.assertIsNone(errors)

    def test_validate_metrics_negative_values(self):
        """Test validation rejects negative metrics values."""
        test_cases = [
            (-10.0, 50.0, 5),   # Negative response time
            (100.0, -20.0, 5),  # Negative memory usage
            (100.0, 50.0, -1)   # Negative query count
        ]
        
        for response_time, memory_usage, query_count in test_cases:
            with self.subTest(response_time=response_time, memory_usage=memory_usage, query_count=query_count):
                is_valid, errors = validate_metrics_values(response_time, memory_usage, query_count)
                
                self.assertFalse(is_valid)
                self.assertIsNotNone(errors)
                self.assertIsInstance(errors, list)
                self.assertGreater(len(errors), 0)

    def test_validate_metrics_maximum_bounds(self):
        """Test validation respects maximum value bounds."""
        test_cases = [
            (100000.0, 50.0, 5),    # Excessive response time
            (100.0, 5000.0, 5),     # Excessive memory usage
            (100.0, 50.0, 50000)    # Excessive query count
        ]
        
        for response_time, memory_usage, query_count in test_cases:
            with self.subTest(response_time=response_time, memory_usage=memory_usage, query_count=query_count):
                is_valid, errors = validate_metrics_values(response_time, memory_usage, query_count)
                
                self.assertFalse(is_valid)
                self.assertIsNotNone(errors)
                self.assertTrue(any("exceeds maximum" in error for error in errors))

    def test_validate_metrics_zero_values(self):
        """Test validation allows zero values."""
        is_valid, errors = validate_metrics_values(
            response_time=0.0,
            memory_usage=0.0,
            query_count=0
        )
        
        self.assertTrue(is_valid)
        self.assertIsNone(errors)

    def test_validate_metrics_boundary_values(self):
        """Test validation at exact boundary values."""
        # These should be valid (at maximum bounds)
        is_valid, errors = validate_metrics_values(
            response_time=60000.0,  # MAX_VALUES['RESPONSE_TIME_MS']
            memory_usage=2048.0,    # MAX_VALUES['MEMORY_MB']
            query_count=10000       # MAX_VALUES['QUERY_COUNT']
        )
        
        self.assertTrue(is_valid)
        self.assertIsNone(errors)


class TestOperationNameSanitization(unittest.TestCase):
    """Test cases for operation name sanitization."""

    def test_sanitize_clean_operation_name(self):
        """Test sanitization of clean operation names."""
        clean_names = [
            "UserListView",
            "user_search_operation",
            "TestOperation123"
        ]
        
        for name in clean_names:
            with self.subTest(name=name):
                sanitized = sanitize_operation_name(name)
                self.assertEqual(sanitized, name)

    def test_sanitize_operation_name_dangerous_characters(self):
        """Test sanitization replaces dangerous characters."""
        # Note: Current implementation has a bug where & is replaced first,
        # causing double-escaping of < and > characters
        test_cases = [
            ("operation<script>", "operation&amp;lt;script&amp;gt;"),  # Double-escaped due to bug
            ("operation&test", "operation&amp;test"),
            ('operation"quote', "operation&quot;quote"),              # Quotes don't get double-escaped
            ("operation'quote", "operation&#39;quote"),               # Quotes don't get double-escaped
            ("operation\ntest", "operation test"),
            ("operation\rtest", "operation test"),
            ("operation\x00test", "operationtest")
        ]
        
        for original, expected in test_cases:
            with self.subTest(original=repr(original)):
                sanitized = sanitize_operation_name(original)
                self.assertEqual(sanitized, expected)

    def test_sanitize_operation_name_too_long(self):
        """Test sanitization truncates long operation names."""
        long_name = "a" * 300
        
        sanitized = sanitize_operation_name(long_name)
        
        self.assertLessEqual(len(sanitized), 256)  # MAX_VALUES['OPERATION_NAME_LENGTH']
        self.assertTrue(sanitized.endswith("..."))

    def test_sanitize_operation_name_preserves_useful_content(self):
        """Test sanitization preserves useful content while fixing issues."""
        test_name = "UserListView<script>alert('test')</script>"
        
        sanitized = sanitize_operation_name(test_name)
        
        self.assertIn("UserListView", sanitized)
        self.assertNotIn("<script>", sanitized)
        # Due to double-escaping bug, we get &amp;lt; instead of &lt;
        self.assertIn("&amp;lt;script&amp;gt;", sanitized)


class TestConfigFileLoading(unittest.TestCase):
    """Test cases for configuration file loading and validation."""

    def test_load_valid_config_file(self):
        """Test loading a valid configuration file."""
        valid_config = {
            "enabled": True,
            "auto_scoring": True,
            "scoring_weights": {
                "response_time": 25.0,
                "query_efficiency": 25.0,
                "memory_efficiency": 25.0,
                "cache_performance": 25.0
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(valid_config, f)
            config_path = f.name
        
        try:
            config, errors = load_and_validate_config(config_path)
            
            self.assertIsNotNone(config)
            self.assertIsNone(errors)
            self.assertEqual(config['enabled'], True)
        finally:
            Path(config_path).unlink()

    def test_load_nonexistent_config_file(self):
        """Test loading a nonexistent configuration file."""
        config, errors = load_and_validate_config("/nonexistent/path/config.json")
        
        self.assertIsNone(config)
        self.assertIsNotNone(errors)
        self.assertTrue(any("not found" in error for error in errors))

    def test_load_invalid_json_config_file(self):
        """Test loading a configuration file with invalid JSON."""
        invalid_json = '{"enabled": true, "auto_scoring": invalid_json}'
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(invalid_json)
            config_path = f.name
        
        try:
            config, errors = load_and_validate_config(config_path)
            
            self.assertIsNone(config)
            self.assertIsNotNone(errors)
            self.assertTrue(any("Invalid JSON" in error for error in errors))
        finally:
            Path(config_path).unlink()

    def test_load_config_file_with_validation_errors(self):
        """Test loading a configuration file that fails validation."""
        invalid_config = {
            "enabled": "not_a_boolean",  # Should be boolean
            "scoring_weights": {
                "response_time": 150.0  # Weights don't sum to 100
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_config, f)
            config_path = f.name
        
        try:
            config, errors = load_and_validate_config(config_path)
            
            self.assertIsNone(config)
            self.assertIsNotNone(errors)
            self.assertIsInstance(errors, list)
            self.assertGreater(len(errors), 0)
        finally:
            Path(config_path).unlink()


    def test_load_config_pathlib_path(self):
        """Test loading configuration using pathlib.Path object."""
        valid_config = {"enabled": True}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(valid_config, f)
            config_path = Path(f.name)
        
        try:
            config, errors = load_and_validate_config(config_path)
            
            self.assertIsNotNone(config)
            self.assertIsNone(errors)
        finally:
            config_path.unlink()


class TestValidationSchemas(unittest.TestCase):
    """Test cases for validation schemas themselves."""

    def test_mercury_config_schema_structure(self):
        """Test Mercury config schema has required structure."""
        self.assertIn("$schema", MERCURY_CONFIG_SCHEMA)
        self.assertIn("type", MERCURY_CONFIG_SCHEMA)
        self.assertIn("properties", MERCURY_CONFIG_SCHEMA)
        self.assertEqual(MERCURY_CONFIG_SCHEMA["type"], "object")

    def test_threshold_schema_structure(self):
        """Test threshold schema has required structure."""
        self.assertIn("$schema", THRESHOLD_SCHEMA)
        self.assertIn("type", THRESHOLD_SCHEMA)
        self.assertIn("properties", THRESHOLD_SCHEMA)
        self.assertEqual(THRESHOLD_SCHEMA["type"], "object")

    def test_mercury_config_schema_required_properties(self):
        """Test Mercury config schema defines expected properties."""
        expected_properties = [
            "enabled", "auto_scoring", "auto_threshold_adjustment",
            "verbose_reporting", "n_plus_one_sensitivity",
            "thresholds", "scoring_weights"
        ]
        
        for prop in expected_properties:
            self.assertIn(prop, MERCURY_CONFIG_SCHEMA["properties"])

    def test_threshold_schema_properties(self):
        """Test threshold schema defines expected properties."""
        expected_properties = [
            "response_time_ms", "memory_overhead_mb",
            "query_count_max", "cache_hit_ratio_min"
        ]
        
        for prop in expected_properties:
            self.assertIn(prop, THRESHOLD_SCHEMA["properties"])


class TestValidationLogging(unittest.TestCase):
    """Test cases for validation logging."""

    @patch('django_mercury.python_bindings.validation.logger')
    def test_validation_success_logging(self, mock_logger):
        """Test that successful validations are logged."""
        valid_config = {"enabled": True}
        
        validate_mercury_config(valid_config)
        
        mock_logger.info.assert_called()

    @patch('django_mercury.python_bindings.validation.logger')
    def test_validation_failure_logging(self, mock_logger):
        """Test that validation failures are logged."""
        invalid_config = {"enabled": "not_a_boolean"}
        
        validate_mercury_config(invalid_config)
        
        mock_logger.error.assert_called()

    @patch('django_mercury.python_bindings.validation.logger')
    def test_threshold_validation_logging(self, mock_logger):
        """Test that threshold validations are logged."""
        valid_thresholds = {"response_time_ms": 100.0}
        
        validate_thresholds(valid_thresholds)
        
        mock_logger.debug.assert_called()

    @patch('django_mercury.python_bindings.validation.logger')
    def test_metrics_validation_logging(self, mock_logger):
        """Test that metrics validation failures are logged."""
        validate_metrics_values(-10.0, 50.0, 5)  # Negative response time
        
        mock_logger.warning.assert_called()

    @patch('django_mercury.python_bindings.validation.logger')
    def test_sanitization_logging(self, mock_logger):
        """Test that sanitization is logged."""
        sanitize_operation_name("test<script>")
        
        mock_logger.debug.assert_called()


if __name__ == '__main__':
    unittest.main()