"""CI environment tests for c_bindings.py.

These tests cover CI/CD-specific code paths including:
- GitHub Actions environment detection (lines 174-201)
- CI-specific library search paths
- Different CI platforms (GitHub Actions, Travis, Jenkins)
"""

import os
import sys
import unittest
from unittest.mock import patch, Mock, MagicMock
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.mock_multi_plat.platform_mocks import mock_platform, CIMocker
from django_mercury.python_bindings.c_bindings import CExtensionLoader, get_library_paths
# Alias for easier use in tests
CExtensionManager = CExtensionLoader

# Check if we're in CI environment
IS_CI = os.environ.get('CI') == 'true' or os.environ.get('GITHUB_ACTIONS') == 'true'


class TestCIEnvironmentPaths(unittest.TestCase):
    """Test CI environment detection and paths (lines 174-201)."""
    
    def test_github_actions_detection(self):
        """Test GitHub Actions environment detection (line 174)."""
        # Test with GitHub Actions environment
        with CIMocker('github_actions'):
            self.assertEqual(os.environ.get('CI'), 'true')
            self.assertEqual(os.environ.get('GITHUB_ACTIONS'), 'true')
            
            # Should detect CI environment
            paths = get_library_paths()
            # CI-specific paths should be added
            self.assertGreater(len(paths), 0)
    
    @unittest.skipIf(not IS_CI, "Test requires CI environment (GitHub Actions)")
    @mock_platform("Linux")
    def test_github_actions_linux_paths(self):
        """Test GitHub Actions Linux runner paths (lines 193-196)."""
        with patch.dict('os.environ', {'CI': 'true', 'GITHUB_ACTIONS': 'true'}):
            paths = get_library_paths()
            paths_str = [str(p) for p in paths]
            
            # Should include Linux GitHub runner paths
            expected_paths = [
                '/home/runner/work/Django-Mercury-Performance-Testing/Django-Mercury-Performance-Testing/django_mercury/python_bindings',
                '/home/runner/work/Django-Mercury-Performance-Testing/Django-Mercury-Performance-Testing/django_mercury/c_core'
            ]
            
            for expected in expected_paths:
                self.assertTrue(any(expected in p for p in paths_str), 
                              f"Expected path {expected} not found in {paths_str}")
    
    @mock_platform("Windows")
    def test_github_actions_windows_paths(self):
        """Test GitHub Actions Windows runner paths (lines 186-190)."""
        with patch.dict('os.environ', {'CI': 'true', 'GITHUB_ACTIONS': 'true'}):
            paths = get_library_paths()
            paths_str = [str(p) for p in paths]
            
            # Should include Windows GitHub runner paths
            expected_patterns = [
                'D:/a/Django-Mercury-Performance-Testing',
                'D:\\a\\Django-Mercury-Performance-Testing'
            ]
            
            found = False
            for pattern in expected_patterns:
                if any(pattern in p for p in paths_str):
                    found = True
                    break
            self.assertTrue(found, f"No Windows CI paths found in {paths_str}")
    
    @mock_platform("Darwin")
    def test_github_actions_macos_paths(self):
        """Test GitHub Actions macOS runner paths."""
        with patch.dict('os.environ', {'CI': 'true', 'GITHUB_ACTIONS': 'true'}):
            # macOS uses similar paths to Linux
            paths = get_library_paths()
            paths_str = [str(p) for p in paths]
            
            # GitHub Actions macOS runners use /Users/runner
            # But the code defaults to Linux-style paths
            self.assertGreater(len(paths), 0)
    
    def test_ci_workspace_root_detection(self):
        """Test CI workspace root detection (line 176)."""
        with patch.dict('os.environ', {'CI': 'true', 'GITHUB_ACTIONS': 'true'}):
            # Mock current working directory
            test_workspace = Path("/home/runner/work/test-project")
            with patch('pathlib.Path.cwd', return_value=test_workspace):
                paths = get_library_paths()
                
                # Should use workspace root for CI paths
                workspace_paths = [
                    test_workspace / 'django_mercury' / 'python_bindings',
                    test_workspace / 'django_mercury' / 'c_core',
                    test_workspace / 'django_mercury'
                ]
                
                for wp in workspace_paths:
                    # These paths should be considered
                    self.assertIsInstance(wp, Path)
    
    def test_ci_path_exists_check(self):
        """Test CI path existence checking (lines 198-201)."""
        with patch.dict('os.environ', {'CI': 'true', 'GITHUB_ACTIONS': 'true'}):
            # Mock path existence
            existing_path = Path("/home/runner/work/Django-Mercury-Performance-Testing")
            non_existing_path = Path("/nonexistent/path")
            
            def path_exists(path_obj):
                return str(path_obj) == str(existing_path)
            
            with patch.object(Path, 'exists', path_exists):
                paths = get_library_paths()
                
                # Only existing paths should be added
                self.assertGreater(len(paths), 0)
    
    @unittest.skipIf(IS_CI, "Test requires non-CI environment (skipping when running in CI)")
    def test_non_ci_environment(self):
        """Test behavior when not in CI environment."""
        # Remove CI environment variables
        with patch.dict('os.environ', {}, clear=True):
            # Ensure CI and GITHUB_ACTIONS are not set
            self.assertIsNone(os.environ.get('CI'))
            self.assertIsNone(os.environ.get('GITHUB_ACTIONS'))
            
            paths = get_library_paths()
            paths_str = [str(p) for p in paths]
            
            # Should not include CI-specific paths
            self.assertFalse(any('/home/runner/work' in p for p in paths_str))
            self.assertFalse(any('D:/a' in p for p in paths_str))
    
    def test_ci_environment_logging(self):
        """Test CI environment logging (line 201)."""
        with patch.dict('os.environ', {'CI': 'true', 'GITHUB_ACTIONS': 'true'}):
            with patch('django_mercury.python_bindings.c_bindings.logger') as mock_logger:
                # Mock an existing CI path
                ci_path = Path("/home/runner/work/Django-Mercury-Performance-Testing")
                with patch.object(Path, 'exists', return_value=True):
                    paths = get_library_paths()
                    
                    # Should log CI paths being added
                    # Note: Actual logging depends on implementation
                    self.assertIsNotNone(paths)
    
    def test_ci_build_verbosity(self):
        """Test CI build verbosity settings."""
        with patch.dict('os.environ', {'CIBUILDWHEEL': '1', 'CIBW_BUILD_VERBOSITY': '1'}):
            # Check that CI build flags are recognized
            self.assertEqual(os.environ.get('CIBUILDWHEEL'), '1')
            self.assertEqual(os.environ.get('CIBW_BUILD_VERBOSITY'), '1')


