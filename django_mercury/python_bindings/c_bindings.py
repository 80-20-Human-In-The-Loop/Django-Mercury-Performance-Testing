# mypy: strict
"""
c_bindings.py - Unified C Extension Loader for Mercury Performance Testing Framework

This module provides a unified interface for loading and configuring the three high-performance
C libraries that power the Mercury framework:
- libquery_analyzer.so    - SQL Query Analysis Engine
- libmetrics_engine.so    - Performance Metrics Engine
- libtest_orchestrator.so - Test Orchestration Engine

Key Features:
- Automatic C extension loading with Python fallback
- Cross-platform compatibility (Linux, macOS, Windows)
- Function signature configuration and validation
- Error handling and graceful degradation
- Performance monitoring and statistics
- Thread-safe initialization and cleanup

Usage:
    from django_mercury.python_bindings.c_bindings import c_extensions

    # Query analysis
    if c_extensions.query_analyzer:
        c_extensions.query_analyzer.analyze_query(b"SELECT * FROM users", 0.05)

    # Metrics collection
    session_id = c_extensions.metrics_engine.start_performance_monitoring_enhanced(
        b"test_operation", b"view"
    )

    # Test orchestration
    context = c_extensions.test_orchestrator.create_test_context(
        b"TestClass", b"test_method"
    )

Author: EduLite Performance Team
Version: 2.0.0
"""

import ctypes
import os
import sys
import logging
import platform
import threading
from pathlib import Path
from typing import Optional, Dict, Any, Callable, List, Tuple
from dataclasses import dataclass
from contextlib import contextmanager

# Configure logging
logger = logging.getLogger(__name__)

# Import validation for security
try:
    from .validation import sanitize_operation_name
except ImportError:
    # Fallback if validation module not available
    def sanitize_operation_name(operation_name: str) -> str:
        """Basic sanitization fallback."""
        dangerous_chars = ["<", ">", "&", '"', "'", "\n", "\r", "\0"]
        sanitized = operation_name
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, "")
        return sanitized[:255] if len(sanitized) > 255 else sanitized

# === CONFIGURATION ===

# Determine library naming scheme based on platform
IS_WINDOWS = platform.system() == "Windows"

# Library names and paths
# Use different names for Windows (Python extensions) vs Unix (standalone libraries)
if IS_WINDOWS:
    # Windows: Python extensions built by setup.py
    # These are built as _c_performance.pyd, _c_metrics.pyd, etc.
    LIBRARY_CONFIG = {
        "query_analyzer": {
            "name": "_c_analyzer",
            "fallback_name": "django_mercury._c_analyzer",
            "required": False,
            "description": "SQL Query Analysis Engine",
        },
        "metrics_engine": {
            "name": "_c_metrics",
            "fallback_name": "django_mercury._c_metrics",
            "required": False,
            "description": "Performance Metrics Engine",
        },
        "test_orchestrator": {
            "name": "_c_orchestrator",
            "fallback_name": "django_mercury._c_orchestrator",
            "required": False,
            "description": "Test Orchestration Engine",
        },
    }
else:
    # Unix: Use Python extensions just like Windows for consistency
    # These are built as _c_analyzer.so, _c_metrics.so, etc.
    LIBRARY_CONFIG = {
        "query_analyzer": {
            "name": "_c_analyzer",
            "fallback_name": "django_mercury._c_analyzer",
            "required": False,
            "description": "SQL Query Analysis Engine",
        },
        "metrics_engine": {
            "name": "_c_metrics",
            "fallback_name": "django_mercury._c_metrics",
            "required": False,
            "description": "Performance Metrics Engine",
        },
        "test_orchestrator": {
            "name": "_c_orchestrator",
            "fallback_name": "django_mercury._c_orchestrator",
            "required": False,
            "description": "Test Orchestration Engine",
        },
    }

# Platform-specific library extensions
PLATFORM_EXTENSIONS = {
    "Linux": ".so", 
    "Darwin": ".so",  # macOS uses .so for compatibility with our Makefile
    "Windows": ".dll",
    # Windows Python extensions
    "Windows_Python": ".pyd"
}

