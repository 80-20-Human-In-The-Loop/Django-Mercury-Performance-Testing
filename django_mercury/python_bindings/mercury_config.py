# backend/performance_testing/python_bindings/mercury_config.py - Mercury Configuration Management
# Provides a structured system for managing performance testing configurations, thresholds, and standards.

# --- Standard Library Imports ---
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict

# --- Data Classes for Configuration ---


@dataclass
class PerformanceThresholds:
    """
    Defines performance thresholds for different types of operations.

    Attributes:
        response_time_ms (float): Maximum acceptable response time in milliseconds.
        memory_overhead_mb (float): Maximum acceptable memory overhead in megabytes.
        query_count_max (int): Maximum number of database queries allowed.
        cache_hit_ratio_min (float): Minimum acceptable cache hit ratio.
    """

    response_time_ms: float
    memory_overhead_mb: float
    query_count_max: int
    cache_hit_ratio_min: float


@dataclass
class MercuryConfiguration:
    """
    A comprehensive data class for Mercury's performance testing configuration.

    This class centralizes all settings, from core behavior to detailed thresholds
    and reporting options, providing a single source of truth for configuration.
    """

    # -- Core Settings --
    enabled: bool = True
    auto_scoring: bool = True
    auto_threshold_adjustment: bool = True
    verbose_reporting: bool = False

    # -- Thresholds and Scoring --
    thresholds: Dict[str, PerformanceThresholds] = None
    scoring_weights: Dict[str, float] = None

    # -- Detection Settings --
    n_plus_one_sensitivity: str = "normal"  # Options: strict, normal, lenient

    # -- Reporting Settings --
    generate_executive_summaries: bool = True
    include_business_impact: bool = True
    show_optimization_potential: bool = True

    def __post_init__(self):
        """Initializes default thresholds and scoring weights after object creation."""
        if self.thresholds is None:
            self.thresholds = self._get_default_thresholds()
        if self.scoring_weights is None:
            self.scoring_weights = self._get_default_scoring_weights()

    def _get_default_thresholds(self) -> Dict[str, PerformanceThresholds]:
        """Returns a dictionary of default performance thresholds for common operation types."""
        return {
            "list_view": PerformanceThresholds(150.0, 25.0, 5, 0.0),
            "detail_view": PerformanceThresholds(80.0, 15.0, 3, 0.0),
            "create_view": PerformanceThresholds(120.0, 20.0, 6, 0.0),
            "update_view": PerformanceThresholds(100.0, 18.0, 5, 0.0),
            "search_view": PerformanceThresholds(250.0, 30.0, 8, 0.0),
            "authentication": PerformanceThresholds(50.0, 10.0, 2, 0.0),
        }

    def _get_default_scoring_weights(self) -> Dict[str, float]:
        """Returns a dictionary of default weights for performance scoring components."""
        return {
            "response_time": 25.0,
            "query_efficiency": 30.0,
            "memory_efficiency": 15.0,
            "cache_performance": 10.0,
            "n_plus_one_penalty": 40.0,
        }


# --- Configuration Management ---


