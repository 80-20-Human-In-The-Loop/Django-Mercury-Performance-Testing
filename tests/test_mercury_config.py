"""
Unit tests for mercury_config module
"""

import unittest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

from django_mercury.python_bindings.mercury_config import (
    PerformanceThresholds,
    MercuryConfiguration,
    MercuryConfigurationManager,
    ProjectPerformanceStandards,
    get_mercury_config,
    update_mercury_config,
    configure_for_project,
    configure_for_environment
)


class TestPerformanceThresholds(unittest.TestCase):
    """Test cases for PerformanceThresholds class."""

    def test_performance_thresholds_initialization(self):
        """Test PerformanceThresholds dataclass initialization."""
        thresholds = PerformanceThresholds(
            response_time_ms=200.0,
            memory_overhead_mb=50.0,
            query_count_max=10,
            cache_hit_ratio_min=0.8
        )
        
        self.assertEqual(thresholds.response_time_ms, 200.0)
        self.assertEqual(thresholds.memory_overhead_mb, 50.0)
        self.assertEqual(thresholds.query_count_max, 10)
        self.assertEqual(thresholds.cache_hit_ratio_min, 0.8)

    def test_performance_thresholds_defaults(self):
        """Test PerformanceThresholds can be created with keyword args."""
        thresholds = PerformanceThresholds(
            response_time_ms=100.0,
            memory_overhead_mb=25.0,
            query_count_max=5,
            cache_hit_ratio_min=0.9
        )
        
        self.assertIsInstance(thresholds.response_time_ms, float)
        self.assertIsInstance(thresholds.memory_overhead_mb, float)
        self.assertIsInstance(thresholds.query_count_max, int)
        self.assertIsInstance(thresholds.cache_hit_ratio_min, float)


class TestMercuryConfiguration(unittest.TestCase):
    """Test cases for MercuryConfiguration class."""

    def test_mercury_configuration_initialization_defaults(self):
        """Test MercuryConfiguration initialization with defaults."""
        config = MercuryConfiguration()
        
        self.assertTrue(config.enabled)
        self.assertTrue(config.auto_scoring)
        self.assertTrue(config.auto_threshold_adjustment)
        self.assertFalse(config.verbose_reporting)
        # After __post_init__, thresholds and scoring_weights should be set
        self.assertIsNotNone(config.thresholds)
        self.assertIsNotNone(config.scoring_weights)
        self.assertEqual(config.n_plus_one_sensitivity, "normal")
        self.assertTrue(config.generate_executive_summaries)
        self.assertTrue(config.include_business_impact)
        self.assertTrue(config.show_optimization_potential)

    def test_mercury_configuration_custom_values(self):
        """Test MercuryConfiguration with custom values."""
        thresholds = {
            'list_view': PerformanceThresholds(100.0, 20.0, 5, 0.85),
            'detail_view': PerformanceThresholds(50.0, 10.0, 3, 0.90)
        }
        
        scoring_weights = {
            'response_time': 40.0,
            'memory_usage': 30.0,
            'query_count': 30.0
        }
        
        config = MercuryConfiguration(
            enabled=False,
            auto_scoring=False,
            auto_threshold_adjustment=False,
            verbose_reporting=True,
            thresholds=thresholds,
            scoring_weights=scoring_weights,
            n_plus_one_sensitivity="strict"
        )
        
        self.assertFalse(config.enabled)
        self.assertFalse(config.auto_scoring)
        self.assertFalse(config.auto_threshold_adjustment)
        self.assertTrue(config.verbose_reporting)
        self.assertEqual(config.thresholds, thresholds)
        self.assertEqual(config.scoring_weights, scoring_weights)
        self.assertEqual(config.n_plus_one_sensitivity, "strict")

    def test_mercury_configuration_sensitivity_options(self):
        """Test different sensitivity options."""
        for sensitivity in ["strict", "normal", "lenient"]:
            config = MercuryConfiguration(n_plus_one_sensitivity=sensitivity)
            self.assertEqual(config.n_plus_one_sensitivity, sensitivity)