# === DATA STRUCTURES ===


@dataclass
class LibraryInfo:
    """Information about a loaded C library."""

    name: str
    path: str
    handle: Optional[ctypes.CDLL]
    is_loaded: bool
    error_message: Optional[str] = None
    load_time_ms: float = 0.0
    function_count: int = 0


@dataclass
class ExtensionStats:
    """Statistics about C extension usage."""

    libraries_loaded: int = 0
    total_load_time_ms: float = 0.0
    functions_configured: int = 0
    fallback_mode: bool = False
    errors_encountered: int = 0
    performance_boost_factor: float = 1.0


# === UTILITY FUNCTIONS ===


def get_library_paths() -> List[Path]:
    """Get ordered list of paths to search for C libraries."""
    paths = []

    # Current directory (for development)
    current_dir = Path(__file__).parent
    paths.append(current_dir)

    # C core directory (build location)
    c_core_dir = current_dir.parent / "c_core"
    paths.append(c_core_dir)
    
    # Check if we're in a CI environment - libraries might be in different locations
    if os.environ.get('CI') or os.environ.get('GITHUB_ACTIONS'):
        # In CI, also check workspace and runner paths
        workspace_root = Path.cwd()
        ci_paths = [
            workspace_root / 'django_mercury' / 'python_bindings',
            workspace_root / 'django_mercury' / 'c_core',
            workspace_root / 'django_mercury',  # Windows might have .pyd files here
        ]
        
        # Add platform-specific CI paths
        if platform.system() == "Windows":
            # Windows GitHub Actions runner paths
            ci_paths.extend([
                Path('D:/a') / 'Django-Mercury-Performance-Testing' / 'Django-Mercury-Performance-Testing' / 'django_mercury' / 'python_bindings',
                Path('D:/a') / 'Django-Mercury-Performance-Testing' / 'Django-Mercury-Performance-Testing' / 'django_mercury' / 'c_core',
                Path('D:/a') / 'Django-Mercury-Performance-Testing' / 'Django-Mercury-Performance-Testing' / 'django_mercury',
            ])
        else:
            # Linux/macOS GitHub Actions runner paths
            ci_paths.extend([
                Path('/home/runner/work') / 'Django-Mercury-Performance-Testing' / 'Django-Mercury-Performance-Testing' / 'django_mercury' / 'python_bindings',
                Path('/home/runner/work') / 'Django-Mercury-Performance-Testing' / 'Django-Mercury-Performance-Testing' / 'django_mercury' / 'c_core',
            ])
        
        for path in ci_paths:
            if path.exists() and path not in paths:
                paths.append(path)
                logger.debug(f"Added CI path: {path}")

    # System paths (for installed libraries)
    if platform.system() == "Linux":
        paths.extend([Path("/usr/local/lib"), Path("/usr/lib"), Path("/lib")])
    elif platform.system() == "Darwin":
        paths.extend([Path("/usr/local/lib"), Path("/opt/homebrew/lib"), Path("/usr/lib")])
    elif platform.system() == "Windows":
        paths.extend(
            [
                Path(os.environ.get("SYSTEMROOT", "C:\\Windows")) / "System32",
                Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "Mercury",
            ]
        )

    # Python site-packages (for pip installations)
    try:
        import site

        for site_dir in site.getsitepackages():
            paths.append(Path(site_dir) / "mercury_performance")
    except Exception:
        pass
    
    # Debug output if requested
    if os.environ.get('DEBUG_C_LOADING'):
        logger.info(f"Searching for C libraries in {len(paths)} paths:")
        for i, path in enumerate(paths, 1):
            logger.info(f"  {i}. {path}")

    return paths