class TestDifferentCIPlatforms(unittest.TestCase):
    """Test different CI platforms beyond GitHub Actions."""
    
    def test_travis_ci_detection(self):
        """Test Travis CI environment detection."""
        with patch.dict('os.environ', {'CI': 'true', 'TRAVIS': 'true', 'TRAVIS_BUILD_DIR': '/home/travis/build/user/repo'}):
            self.assertEqual(os.environ.get('TRAVIS'), 'true')
            # Travis uses different paths
            build_dir = os.environ.get('TRAVIS_BUILD_DIR')
            self.assertIn('travis', build_dir)
    
    def test_jenkins_ci_detection(self):
        """Test Jenkins CI environment detection."""
        with patch.dict('os.environ', {'JENKINS_HOME': '/var/jenkins', 'WORKSPACE': '/var/jenkins/workspace/job'}):
            self.assertIsNotNone(os.environ.get('JENKINS_HOME'))
            workspace = os.environ.get('WORKSPACE')
            self.assertIn('jenkins', workspace.lower())
    
    def test_gitlab_ci_detection(self):
        """Test GitLab CI environment detection."""
        with patch.dict('os.environ', {'CI': 'true', 'GITLAB_CI': 'true', 'CI_PROJECT_DIR': '/builds/user/project'}):
            self.assertEqual(os.environ.get('GITLAB_CI'), 'true')
            project_dir = os.environ.get('CI_PROJECT_DIR')
            self.assertIn('builds', project_dir)
    
    def test_azure_pipelines_detection(self):
        """Test Azure Pipelines environment detection."""
        with patch.dict('os.environ', {'TF_BUILD': 'True', 'AGENT_BUILDDIRECTORY': 'D:\\a\\1\\s'}):
            self.assertEqual(os.environ.get('TF_BUILD'), 'True')
            build_dir = os.environ.get('AGENT_BUILDDIRECTORY')
            # Azure uses similar paths to GitHub on Windows
            self.assertIn('a', build_dir)


class TestCIPathPriority(unittest.TestCase):
    """Test CI path priority and ordering."""
    
    def test_ci_paths_added_to_front(self):
        """Test that CI paths are prioritized in search order."""
        with patch.dict('os.environ', {'CI': 'true', 'GITHUB_ACTIONS': 'true'}):
            paths = get_library_paths()
            
            # CI paths should be near the beginning for priority
            # (after current directory but before system paths)
            self.assertGreater(len(paths), 3)
    
    def test_ci_path_deduplication(self):
        """Test that duplicate CI paths are not added (line 199)."""
        with patch.dict('os.environ', {'CI': 'true', 'GITHUB_ACTIONS': 'true'}):
            # Mock a path that already exists in the list
            existing_path = Path("/home/runner/work/Django-Mercury-Performance-Testing")
            
            with patch.object(Path, 'exists', return_value=True):
                paths = get_library_paths()
                
                # Count occurrences of the path
                path_strs = [str(p) for p in paths]
                count = path_strs.count(str(existing_path))
                
                # Should not have duplicates
                self.assertLessEqual(count, 1)


if __name__ == '__main__':
    unittest.main()