class TestMercuryConfigurationManager(unittest.TestCase):
    """Test cases for MercuryConfigurationManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = MercuryConfigurationManager()

    def test_manager_initialization(self):
        """Test MercuryConfigurationManager initialization."""
        self.assertIsInstance(self.manager, MercuryConfigurationManager)

    def test_load_configuration_from_file(self):
        """Test loading configuration from file."""
        # Create a temporary config file
        mock_config = {
            "enabled": True,
            "auto_scoring": False,
            "n_plus_one_sensitivity": "strict",
            "thresholds": {
                "list_view": {
                    "response_time_ms": 150.0,
                    "memory_overhead_mb": 30.0,
                    "query_count_max": 8,
                    "cache_hit_ratio_min": 0.85
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(mock_config, f)
            temp_path = f.name
        
        try:
            manager = MercuryConfigurationManager(temp_path)
            config = manager.load_configuration()
            
            self.assertIsInstance(config, MercuryConfiguration)
            self.assertTrue(config.enabled)
            self.assertFalse(config.auto_scoring)
            self.assertEqual(config.n_plus_one_sensitivity, "strict")
        finally:
            os.unlink(temp_path)

    @patch('django_mercury.python_bindings.mercury_config.Path.exists')
    def test_load_configuration_file_not_found(self, mock_exists):
        """Test loading configuration when file doesn't exist."""
        mock_exists.return_value = False
        
        config = self.manager.load_configuration()
        
        # Should return default configuration
        self.assertIsInstance(config, MercuryConfiguration)
        self.assertTrue(config.enabled)

    def test_load_configuration_invalid_json(self):
        """Test loading configuration with invalid JSON."""
        # Create a file with invalid JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_path = f.name
        
        try:
            manager = MercuryConfigurationManager(temp_path)
            config = manager.load_configuration()
            
            # Should return default configuration on JSON error
            self.assertIsInstance(config, MercuryConfiguration)
            self.assertTrue(config.enabled)
        finally:
            os.unlink(temp_path)

    def test_save_configuration(self):
        """Test saving configuration to file."""
        config = MercuryConfiguration(
            enabled=False,
            auto_scoring=True,
            n_plus_one_sensitivity="lenient"
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            manager = MercuryConfigurationManager(temp_path)
            manager.save_configuration(config)
            
            # Verify file was created and contains expected data
            self.assertTrue(os.path.exists(temp_path))
            
            with open(temp_path, 'r') as f:
                saved_data = json.load(f)
                self.assertFalse(saved_data["enabled"])
                self.assertTrue(saved_data["auto_scoring"])
                self.assertEqual(saved_data["n_plus_one_sensitivity"], "lenient")
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_update_thresholds_for_project_large(self):
        """Test updating thresholds for large project."""
        project_characteristics = {
            'project_size': 'large',
            'database_type': 'postgresql',
            'has_caching': True
        }
        
        # Should not raise an exception
        self.manager.update_thresholds_for_project(project_characteristics)

    def test_create_environment_specific_config_development(self):
        """Test creating development environment configuration."""
        dev_config = self.manager.create_environment_specific_config("development")
        
        self.assertIsInstance(dev_config, MercuryConfiguration)
        self.assertTrue(dev_config.verbose_reporting)

    def test_create_environment_specific_config_production(self):
        """Test creating production environment configuration."""
        prod_config = self.manager.create_environment_specific_config("production")
        
        self.assertIsInstance(prod_config, MercuryConfiguration)
        self.assertEqual(prod_config.n_plus_one_sensitivity, "strict")
        self.assertTrue(prod_config.include_business_impact)

    def test_create_environment_specific_config_staging(self):
        """Test creating staging environment configuration."""
        staging_config = self.manager.create_environment_specific_config("staging")
        
        self.assertIsInstance(staging_config, MercuryConfiguration)

    def test_update_thresholds_postgresql(self):
        """Test updating thresholds for PostgreSQL database."""
        project_characteristics = {'database_type': 'postgresql'}
        
        # Should not raise an exception
        self.manager.update_thresholds_for_project(project_characteristics)

    def test_update_thresholds_with_caching(self):
        """Test updating thresholds for project with caching."""
        project_characteristics = {'has_caching': True}
        
        # Should not raise an exception
        self.manager.update_thresholds_for_project(project_characteristics)


class TestProjectPerformanceStandards(unittest.TestCase):
    """Test cases for ProjectPerformanceStandards class."""

    def setUp(self):
        """Set up test fixtures."""
        self.standards = ProjectPerformanceStandards()

    def test_initialization(self):
        """Test ProjectPerformanceStandards initialization."""
        self.assertIsInstance(self.standards.standards, dict)
        self.assertIn('response_time_goals', self.standards.standards)
        self.assertIn('database_query_goals', self.standards.standards)
        self.assertIn('memory_efficiency_goals', self.standards.standards)
        self.assertIn('n_plus_one_tolerance', self.standards.standards)

    def test_get_performance_category_response_time(self):
        """Test categorizing response time performance."""
        # Test excellent performance
        category = self.standards.get_performance_category('response_time', 25.0)
        self.assertEqual(category, 'excellent')
        
        # Test good performance
        category = self.standards.get_performance_category('response_time', 75.0)
        self.assertEqual(category, 'good')
        
        # Test acceptable performance
        category = self.standards.get_performance_category('response_time', 250.0)
        self.assertEqual(category, 'acceptable')
        
        # Test poor performance
        category = self.standards.get_performance_category('response_time', 450.0)
        self.assertEqual(category, 'poor')

    def test_get_performance_category_database_query(self):
        """Test categorizing database query performance."""
        # Test excellent performance
        category = self.standards.get_performance_category('database_query', 1.0)
        self.assertEqual(category, 'excellent')
        
        # Test good performance
        category = self.standards.get_performance_category('database_query', 2.5)
        self.assertEqual(category, 'good')
        
        # Test acceptable performance
        category = self.standards.get_performance_category('database_query', 4.0)
        self.assertEqual(category, 'acceptable')

    def test_get_performance_category_memory_efficiency(self):
        """Test categorizing memory efficiency performance."""
        # Test excellent performance
        category = self.standards.get_performance_category('memory_efficiency', 5.0)
        self.assertEqual(category, 'excellent')
        
        # Test good performance
        category = self.standards.get_performance_category('memory_efficiency', 15.0)
        self.assertEqual(category, 'good')

    def test_get_performance_category_unknown_metric(self):
        """Test categorizing unknown metric type."""
        category = self.standards.get_performance_category('unknown_metric', 100.0)
        self.assertEqual(category, 'critical')

    def test_should_block_deployment_acceptable(self):
        """Test deployment blocking with acceptable metrics."""
        metrics = {
            'response_time': 200.0,
            'query_count': 5,
            'memory_overhead': 30.0,
            'n_plus_one_severity': 1
        }
        
        should_block, blocking_issues = self.standards.should_block_deployment(metrics)
        
        self.assertFalse(should_block)
        self.assertEqual(len(blocking_issues), 0)

    def test_should_block_deployment_slow_response(self):
        """Test deployment blocking with slow response time."""
        metrics = {
            'response_time': 1500.0,  # Over 1000ms threshold
            'query_count': 5,
            'memory_overhead': 30.0,
            'n_plus_one_severity': 1
        }
        
        should_block, blocking_issues = self.standards.should_block_deployment(metrics)
        
        self.assertTrue(should_block)
        self.assertGreater(len(blocking_issues), 0)
        self.assertIn("Response time exceeds 1 second", blocking_issues[0])

    def test_should_block_deployment_excessive_queries(self):
        """Test deployment blocking with excessive queries."""
        metrics = {
            'response_time': 200.0,
            'query_count': 25,  # Over 20 query threshold
            'memory_overhead': 30.0,
            'n_plus_one_severity': 1
        }
        
        should_block, blocking_issues = self.standards.should_block_deployment(metrics)
        
        self.assertTrue(should_block)
        self.assertGreater(len(blocking_issues), 0)
        self.assertIn("Excessive database queries", blocking_issues[0])

    def test_should_block_deployment_high_memory(self):
        """Test deployment blocking with high memory usage."""
        metrics = {
            'response_time': 200.0,
            'query_count': 5,
            'memory_overhead': 150.0,  # Over 100MB threshold
            'n_plus_one_severity': 1
        }
        
        should_block, blocking_issues = self.standards.should_block_deployment(metrics)
        
        self.assertTrue(should_block)
        self.assertGreater(len(blocking_issues), 0)
        self.assertIn("Excessive memory overhead", blocking_issues[0])

    def test_should_block_deployment_critical_n_plus_one(self):
        """Test deployment blocking with critical N+1 issues."""
        metrics = {
            'response_time': 200.0,
            'query_count': 5,
            'memory_overhead': 30.0,
            'n_plus_one_severity': 4  # Critical severity
        }
        
        should_block, blocking_issues = self.standards.should_block_deployment(metrics)
        
        self.assertTrue(should_block)
        self.assertGreater(len(blocking_issues), 0)
        self.assertIn("Critical N+1 query issues", blocking_issues[0])

    def test_should_block_deployment_multiple_issues(self):
        """Test deployment blocking with multiple issues."""
        metrics = {
            'response_time': 1500.0,  # Over threshold
            'query_count': 25,       # Over threshold
            'memory_overhead': 150.0, # Over threshold
            'n_plus_one_severity': 4  # Critical
        }
        
        should_block, blocking_issues = self.standards.should_block_deployment(metrics)
        
        self.assertTrue(should_block)
        self.assertEqual(len(blocking_issues), 4)  # All four issues


class TestModuleFunctions(unittest.TestCase):
    """Test cases for module-level functions."""

    def test_get_mercury_config(self):
        """Test get_mercury_config function."""
        config = get_mercury_config()
        self.assertIsInstance(config, MercuryConfiguration)

    def test_update_mercury_config(self):
        """Test update_mercury_config function."""
        new_config = MercuryConfiguration(enabled=False)
        
        # Should not raise an exception
        update_mercury_config(new_config)

    def test_configure_for_project(self):
        """Test configure_for_project function."""
        project_characteristics = {
            "project_size": "large",
            "database_type": "postgresql",
            "has_caching": True
        }
        
        # Should not raise an exception
        configure_for_project(project_characteristics)

    def test_configure_for_environment_development(self):
        """Test configure_for_environment function with development."""
        config = configure_for_environment("development")
        self.assertIsInstance(config, MercuryConfiguration)
        self.assertTrue(config.verbose_reporting)

    def test_configure_for_environment_production(self):
        """Test configure_for_environment function with production."""
        config = configure_for_environment("production")
        self.assertIsInstance(config, MercuryConfiguration)
        self.assertEqual(config.n_plus_one_sensitivity, "strict")

    def test_configure_for_environment_staging(self):
        """Test configure_for_environment function with staging."""
        config = configure_for_environment("staging")
        self.assertIsInstance(config, MercuryConfiguration)

    def test_configure_for_environment_unknown(self):
        """Test configure_for_environment function with unknown environment."""
        config = configure_for_environment("unknown_env")
        self.assertIsInstance(config, MercuryConfiguration)


class TestConfigurationSerialization(unittest.TestCase):
    """Test configuration serialization and deserialization."""

    def test_configuration_to_dict(self):
        """Test converting configuration to dictionary."""
        config = MercuryConfiguration(
            enabled=True,
            auto_scoring=False,
            n_plus_one_sensitivity="strict"
        )
        
        # Test that dataclass can be converted to dict
        from dataclasses import asdict
        config_dict = asdict(config)
        
        self.assertIsInstance(config_dict, dict)
        self.assertTrue(config_dict["enabled"])
        self.assertFalse(config_dict["auto_scoring"])
        self.assertEqual(config_dict["n_plus_one_sensitivity"], "strict")

    def test_configuration_json_serialization(self):
        """Test JSON serialization of configuration."""
        thresholds = {
            'test_view': PerformanceThresholds(100.0, 20.0, 5, 0.8)
        }
        
        config = MercuryConfiguration(
            enabled=True,
            thresholds=thresholds
        )
        
        # Convert to dict first (as done in the actual implementation)
        from dataclasses import asdict
        config_dict = asdict(config)
        
        # Should be JSON serializable
        json_str = json.dumps(config_dict, indent=2)
        
        self.assertIsInstance(json_str, str)
        self.assertIn('"enabled": true', json_str)

    def test_configuration_from_dict(self):
        """Test creating configuration from dictionary."""
        config_dict = {
            "enabled": False,
            "auto_scoring": True,
            "auto_threshold_adjustment": False,
            "verbose_reporting": False,
            "thresholds": None,
            "scoring_weights": None,
            "n_plus_one_sensitivity": "lenient"
        }
        
        config = MercuryConfiguration(**config_dict)
        
        self.assertFalse(config.enabled)
        self.assertTrue(config.auto_scoring)
        self.assertFalse(config.auto_threshold_adjustment)
        self.assertEqual(config.n_plus_one_sensitivity, "lenient")


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""

    def test_performance_thresholds_with_zero_values(self):
        """Test PerformanceThresholds with edge case values."""
        thresholds = PerformanceThresholds(
            response_time_ms=0.0,
            memory_overhead_mb=0.0,
            query_count_max=0,
            cache_hit_ratio_min=0.0
        )
        
        self.assertEqual(thresholds.response_time_ms, 0.0)
        self.assertEqual(thresholds.cache_hit_ratio_min, 0.0)

    def test_performance_thresholds_with_high_values(self):
        """Test PerformanceThresholds with very high values."""
        thresholds = PerformanceThresholds(
            response_time_ms=10000.0,
            memory_overhead_mb=1000.0,
            query_count_max=1000,
            cache_hit_ratio_min=1.0
        )
        
        self.assertEqual(thresholds.response_time_ms, 10000.0)
        self.assertEqual(thresholds.cache_hit_ratio_min, 1.0)

    @patch('builtins.open', new_callable=mock_open)
    @patch('django_mercury.python_bindings.mercury_config.Path.exists')
    def test_configuration_manager_corrupted_file(self, mock_exists, mock_file):
        """Test handling of corrupted configuration file."""
        mock_exists.return_value = True
        mock_file.side_effect = OSError("Permission denied")
        
        manager = MercuryConfigurationManager()
        config = manager.load_configuration()
        
        # Should gracefully handle file read errors
        self.assertIsInstance(config, MercuryConfiguration)

    def test_configuration_manager_empty_file(self):
        """Test handling of empty configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("")
            temp_path = f.name
        
        try:
            manager = MercuryConfigurationManager(temp_path)
            config = manager.load_configuration()
            
            # Should handle empty file gracefully
            self.assertIsInstance(config, MercuryConfiguration)
        finally:
            os.unlink(temp_path)


if __name__ == '__main__':
    unittest.main()