def find_library(library_name: str) -> Optional[Path]:
    """Find a library file in the search paths.
    
    On Windows, tries both .dll and .pyd extensions.
    On other platforms, uses platform-specific extension.
    """
    # Handle platform-specific extensions
    system = platform.system()
    base_name = library_name.rsplit(".", 1)[0]
    
    # On Windows, try both .pyd and .dll (.pyd is for Python extensions)
    if system == "Windows":
        extensions_to_try = [".pyd", ".dll"]
    elif system in PLATFORM_EXTENSIONS:
        extensions_to_try = [PLATFORM_EXTENSIONS[system]]
    else:
        # Fallback - try the original name
        extensions_to_try = [""]
    
    # Search all paths with all extensions
    for search_path in get_library_paths():
        for extension in extensions_to_try:
            if extension:
                library_file = f"{base_name}{extension}"
            else:
                library_file = library_name
            
            library_path = search_path / library_file
            if library_path.exists() and library_path.is_file():
                logger.debug(f"Found library: {library_path}")
                return library_path

    logger.debug(f"Library not found: {library_name} (tried extensions: {extensions_to_try})")
    return None


def measure_time(func: Callable[[], Any]) -> Tuple[Any, float]:
    """Measure execution time of a function in milliseconds.
    
    This function helps track how long operations take. Performance monitoring
    is essential for finding slow parts of your application.
    
    Args:
        func: Function to time (must take no parameters).
        
    Returns:
        Tuple containing (function_result, execution_time_in_milliseconds).
        
    Example:
        >>> result, time_ms = measure_time(lambda: expensive_calculation())
        >>> print(f"Calculation took {time_ms:.2f}ms")
        
    Note:
        Uses time.perf_counter() for high-precision timing. This is the most
        accurate way to measure short operations in Python.
    """
    import time

    start_time = time.perf_counter()
    result = func()
    end_time = time.perf_counter()
    elapsed_ms = (end_time - start_time) * 1000.0
    return result, elapsed_ms


# === C EXTENSION LOADER ===