class MercuryConfigurationManager:
    """
    Manages loading, saving, and updating the Mercury configuration.

    This class handles the persistence of the configuration to a JSON file
    and provides methods for dynamic adjustments based on project or environment needs.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initializes the configuration manager.

        Args:
            config_path (Optional[str]): The path to the configuration file.
                                         Defaults to 'mercury_config.json' in the project root.
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "mercury_config.json"
        self.config_path = Path(config_path)
        self._config: Optional[MercuryConfiguration] = None

    def load_configuration(self) -> MercuryConfiguration:
        """
        Loads the configuration from the JSON file or returns default settings.

        Returns:
            MercuryConfiguration: The loaded or default configuration object.
        """
        if self._config:
            return self._config

        if self.config_path.exists():
            try:
                with self.config_path.open("r") as f:
                    data = json.load(f)
                if "thresholds" in data:
                    data["thresholds"] = {
                        op_type: PerformanceThresholds(**threshold_data)
                        for op_type, threshold_data in data["thresholds"].items()
                    }
                self._config = MercuryConfiguration(**data)
            except Exception as e:
                print(f"Warning: Failed to load Mercury configuration from {self.config_path}: {e}")
                self._config = MercuryConfiguration()
        else:
            self._config = MercuryConfiguration()
        return self._config

    def save_configuration(self, config: MercuryConfiguration) -> None:
        """
        Saves the given configuration object to the JSON file.

        Args:
            config (MercuryConfiguration): The configuration object to save.
        """
        self._config = config
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        data = asdict(config)
        if "thresholds" in data:
            data["thresholds"] = {
                op_type: (
                    asdict(threshold_obj) if hasattr(threshold_obj, "__dict__") else threshold_obj
                )
                for op_type, threshold_obj in data["thresholds"].items()
            }
        with self.config_path.open("w") as f:
            json.dump(data, f, indent=2)

    def update_thresholds_for_project(self, project_characteristics: Dict[str, Any]) -> None:
        """
        Dynamically adjusts performance thresholds based on project characteristics.

        Args:
            project_characteristics (Dict[str, Any]): A dictionary describing the project.
        """
        config = self.load_configuration()
        if project_characteristics.get("project_size") == "large":
            for threshold in config.thresholds.values():
                threshold.query_count_max = int(threshold.query_count_max * 1.5)
                threshold.response_time_ms *= 1.3
                threshold.memory_overhead_mb *= 1.2
        if project_characteristics.get("database_type") == "postgresql":
            for threshold in config.thresholds.values():
                threshold.response_time_ms *= 0.8
        if project_characteristics.get("has_caching"):
            for threshold in config.thresholds.values():
                threshold.cache_hit_ratio_min = 0.3
        self.save_configuration(config)

    def create_environment_specific_config(self, environment: str) -> MercuryConfiguration:
        """
        Creates a tailored configuration for a specific deployment environment.

        Args:
            environment (str): The target environment (e.g., 'development', 'production').

        Returns:
            MercuryConfiguration: An adjusted configuration for the specified environment.
        """
        base_config = self.load_configuration()
        if environment == "development":
            for threshold in base_config.thresholds.values():
                threshold.response_time_ms *= 1.5
                threshold.memory_overhead_mb *= 1.3
            base_config.verbose_reporting = True
        elif environment == "staging":
            for threshold in base_config.thresholds.values():
                threshold.response_time_ms *= 0.9
                threshold.memory_overhead_mb *= 0.9
        elif environment == "production":
            for threshold in base_config.thresholds.values():
                threshold.response_time_ms *= 0.7
                threshold.memory_overhead_mb *= 0.8
                threshold.query_count_max = max(1, int(threshold.query_count_max * 0.8))
            base_config.n_plus_one_sensitivity = "strict"
            base_config.include_business_impact = True
        return base_config


# --- Performance Standards ---


class ProjectPerformanceStandards:
    """
    Defines and evaluates project-specific performance goals and deployment gates.
    """

    def __init__(self):
        """Initializes the performance standards with default goals."""
        self.standards = {
            "response_time_goals": {
                "excellent": 50,
                "good": 100,
                "acceptable": 300,
                "poor": 500,
                "critical": float("inf"),
            },
            "database_query_goals": {
                "excellent": 1,
                "good": 3,
                "acceptable": 5,
                "poor": 10,
                "critical": float("inf"),
            },
            "memory_efficiency_goals": {
                "excellent": 10,
                "good": 20,
                "acceptable": 40,
                "poor": 80,
                "critical": float("inf"),
            },
            "n_plus_one_tolerance": {"strict": 0, "normal": 1, "lenient": 3},
        }

    def get_performance_category(self, metric_name: str, value: float) -> str:
        """
        Categorizes a performance metric value based on predefined goals.

        Args:
            metric_name (str): The name of the metric (e.g., 'response_time').
            value (float): The value of the metric.

        Returns:
            str: The performance category (e.g., 'excellent', 'critical').
        """
        goals = self.standards.get(f"{metric_name}_goals", {})
        for category, threshold in goals.items():
            if value <= threshold:
                return category
        return "critical"

    def should_block_deployment(self, metrics: Dict[str, float]) -> Tuple[bool, List[str]]:
        """
        Determines if performance metrics are severe enough to block a deployment.

        Args:
            metrics (Dict[str, float]): A dictionary of performance metrics.

        Returns:
            Tuple[bool, List[str]]: A tuple containing a boolean indicating if deployment
                                     should be blocked and a list of blocking issues.
        """
        blocking_issues = []
        if metrics.get("response_time", 0) > 1000:
            blocking_issues.append("Response time exceeds 1 second.")
        if metrics.get("query_count", 0) > 20:
            blocking_issues.append("Excessive database queries (> 20).")
        if metrics.get("memory_overhead", 0) > 100:
            blocking_issues.append("Excessive memory overhead (> 100MB).")
        if metrics.get("n_plus_one_severity", 0) >= 4:
            blocking_issues.append("Critical N+1 query issues detected.")
        return bool(blocking_issues), blocking_issues


# --- Global Singleton and Helper Functions ---

_config_manager = MercuryConfigurationManager()


def get_mercury_config() -> MercuryConfiguration:
    """Retrieves the global Mercury configuration."""
    return _config_manager.load_configuration()


def update_mercury_config(config: MercuryConfiguration) -> None:
    """Updates and saves the global Mercury configuration."""
    _config_manager.save_configuration(config)


def configure_for_project(project_characteristics: Dict[str, Any]) -> None:
    """Configures Mercury based on specific project characteristics."""
    _config_manager.update_thresholds_for_project(project_characteristics)


def configure_for_environment(environment: str) -> MercuryConfiguration:
    """Retrieves a configuration tailored for a specific environment."""
    return _config_manager.create_environment_specific_config(environment)


# --- Test Execution ---

if __name__ == "__main__":
    # Example of configuring Mercury for a large, complex project.
    project_config = {
        "project_size": "large",
        "database_type": "postgresql",
        "has_caching": True,
        "api_complexity": "high",
    }
    configure_for_project(project_config)

    # Example of retrieving a production-specific configuration.
    prod_config = configure_for_environment("production")
    print(
        f"Production response time threshold for list views: {prod_config.thresholds['list_view'].response_time_ms:.2f}ms"
    )

    # Example of checking if a set of metrics should block a deployment.
    standards = ProjectPerformanceStandards()
    test_metrics = {
        "response_time": 250,
        "query_count": 8,
        "memory_overhead": 35,
        "n_plus_one_severity": 2,
    }
    should_block, issues = standards.should_block_deployment(test_metrics)
    print(f"\nShould block deployment: {should_block}")
    if issues:
        print("Blocking issues:", issues)
