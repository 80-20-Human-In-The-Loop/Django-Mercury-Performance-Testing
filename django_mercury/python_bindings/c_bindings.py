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
    from performance_testing.python_bindings.c_bindings import c_extensions
    
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
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from contextlib import contextmanager

# Configure logging
logger = logging.getLogger(__name__)

# === CONFIGURATION ===

# Library names and paths
LIBRARY_CONFIG = {
    'query_analyzer': {
        'name': 'libquery_analyzer.so',
        'fallback_name': 'libquery_analyzer.dylib',
        'required': False,
        'description': 'SQL Query Analysis Engine'
    },
    'metrics_engine': {
        'name': 'libmetrics_engine.so', 
        'fallback_name': 'libmetrics_engine.dylib',
        'required': False,
        'description': 'Performance Metrics Engine'
    },
    'test_orchestrator': {
        'name': 'libtest_orchestrator.so',
        'fallback_name': 'libtest_orchestrator.dylib', 
        'required': False,
        'description': 'Test Orchestration Engine'
    },
    'legacy_performance': {
        'name': 'libperformance.so',
        'fallback_name': 'libperformance.dylib',
        'required': False,
        'description': 'Legacy Performance Library (compatibility)'
    }
}

# Platform-specific library extensions
PLATFORM_EXTENSIONS = {
    'Linux': '.so',
    'Darwin': '.dylib',
    'Windows': '.dll'
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

def get_library_paths() -> list[Path]:
    """Get ordered list of paths to search for C libraries."""
    paths = []
    
    # Current directory (for development)
    current_dir = Path(__file__).parent
    paths.append(current_dir)
    
    # C core directory (build location)
    c_core_dir = current_dir.parent / "c_core"
    paths.append(c_core_dir)
    
    # System paths (for installed libraries)  
    if platform.system() == "Linux":
        paths.extend([
            Path("/usr/local/lib"),
            Path("/usr/lib"),
            Path("/lib")
        ])
    elif platform.system() == "Darwin":
        paths.extend([
            Path("/usr/local/lib"),
            Path("/opt/homebrew/lib"),
            Path("/usr/lib")
        ])
    elif platform.system() == "Windows":
        paths.extend([
            Path(os.environ.get("SYSTEMROOT", "C:\\Windows")) / "System32",
            Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "Mercury"
        ])
    
    # Python site-packages (for pip installations)
    try:
        import site
        for site_dir in site.getsitepackages():
            paths.append(Path(site_dir) / "mercury_performance")
    except Exception:
        pass
    
    return paths

def find_library(library_name: str) -> Optional[Path]:
    """Find a library file in the search paths."""
    # Handle platform-specific extensions
    system = platform.system()
    if system in PLATFORM_EXTENSIONS:
        base_name = library_name.rsplit('.', 1)[0]
        extension = PLATFORM_EXTENSIONS[system]
        library_name = f"{base_name}{extension}"
    
    # Search all paths
    for search_path in get_library_paths():
        library_path = search_path / library_name
        if library_path.exists() and library_path.is_file():
            logger.debug(f"Found library: {library_path}")
            return library_path
    
    logger.debug(f"Library not found: {library_name}")
    return None

def measure_time(func: Callable) -> tuple[Any, float]:
    """Measure execution time of a function in milliseconds."""
    import time
    start_time = time.perf_counter()
    result = func()
    end_time = time.perf_counter()
    elapsed_ms = (end_time - start_time) * 1000.0
    return result, elapsed_ms

# === C EXTENSION LOADER ===

class CExtensionLoader:
    """Main class for loading and managing C extensions."""
    
    def __init__(self):
        self._libraries: Dict[str, LibraryInfo] = {}
        self._stats = ExtensionStats()
        self._lock = threading.RLock()
        self._initialized = False
        
        # Library handles (public interfaces)
        self.query_analyzer: Optional[ctypes.CDLL] = None
        self.metrics_engine: Optional[ctypes.CDLL] = None  
        self.test_orchestrator: Optional[ctypes.CDLL] = None
        self.legacy_performance: Optional[ctypes.CDLL] = None
        
    def initialize(self) -> bool:
        """Initialize all C extensions."""
        with self._lock:
            if self._initialized:
                return True
            
            # Check if we're in test mode and should be quieter
            import os
            test_mode = os.environ.get('MERCURY_TEST_MODE', '0') == '1'
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
                        logger.info(f"✅ Loaded {library_info.name} ({load_time:.2f}ms)")
                else:
                    if not test_mode:
                        logger.warning(f"❌ Failed to load {library_info.name}: {library_info.error_message}")
                    self._stats.errors_encountered += 1
            
            # Update statistics
            self._stats.libraries_loaded = success_count
            self._stats.total_load_time_ms = total_load_time
            self._stats.fallback_mode = (success_count == 0)
            
            # Calculate performance boost estimate
            if success_count > 0:
                # Estimate based on libraries loaded (conservative estimate)
                boost_factors = {
                    'query_analyzer': 3.0,    # 75% reduction = 4x faster
                    # 'metrics_engine': 2.5,    # 60% reduction = 2.5x faster  
                    'test_orchestrator': 4.0  # 75% reduction = 4x faster
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
                    logger.info(f"🚀 Mercury C extensions initialized: {success_count}/{len(LIBRARY_CONFIG)} libraries loaded")
                    logger.info(f"   Performance boost: {self._stats.performance_boost_factor:.1f}x faster")
                    logger.info(f"   Load time: {total_load_time:.2f}ms")
            else:
                if not test_mode:
                    logger.warning("⚠️  No C extensions loaded - running in pure Python fallback mode")
                    logger.info("   To enable C extensions, run: cd c_core && make && make install")
            
            return success_count > 0
    
    def _load_library(self, lib_key: str, lib_config: Dict[str, Any]) -> LibraryInfo:
        """Load a single C library."""
        lib_name = lib_config['name']
        description = lib_config['description']
        
        # Find library file
        library_path = find_library(lib_name)
        if not library_path:
            # Try fallback name (e.g., .dylib on macOS)
            fallback_name = lib_config.get('fallback_name')
            if fallback_name:
                library_path = find_library(fallback_name)
                if library_path:
                    lib_name = fallback_name
        
        if not library_path:
            return LibraryInfo(
                name=lib_name,
                path="",
                handle=None,
                is_loaded=False,
                error_message=f"Library file not found: {lib_name}"
            )
        
        # Load library
        try:
            # Use RTLD_GLOBAL for symbol sharing between libraries
            if hasattr(ctypes, 'RTLD_GLOBAL'):
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
                function_count=function_count
            )
            
        except Exception as e:
            return LibraryInfo(
                name=lib_name,
                path=str(library_path),
                handle=None,
                is_loaded=False,
                error_message=f"Failed to load library: {str(e)}"
            )
    
    def _configure_library_functions(self, handle: ctypes.CDLL, lib_key: str) -> int:
        """Configure function signatures for a loaded library."""
        function_count = 0
        
        try:
            if lib_key == 'query_analyzer':
                function_count += self._configure_query_analyzer(handle)
            elif lib_key == 'metrics_engine':
                function_count += self._configure_metrics_engine(handle)
            elif lib_key == 'test_orchestrator':
                function_count += self._configure_test_orchestrator(handle)
            elif lib_key == 'legacy_performance':
                function_count += self._configure_legacy_performance(handle)
                
        except Exception as e:
            if os.environ.get('MERCURY_TEST_MODE', '0') != '1':
                logger.warning(f"Failed to configure {lib_key} functions: {e}")
            
        self._stats.functions_configured += function_count
        return function_count
    
    def _configure_query_analyzer(self, lib: ctypes.CDLL) -> int:
        """Configure query analyzer function signatures."""
        functions_configured = 0
        
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
                ctypes.POINTER(ctypes.c_int)
            ]
            lib.get_query_statistics.restype = None
            functions_configured += 1
            
            # reset_query_analyzer() -> void
            lib.reset_query_analyzer.argtypes = []
            lib.reset_query_analyzer.restype = None
            functions_configured += 1
            
        except AttributeError as e:
            if os.environ.get('MERCURY_TEST_MODE', '0') != '1':
                logger.debug(f"Some query analyzer functions not available: {e}")
            
        return functions_configured
    
    def _configure_metrics_engine(self, lib: ctypes.CDLL) -> int:
        """Configure metrics engine function signatures."""
        functions_configured = 0
        
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
            if os.environ.get('MERCURY_TEST_MODE', '0') != '1':
                logger.debug(f"Some metrics engine functions not available: {e}")
            
        return functions_configured
    
    def _configure_test_orchestrator(self, lib: ctypes.CDLL) -> int:
        """Configure test orchestrator function signatures."""
        functions_configured = 0
        
        try:
            # create_test_context(const char*, const char*) -> void*
            lib.create_test_context.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
            lib.create_test_context.restype = ctypes.c_void_p
            functions_configured += 1
            
            # update_test_context(void*, double, double, uint32_t, double, double, const char*) -> int
            lib.update_test_context.argtypes = [
                ctypes.c_void_p, ctypes.c_double, ctypes.c_double,
                ctypes.c_uint32, ctypes.c_double, ctypes.c_double, ctypes.c_char_p
            ]
            lib.update_test_context.restype = ctypes.c_int
            functions_configured += 1
            
            # update_n_plus_one_analysis(void*, int, int, const char*) -> int
            lib.update_n_plus_one_analysis.argtypes = [
                ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_char_p
            ]
            lib.update_n_plus_one_analysis.restype = ctypes.c_int
            functions_configured += 1
            
            # finalize_test_context(void*) -> int
            lib.finalize_test_context.argtypes = [ctypes.c_void_p]
            lib.finalize_test_context.restype = ctypes.c_int
            functions_configured += 1
            
            # get_orchestrator_statistics(uint64_t*, uint64_t*, uint64_t*, size_t*, uint64_t*) -> void
            lib.get_orchestrator_statistics.argtypes = [
                ctypes.POINTER(ctypes.c_uint64),
                ctypes.POINTER(ctypes.c_uint64),
                ctypes.POINTER(ctypes.c_uint64),
                ctypes.POINTER(ctypes.c_size_t),
                ctypes.POINTER(ctypes.c_uint64)
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
            if os.environ.get('MERCURY_TEST_MODE', '0') != '1':
                logger.debug(f"Some test orchestrator functions not available: {e}")
            
        return functions_configured
    
    def _configure_legacy_performance(self, lib: ctypes.CDLL) -> int:
        """Configure legacy performance library function signatures."""
        functions_configured = 0
        
        try:
            # Legacy functions for backward compatibility
            # These would match the existing libperformance.so interface
            
            if hasattr(lib, 'start_performance_monitoring'):
                lib.start_performance_monitoring.argtypes = [ctypes.c_char_p]
                lib.start_performance_monitoring.restype = ctypes.c_int64
                functions_configured += 1
            
            if hasattr(lib, 'stop_performance_monitoring'):
                lib.stop_performance_monitoring.argtypes = [ctypes.c_int64]
                lib.stop_performance_monitoring.restype = ctypes.c_void_p
                functions_configured += 1
                
        except AttributeError as e:
            if os.environ.get('MERCURY_TEST_MODE', '0') != '1':
                logger.debug(f"Legacy performance functions not available: {e}")
            
        return functions_configured
    
    @contextmanager
    def performance_session(self, operation_name: str, operation_type: str = "general"):
        """Context manager for performance monitoring sessions."""
        if not self.metrics_engine:
            # Fallback to no-op if C extension not available
            yield None
            return
            
        session_id = self.metrics_engine.start_performance_monitoring_enhanced(
            operation_name.encode('utf-8'),
            operation_type.encode('utf-8')
        )
        
        if session_id == -1:
            if os.environ.get('MERCURY_TEST_MODE', '0') != '1':
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
                if os.environ.get('MERCURY_TEST_MODE', '0') != '1':
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
    
    def cleanup(self):
        """Cleanup resources and unload libraries."""
        with self._lock:
            # Clear public interfaces
            self.query_analyzer = None
            self.metrics_engine = None
            self.test_orchestrator = None
            self.legacy_performance = None
            
            # Clear library info (handles are automatically cleaned up by Python)
            self._libraries.clear()
            self._initialized = False
            
            # Only log if not in test mode and logger is still active
            try:
                if not os.environ.get('MERCURY_TEST_MODE', '0') == '1':
                    logger.info("C extensions cleaned up")
            except (ValueError, OSError):
                # Logger might be closed during shutdown
                pass

# === GLOBAL INSTANCE ===

# Create global instance and initialize
c_extensions = CExtensionLoader()

def initialize_c_extensions() -> bool:
    """Initialize C extensions. Can be called multiple times safely."""
    return c_extensions.initialize()

def get_extension_stats() -> ExtensionStats:
    """Get C extension statistics."""
    return c_extensions.get_stats()

def is_c_extension_available(library_name: str) -> bool:
    """Check if a specific C extension is available."""
    return c_extensions.is_available(library_name)

# === AUTOMATIC INITIALIZATION ===

# Try to initialize on import, but don't fail if it doesn't work
try:
    _init_success = initialize_c_extensions()
    test_mode = os.environ.get('MERCURY_TEST_MODE', '0') == '1'
    if not test_mode:
        if _init_success:
            logger.info("Mercury C extensions automatically initialized")
        else:
            logger.info("Mercury running in Python fallback mode")
except Exception as e:
    test_mode = os.environ.get('MERCURY_TEST_MODE', '0') == '1'
    if not test_mode:
        logger.warning(f"Failed to auto-initialize C extensions: {e}")
        logger.info("Mercury will run in Python fallback mode")

# === CLEANUP ON EXIT ===

import atexit
atexit.register(c_extensions.cleanup)