class CExtensionLoader:
    """Main class for loading and managing C extensions."""

    def __init__(self) -> None:
        self._libraries: Dict[str, LibraryInfo] = {}
        self._stats = ExtensionStats()
        self._lock = threading.RLock()
        self._initialized = False

        # Library handles (public interfaces)
        self.query_analyzer: Optional[ctypes.CDLL] = None
        self.metrics_engine: Optional[ctypes.CDLL] = None
        self.test_orchestrator: Optional[ctypes.CDLL] = None

    def initialize(self, force_reinit: bool = False) -> bool:
        """Initialize all C extensions.
        
        Args:
            force_reinit: If True, force reinitialization even if already initialized.
                         This is useful for tests that need a clean state.
        
        Returns:
            True if at least one C extension loaded successfully, False otherwise.
        """
        with self._lock:
            if self._initialized and not force_reinit:
                return True
            
            # Clean up any existing state if reinitializing
            if self._initialized and force_reinit:
                self.cleanup()

            # Check if we're in test mode and should be quieter
            import os

            test_mode = os.environ.get("MERCURY_TEST_MODE", "0") == "1"
            if not test_mode:
                logger.info("Initializing Mercury C extensions...")

            success_count = 0
            total_load_time = 0.0

            # Load each library
            for lib_key, lib_config in LIBRARY_CONFIG.items():
                library_info, load_time = measure_time(
                    lambda: self._load_library(lib_key, lib_config)
                )

                self._libraries[lib_key] = library_info
                total_load_time += load_time

                if library_info.is_loaded:
                    success_count += 1
                    # Set public interface
                    setattr(self, lib_key, library_info.handle)
                    if not test_mode:
                        logger.info(f"Loaded {library_info.name} ({load_time:.2f}ms)")
                else:
                    if not test_mode:
                        logger.warning(
                            f"Failed to load {library_info.name}: {library_info.error_message}"
                        )
                    self._stats.errors_encountered += 1

            # Update statistics
            self._stats.libraries_loaded = success_count
            self._stats.total_load_time_ms = total_load_time
            self._stats.fallback_mode = success_count == 0

            # Calculate performance boost estimate
            if success_count > 0:
                # Estimate based on libraries loaded (conservative estimate)
                boost_factors = {
                    "query_analyzer": 3.0,  # 75% reduction = 4x faster
                    # 'metrics_engine': 2.5,    # 60% reduction = 2.5x faster
                    "test_orchestrator": 4.0,  # 75% reduction = 4x faster
                }

                total_boost = 1.0
                for lib_key in boost_factors:
                    if self._libraries.get(lib_key, LibraryInfo("", "", None, False)).is_loaded:
                        total_boost *= boost_factors[lib_key]

                self._stats.performance_boost_factor = total_boost

            self._initialized = True

            # Log initialization summary
            if success_count > 0:
                if not test_mode:
                    logger.info(
                        f"Mercury C extensions initialized: {success_count}/{len(LIBRARY_CONFIG)} "
                        f"libraries loaded"
                    )
                    logger.info(
                        f"   Performance boost: {self._stats.performance_boost_factor:.1f}x faster"
                    )
                    logger.info(f"   Load time: {total_load_time:.2f}ms")
            else:
                if not test_mode:
                    logger.warning(
                        "No C extensions loaded - running in pure Python fallback mode"
                    )
                    logger.info("   To enable C extensions, run: cd c_core && make && make install")

            return success_count > 0

    def _load_library(self, lib_key: str, lib_config: Dict[str, Any]) -> LibraryInfo:
        """Load a single C library."""
        lib_name = lib_config["name"]
        
        # All platforms: Try to import as Python extension module
        # This provides consistency across platforms and better packaging support
        try:
            # Import the Python extension module using importlib for better mockability
            module_map = {
                "query_analyzer": "django_mercury._c_analyzer",
                "metrics_engine": "django_mercury._c_metrics",
                "test_orchestrator": "django_mercury._c_orchestrator",
            }
            
            module_name = module_map.get(lib_key)
            if not module_name:
                raise ImportError(f"Unknown library key: {lib_key}")
            
            # Use importlib.import_module for mockability in tests
            import importlib
            module = importlib.import_module(module_name)
            
            # Configure function signatures (for Python modules)
            function_count = self._configure_library_functions(module, lib_key)
            
            # The module itself is the "handle"
            return LibraryInfo(
                name=lib_name,
                path=f"<Python module: {module.__name__}>",
                handle=module,  # Use the module as the handle
                is_loaded=True,
                function_count=function_count,
            )
        except (ImportError, MemoryError, PermissionError, Exception) as e:
            # Handle specific error types
            if isinstance(e, MemoryError):
                return LibraryInfo(
                    name=lib_name,
                    path="",
                    handle=None,
                    is_loaded=False,
                    error_message=f"Out of memory while loading {lib_name}",
                )
            elif isinstance(e, PermissionError):
                return LibraryInfo(
                    name=lib_name,
                    path="",
                    handle=None,
                    is_loaded=False,
                    error_message=f"Permission denied while loading {lib_name}",
                )
            
            # If Python extension not found, try loading as standalone library (fallback)
            # This is mainly for development environments where libraries are built with make
            if not IS_WINDOWS and isinstance(e, ImportError):
                # Try loading standalone .so file for Unix/Linux development
                library_path = find_library(f"lib{lib_key.replace('_', '')}")
                if not library_path:
                    # Also try the exact library name from config
                    fallback_name = lib_config.get("fallback_name")
                    if fallback_name and "django_mercury" not in fallback_name:
                        library_path = find_library(fallback_name)
                
                if library_path:
                    try:
                        # Use RTLD_GLOBAL for symbol sharing between libraries
                        if hasattr(ctypes, "RTLD_GLOBAL"):
                            handle = ctypes.CDLL(str(library_path), mode=ctypes.RTLD_GLOBAL)
                        else:
                            handle = ctypes.CDLL(str(library_path))

                        # Configure function signatures
                        function_count = self._configure_library_functions(handle, lib_key)

                        return LibraryInfo(
                            name=lib_name,
                            path=str(library_path),
                            handle=handle,
                            is_loaded=True,
                            function_count=function_count,
                        )
                    except Exception as load_error:
                        # Continue to return import error below
                        pass
            
            return LibraryInfo(
                name=lib_name,
                path="",
                handle=None,
                is_loaded=False,
                error_message=f"Failed to import Python extension: {str(e)}",
            )

    def _configure_library_functions(self, handle: ctypes.CDLL, lib_key: str) -> int:
        """Configure function signatures for a loaded library."""
        function_count = 0

        try:
            if lib_key == "query_analyzer":
                function_count += self._configure_query_analyzer(handle)
            elif lib_key == "metrics_engine":
                function_count += self._configure_metrics_engine(handle)
            elif lib_key == "test_orchestrator":
                function_count += self._configure_test_orchestrator(handle)

        except Exception as e:
            if os.environ.get("MERCURY_TEST_MODE", "0") != "1":
                logger.warning(f"Failed to configure {lib_key} functions: {e}")

        self._stats.functions_configured += function_count
        return function_count

    def _configure_query_analyzer(self, lib) -> int:
        """Configure query analyzer function signatures."""
        functions_configured = 0
        
        # Check if it's a Python module (Windows) or ctypes.CDLL
        if hasattr(lib, '__name__'):  # It's a Python module
            # For Python extensions, check for the class
            if hasattr(lib, 'QueryAnalyzer'):
                functions_configured += 1  # The class wraps all functionality
        else:
            # It's a ctypes.CDLL - configure function signatures
            try:
                # analyze_query(const char* query_text, double execution_time) -> int
                lib.analyze_query.argtypes = [ctypes.c_char_p, ctypes.c_double]
                lib.analyze_query.restype = ctypes.c_int
                functions_configured += 1

                # get_duplicate_queries(char* result_buffer, size_t buffer_size) -> int
                lib.get_duplicate_queries.argtypes = [ctypes.c_char_p, ctypes.c_size_t]
                lib.get_duplicate_queries.restype = ctypes.c_int
                functions_configured += 1

                # detect_n_plus_one_patterns() -> int
                lib.detect_n_plus_one_patterns.argtypes = []
                lib.detect_n_plus_one_patterns.restype = ctypes.c_int
                functions_configured += 1

                # get_n_plus_one_severity() -> int
                lib.get_n_plus_one_severity.argtypes = []
                lib.get_n_plus_one_severity.restype = ctypes.c_int
                functions_configured += 1

                # get_n_plus_one_cause() -> int
                lib.get_n_plus_one_cause.argtypes = []
                lib.get_n_plus_one_cause.restype = ctypes.c_int
                functions_configured += 1

                # get_optimization_suggestion() -> const char*
                lib.get_optimization_suggestion.argtypes = []
                lib.get_optimization_suggestion.restype = ctypes.c_char_p
                functions_configured += 1

                # get_query_statistics(uint64_t*, uint64_t*, uint64_t*, int*) -> void
                lib.get_query_statistics.argtypes = [
                    ctypes.POINTER(ctypes.c_uint64),
                    ctypes.POINTER(ctypes.c_uint64),
                    ctypes.POINTER(ctypes.c_uint64),
                    ctypes.POINTER(ctypes.c_int),
                ]
                lib.get_query_statistics.restype = None
                functions_configured += 1

                # reset_query_analyzer() -> void
                lib.reset_query_analyzer.argtypes = []
                lib.reset_query_analyzer.restype = None
                functions_configured += 1

            except AttributeError as e:
                if os.environ.get("MERCURY_TEST_MODE", "0") != "1":
                    logger.debug(f"Some query analyzer functions not available: {e}")

        return functions_configured

    def _configure_metrics_engine(self, lib) -> int:
        """Configure metrics engine function signatures."""
        functions_configured = 0
        
        # Check if it's a Python module (Windows) or ctypes.CDLL
        if hasattr(lib, '__name__'):  # It's a Python module
            # For Python extensions, check for the class
            if hasattr(lib, 'MetricsEngine'):
                functions_configured += 1  # The class wraps all functionality
        else:
            # It's a ctypes.CDLL - configure function signatures
            try:
                # start_performance_monitoring_enhanced(const char*, const char*) -> int64_t
                lib.start_performance_monitoring_enhanced.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
                lib.start_performance_monitoring_enhanced.restype = ctypes.c_int64
                functions_configured += 1

                # stop_performance_monitoring_enhanced(int64_t) -> MercuryMetrics*
                lib.stop_performance_monitoring_enhanced.argtypes = [ctypes.c_int64]
                lib.stop_performance_monitoring_enhanced.restype = ctypes.c_void_p
                functions_configured += 1

                # get_elapsed_time_ms(const MercuryMetrics*) -> double
                lib.get_elapsed_time_ms.argtypes = [ctypes.c_void_p]
                lib.get_elapsed_time_ms.restype = ctypes.c_double
                functions_configured += 1

                # get_memory_usage_mb(const MercuryMetrics*) -> double
                lib.get_memory_usage_mb.argtypes = [ctypes.c_void_p]
                lib.get_memory_usage_mb.restype = ctypes.c_double
                functions_configured += 1

                # get_query_count(const MercuryMetrics*) -> uint32_t
                lib.get_query_count.argtypes = [ctypes.c_void_p]
                lib.get_query_count.restype = ctypes.c_uint32
                functions_configured += 1

                # get_cache_hit_count(const MercuryMetrics*) -> uint32_t
                lib.get_cache_hit_count.argtypes = [ctypes.c_void_p]
                lib.get_cache_hit_count.restype = ctypes.c_uint32
                functions_configured += 1

                # get_cache_miss_count(const MercuryMetrics*) -> uint32_t
                lib.get_cache_miss_count.argtypes = [ctypes.c_void_p]
                lib.get_cache_miss_count.restype = ctypes.c_uint32
                functions_configured += 1

                # get_cache_hit_ratio(const MercuryMetrics*) -> double
                lib.get_cache_hit_ratio.argtypes = [ctypes.c_void_p]
                lib.get_cache_hit_ratio.restype = ctypes.c_double
                functions_configured += 1

                # N+1 detection functions
                lib.has_n_plus_one_pattern.argtypes = [ctypes.c_void_p]
                lib.has_n_plus_one_pattern.restype = ctypes.c_int
                functions_configured += 1

                lib.detect_n_plus_one_severe.argtypes = [ctypes.c_void_p]
                lib.detect_n_plus_one_severe.restype = ctypes.c_int
                functions_configured += 1

                lib.detect_n_plus_one_moderate.argtypes = [ctypes.c_void_p]
                lib.detect_n_plus_one_moderate.restype = ctypes.c_int
                functions_configured += 1

                # free_metrics(MercuryMetrics*) -> void
                lib.free_metrics.argtypes = [ctypes.c_void_p]
                lib.free_metrics.restype = None
                functions_configured += 1

                # Counter functions (called by Django hooks)
                lib.increment_query_count.argtypes = []
                lib.increment_query_count.restype = None
                functions_configured += 1

                lib.increment_cache_hits.argtypes = []
                lib.increment_cache_hits.restype = None
                functions_configured += 1

                lib.increment_cache_misses.argtypes = []
                lib.increment_cache_misses.restype = None
                functions_configured += 1

                lib.reset_global_counters.argtypes = []
                lib.reset_global_counters.restype = None
                functions_configured += 1

            except AttributeError as e:
                if os.environ.get("MERCURY_TEST_MODE", "0") != "1":
                    logger.debug(f"Some metrics engine functions not available: {e}")

        return functions_configured

    def _configure_test_orchestrator(self, lib: Any) -> int:
        """Configure test orchestrator function signatures.
        
        Args:
            lib: Either ctypes.CDLL (Unix) or Python module (Windows)
        """
        functions_configured = 0
        
        # Check if it's a Python module or ctypes.CDLL
        if hasattr(lib, '__name__') or hasattr(lib, '__file__'):
            # It's a Python module - check for the class
            if hasattr(lib, 'TestOrchestrator'):
                functions_configured += 1  # The class wraps all functionality
        else:
            # It's a ctypes.CDLL - configure function signatures
            try:
                # create_test_context(const char*, const char*) -> void*
                lib.create_test_context.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
                lib.create_test_context.restype = ctypes.c_void_p
                functions_configured += 1

                # update_test_context(void*, double, double, uint32_t, double, double, 
                #                     const char*) -> int
                lib.update_test_context.argtypes = [
                    ctypes.c_void_p,
                    ctypes.c_double,
                    ctypes.c_double,
                    ctypes.c_uint32,
                    ctypes.c_double,
                    ctypes.c_double,
                    ctypes.c_char_p,
                ]
                lib.update_test_context.restype = ctypes.c_int
                functions_configured += 1

                # update_n_plus_one_analysis(void*, int, int, const char*) -> int
                lib.update_n_plus_one_analysis.argtypes = [
                    ctypes.c_void_p,
                    ctypes.c_int,
                    ctypes.c_int,
                    ctypes.c_char_p,
                ]
                lib.update_n_plus_one_analysis.restype = ctypes.c_int
                functions_configured += 1

                # finalize_test_context(void*) -> int
                lib.finalize_test_context.argtypes = [ctypes.c_void_p]
                lib.finalize_test_context.restype = ctypes.c_int
                functions_configured += 1

                # get_orchestrator_statistics(uint64_t*, uint64_t*, uint64_t*, size_t*, 
                #                              uint64_t*) -> void
                lib.get_orchestrator_statistics.argtypes = [
                    ctypes.POINTER(ctypes.c_uint64),
                    ctypes.POINTER(ctypes.c_uint64),
                    ctypes.POINTER(ctypes.c_uint64),
                    ctypes.POINTER(ctypes.c_size_t),
                    ctypes.POINTER(ctypes.c_uint64),
                ]
                lib.get_orchestrator_statistics.restype = None
                functions_configured += 1

                # Configuration functions
                lib.load_binary_configuration.argtypes = [ctypes.c_char_p]
                lib.load_binary_configuration.restype = ctypes.c_int
                functions_configured += 1

                lib.save_binary_configuration.argtypes = [ctypes.c_char_p]
                lib.save_binary_configuration.restype = ctypes.c_int
                functions_configured += 1

            except AttributeError as e:
                if os.environ.get("MERCURY_TEST_MODE", "0") != "1":
                    logger.debug(f"Some test orchestrator functions not available: {e}")

        return functions_configured

    @contextmanager
    def performance_session(self, operation_name: str, operation_type: str = "general") -> Any:
        """Context manager for performance monitoring sessions.
        
        This context manager automatically starts and stops performance monitoring
        for a specific operation. It handles cleanup even if errors occur.
        
        Args:
            operation_name: Name of the operation being monitored (e.g., "UserListView").
            operation_type: Type of operation. Options:
                - 'general': Default for any operation
                - 'view': Django view functions  
                - 'api': REST API endpoints
                - 'query': Database operations
                - 'search': Search operations
                - 'create': Create operations
                - 'update': Update operations
                - 'delete': Delete operations
                
        Yields:
            session_id: Unique ID for this monitoring session, or None if C extensions
                       not available.
                       
        Example:
            >>> with c_extensions.performance_session("UserSearch", "api") as session:
            ...     response = client.get("/api/users/search?q=test")
            >>> # Metrics are automatically collected and cleaned up
            
        Note:
            This function sanitizes inputs for security and validates operation types.
            Falls back gracefully if C extensions are not available.
        """
        # Sanitize inputs for security
        operation_name = sanitize_operation_name(operation_name)
        
        # Validate operation_type against allowed values
        allowed_types = {"general", "view", "api", "query", "search", "create", "update", "delete"}
        if operation_type not in allowed_types:
            logger.warning(f"Invalid operation_type '{operation_type}', using 'general'")
            operation_type = "general"
        
        if not self.metrics_engine:
            # Fallback to no-op if C extension not available
            yield None
            return

        session_id = self.metrics_engine.start_performance_monitoring_enhanced(
            operation_name.encode("utf-8"), operation_type.encode("utf-8")
        )

        if session_id == -1:
            if os.environ.get("MERCURY_TEST_MODE", "0") != "1":
                logger.warning("Failed to start performance monitoring session")
            yield None
            return

        try:
            yield session_id
        finally:
            try:
                metrics_ptr = self.metrics_engine.stop_performance_monitoring_enhanced(session_id)
                if metrics_ptr:
                    # Extract metrics here if needed
                    self.metrics_engine.free_metrics(metrics_ptr)
            except Exception as e:
                if os.environ.get("MERCURY_TEST_MODE", "0") != "1":
                    logger.error(f"Error stopping performance session: {e}")

    def get_stats(self) -> ExtensionStats:
        """Get extension loading and usage statistics."""
        return self._stats

    def get_library_info(self, lib_key: str) -> Optional[LibraryInfo]:
        """Get information about a specific library."""
        return self._libraries.get(lib_key)

    def is_available(self, lib_key: str) -> bool:
        """Check if a specific library is available."""
        lib_info = self._libraries.get(lib_key)
        return lib_info is not None and lib_info.is_loaded

    def cleanup(self) -> None:
        """Cleanup resources and unload libraries."""
        with self._lock:
            # Clear public interfaces
            self.query_analyzer = None
            self.metrics_engine = None
            self.test_orchestrator = None

            # Clear library info (handles are automatically cleaned up by Python)
            self._libraries.clear()
            self._initialized = False

            # Only log if not in test mode and logger is still active
            try:
                if not os.environ.get("MERCURY_TEST_MODE", "0") == "1":
                    logger.info("C extensions cleaned up")
            except (ValueError, OSError):
                # Logger might be closed during shutdown
                pass


