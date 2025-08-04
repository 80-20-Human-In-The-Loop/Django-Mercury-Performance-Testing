"""Validation utilities for the Performance Testing Framework

This module provides validation functions for configuration,
thresholds, and runtime parameters.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Union, Optional, Tuple
from jsonschema import validate, ValidationError, Draft7Validator

from .constants import (
    MAX_VALUES,
    RESPONSE_TIME_THRESHOLDS,
    MEMORY_THRESHOLDS,
    QUERY_COUNT_THRESHOLDS,
    N_PLUS_ONE_THRESHOLDS,
)
from .logging_config import get_logger

logger = get_logger("validation")

# JSON Schema for Mercury configuration
MERCURY_CONFIG_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "enabled": {"type": "boolean"},
        "auto_scoring": {"type": "boolean"},
        "auto_threshold_adjustment": {"type": "boolean"},
        "verbose_reporting": {"type": "boolean"},
        "generate_executive_summaries": {"type": "boolean"},
        "include_business_impact": {"type": "boolean"},
        "show_optimization_potential": {"type": "boolean"},
        "n_plus_one_sensitivity": {"type": "string", "enum": ["strict", "normal", "lenient"]},
        "thresholds": {
            "type": "object",
            "patternProperties": {
                "^[a-zA-Z_]+$": {
                    "type": "object",
                    "properties": {
                        "response_time_ms": {"type": "number", "minimum": 0},
                        "memory_overhead_mb": {"type": "number", "minimum": 0},
                        "query_count_max": {"type": "integer", "minimum": 0},
                        "cache_hit_ratio_min": {"type": "number", "minimum": 0, "maximum": 1},
                    },
                    "required": ["response_time_ms", "memory_overhead_mb", "query_count_max"],
                }
            },
        },
        "scoring_weights": {
            "type": "object",
            "properties": {
                "response_time": {"type": "number", "minimum": 0, "maximum": 100},
                "query_efficiency": {"type": "number", "minimum": 0, "maximum": 100},
                "memory_efficiency": {"type": "number", "minimum": 0, "maximum": 100},
                "cache_performance": {"type": "number", "minimum": 0, "maximum": 100},
                "n_plus_one_penalty": {"type": "number", "minimum": 0, "maximum": 100},
            },
        },
    },
    "additionalProperties": False,
}

# Threshold validation schema
THRESHOLD_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "response_time_ms": {
            "type": "number",
            "minimum": 0,
            "maximum": MAX_VALUES["RESPONSE_TIME_MS"],
        },
        "memory_overhead_mb": {"type": "number", "minimum": 0, "maximum": MAX_VALUES["MEMORY_MB"]},
        "query_count_max": {"type": "integer", "minimum": 0, "maximum": MAX_VALUES["QUERY_COUNT"]},
        "cache_hit_ratio_min": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "additionalProperties": False,
}


def validate_mercury_config(config: Dict[str, Any]) -> Tuple[bool, Optional[List[str]]]:
    """
    Validate a Mercury configuration dictionary against the schema.

    Args:
        config: The configuration dictionary to validate.

    Returns:
        Tuple[bool, Optional[List[str]]]: (is_valid, error_messages)
    """
    try:
        validate(instance=config, schema=MERCURY_CONFIG_SCHEMA)

        # Additional validation: scoring weights must sum to 100
        if "scoring_weights" in config:
            weights = config["scoring_weights"]
            total_weight = sum(weights.values())
            if abs(total_weight - 100.0) > 0.01:  # Allow small floating point errors
                return False, [f"Scoring weights must sum to 100, got {total_weight}"]

        logger.info("Mercury configuration validated successfully")
        return True, None

    except ValidationError as e:
        errors = [e.message]
        # Get all validation errors
        validator = Draft7Validator(MERCURY_CONFIG_SCHEMA)
        for error in validator.iter_errors(config):
            error_path = " -> ".join(str(p) for p in error.path)
            errors.append(f"{error_path}: {error.message}")

        logger.error(f"Mercury configuration validation failed: {errors}")
        return False, errors


def validate_thresholds(
    thresholds: Dict[str, Union[int, float]],
) -> Tuple[bool, Optional[List[str]]]:
    """
    Validate performance thresholds.

    Args:
        thresholds: Dictionary of threshold values.

    Returns:
        Tuple[bool, Optional[List[str]]]: (is_valid, error_messages)
    """
    try:
        validate(instance=thresholds, schema=THRESHOLD_SCHEMA)
        logger.debug(f"Thresholds validated: {thresholds}")
        return True, None

    except ValidationError as e:
        errors = []
        validator = Draft7Validator(THRESHOLD_SCHEMA)
        for error in validator.iter_errors(thresholds):
            errors.append(f"{error.path}: {error.message}")

        logger.error(f"Threshold validation failed: {errors}")
        return False, errors


def validate_operation_name(operation_name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate an operation name for safety and length.

    Args:
        operation_name: The operation name to validate.

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    if not operation_name:
        return False, "Operation name cannot be empty"

    if len(operation_name) > MAX_VALUES["OPERATION_NAME_LENGTH"]:
        return (
            False,
            f"Operation name exceeds maximum length of {MAX_VALUES['OPERATION_NAME_LENGTH']}",
        )

    # Check for potentially dangerous characters (basic sanitization)
    dangerous_chars = ["<", ">", "&", '"', "'", "\n", "\r", "\0"]
    for char in dangerous_chars:
        if char in operation_name:
            return False, f"Operation name contains invalid character: {repr(char)}"

    return True, None


def validate_metrics_values(
    response_time: float, memory_usage: float, query_count: int
) -> Tuple[bool, Optional[List[str]]]:
    """
    Validate that metric values are within reasonable bounds.

    Args:
        response_time: Response time in milliseconds.
        memory_usage: Memory usage in megabytes.
        query_count: Number of database queries.

    Returns:
        Tuple[bool, Optional[List[str]]]: (is_valid, error_messages)
    """
    errors = []

    if response_time < 0:
        errors.append("Response time cannot be negative")
    elif response_time > MAX_VALUES["RESPONSE_TIME_MS"]:
        errors.append(
            f"Response time {response_time}ms exceeds maximum {MAX_VALUES['RESPONSE_TIME_MS']}ms"
        )

    if memory_usage < 0:
        errors.append("Memory usage cannot be negative")
    elif memory_usage > MAX_VALUES["MEMORY_MB"]:
        errors.append(f"Memory usage {memory_usage}MB exceeds maximum {MAX_VALUES['MEMORY_MB']}MB")

    if query_count < 0:
        errors.append("Query count cannot be negative")
    elif query_count > MAX_VALUES["QUERY_COUNT"]:
        errors.append(f"Query count {query_count} exceeds maximum {MAX_VALUES['QUERY_COUNT']}")

    if errors:
        logger.warning(f"Metrics validation failed: {errors}")
        return False, errors

    return True, None


def sanitize_operation_name(operation_name: str) -> str:
    """
    Sanitize an operation name by removing or replacing invalid characters.

    Args:
        operation_name: The operation name to sanitize.

    Returns:
        str: The sanitized operation name.
    """
    # Replace dangerous characters
    sanitized = operation_name
    replacements = {
        "<": "&lt;",
        ">": "&gt;",
        "&": "&amp;",
        '"': "&quot;",
        "'": "&#39;",
        "\n": " ",
        "\r": " ",
        "\0": "",
    }

    for char, replacement in replacements.items():
        sanitized = sanitized.replace(char, replacement)

    # Truncate if too long
    if len(sanitized) > MAX_VALUES["OPERATION_NAME_LENGTH"]:
        sanitized = sanitized[: MAX_VALUES["OPERATION_NAME_LENGTH"] - 3] + "..."

    logger.debug(f"Sanitized operation name: '{operation_name}' -> '{sanitized}'")
    return sanitized


def load_and_validate_config(
    config_path: Union[str, Path],
) -> Tuple[Optional[Dict[str, Any]], Optional[List[str]]]:
    """
    Load and validate a configuration file.

    Args:
        config_path: Path to the configuration file.

    Returns:
        Tuple[Optional[Dict[str, Any]], Optional[List[str]]]: (config, errors)
    """
    config_path = Path(config_path)

    if not config_path.exists():
        return None, [f"Configuration file not found: {config_path}"]

    try:
        with open(config_path, "r") as f:
            config = json.load(f)

        is_valid, errors = validate_mercury_config(config)
        if not is_valid:
            return None, errors

        return config, None

    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in configuration file: {e}"
        logger.error(error_msg)
        return None, [error_msg]
    except Exception as e:
        error_msg = f"Error loading configuration: {e}"
        logger.error(error_msg)
        return None, [error_msg]