# === GLOBAL INSTANCE ===

# Create global instance and initialize
c_extensions = CExtensionLoader()

# Export availability flags for easy checking
def are_c_extensions_available() -> bool:
    """Check if any C extensions are available.
    
    Returns:
        True if at least one C extension is loaded, False otherwise.
    """
    return (
        c_extensions.query_analyzer is not None or
        c_extensions.metrics_engine is not None or
        c_extensions.test_orchestrator is not None
    )


def is_pure_python_mode() -> bool:
    """Check if running in pure Python mode.
    
    Returns:
        True if DJANGO_MERCURY_PURE_PYTHON=1 or no C extensions available.
    """
    return (
        os.environ.get("DJANGO_MERCURY_PURE_PYTHON", "0") == "1" or
        not are_c_extensions_available()
    )


def initialize_c_extensions(force_reinit: bool = False) -> bool:
    """Initialize C extensions. Can be called multiple times safely.
    
    This function loads the high-performance C libraries that make Mercury fast.
    If C extensions fail to load, Mercury falls back to pure Python.
    
    Args:
        force_reinit: If True, force reinitialization even if already initialized.
                     This is useful for tests that need a clean state.
    
    Returns:
        True if at least one C extension loaded successfully, False otherwise.
        
    Example:
        >>> success = initialize_c_extensions()
        >>> if success:
        ...     print("C extensions loaded - Mercury will be fast!")
        ... else:
        ...     print("Using Python fallback - still works but slower")
        
    Note:
        This function is called automatically when you import c_bindings.
        You only need to call it manually if you want to check the result.
    """
    return c_extensions.initialize(force_reinit=force_reinit)


def get_extension_stats() -> ExtensionStats:
    """Get C extension statistics."""
    return c_extensions.get_stats()


def is_c_extension_available(library_name: str) -> bool:
    """Check if a specific C extension is available."""
    return c_extensions.is_available(library_name)


# === AUTOMATIC INITIALIZATION ===

# Try to initialize on import, but don't fail if it doesn't work
# Skip automatic initialization if MERCURY_DEFER_INIT is set (for CI environments)
if os.environ.get("MERCURY_DEFER_INIT", "0") != "1":
    try:
        _init_success = initialize_c_extensions()
        test_mode = os.environ.get("MERCURY_TEST_MODE", "0") == "1"
        if not test_mode:
            if _init_success:
                logger.info("Mercury C extensions automatically initialized")
            else:
                logger.info("Mercury running in Python fallback mode")
    except Exception as e:
        test_mode = os.environ.get("MERCURY_TEST_MODE", "0") == "1"
        if not test_mode:
            logger.warning(f"Failed to auto-initialize C extensions: {e}")
            logger.info("Mercury will run in Python fallback mode")
else:
    # Deferred initialization mode - will be initialized later by test runner
    logger.debug("Mercury C extensions initialization deferred (MERCURY_DEFER_INIT=1)")

# === CLEANUP ON EXIT ===

import atexit

atexit.register(c_extensions.cleanup)
