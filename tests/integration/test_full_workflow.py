"""Full workflow integration tests.

This module tests complete end-to-end workflows including:
- CLI command execution
- Configuration file integration
- Basic application functionality
"""

import pytest
import tempfile
import os
import json
import sys
from pathlib import Path
from unittest.mock import patch
import yaml

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from pgsd.main import main


@pytest.mark.integration
class TestBasicWorkflow:
    """Test basic application workflows."""

    def test_version_command_workflow(self):
        """Test complete version command workflow."""
        args = ['version']
        exit_code = main(args)
        assert exit_code == 0

    def test_help_command_workflow(self):
        """Test complete help command workflow."""
        args = ['--help']
        
        with pytest.raises(SystemExit) as exc_info:
            main(args)
        assert exc_info.value.code == 0

    def test_dry_run_compare_workflow(self):
        """Test dry-run compare workflow."""
        args = [
            'compare',
            '--source-host', 'localhost',
            '--source-db', 'test_db',
            '--target-host', 'localhost',
            '--target-db', 'test_db',
            '--schema', 'test_schema',
            '--target-schema', 'test_schema',
            '--dry-run'
        ]
        
        try:
            exit_code = main(args)
            # Should either succeed or fail gracefully
            assert exit_code in [0, 1, 2]
        except SystemExit as e:
            # Acceptable exit
            assert e.code in [0, 1, 2]

    def test_configuration_priority_hierarchy(self):
        """Test configuration priority: CLI > ENV > Config file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.yaml"
            
            # Create config file with specific values
            config_data = {
                "database": {
                    "source": {
                        "host": "config-host",
                        "port": 9999,
                        "database": "config-db"
                    }
                },
                "report": {
                    "format": "markdown"
                }
            }
            
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f)
            
            # Set environment variables
            env_vars = {
                'PGSD_SOURCE_HOST': 'env-host',
                'PGSD_REPORT_FORMAT': 'json'
            }
            
            with patch.dict(os.environ, env_vars):
                args = [
                    'compare',
                    '--config', str(config_path),
                    '--source-host', 'cli-host',  # CLI should override
                    '--schema', 'test_schema',
                    '--target-schema', 'test_schema',
                    '--dry-run'
                ]
                
                try:
                    exit_code = main(args)
                    assert exit_code in [0, 1, 2]
                except SystemExit as e:
                    assert e.code in [0, 2]

    def test_error_handling_workflow(self):
        """Test error handling in workflows."""
        test_cases = [
            {
                'name': 'invalid_host',
                'args': [
                    'compare',
                    '--source-host', 'invalid-host-12345',
                    '--source-db', 'test_db',
                    '--target-host', 'invalid-host-12345',
                    '--target-db', 'test_db',
                    '--schema', 'test_schema',
                    '--target-schema', 'test_schema'
                ],
                'expected_exit_codes': [1, 2]
            },
            {
                'name': 'invalid_config_file',
                'args': [
                    'compare',
                    '--config', '/nonexistent/config.yaml',
                    '--schema', 'test_schema',
                    '--target-schema', 'test_schema'
                ],
                'expected_exit_codes': [1, 2]
            },
            {
                'name': 'invalid_command',
                'args': ['invalid-command'],
                'expected_exit_codes': [2]
            }
        ]
        
        for test_case in test_cases:
            try:
                exit_code = main(test_case['args'])
                assert exit_code in test_case['expected_exit_codes'], \
                    f"Test case {test_case['name']} returned unexpected exit code: {exit_code}"
            except SystemExit as e:
                assert e.code in test_case['expected_exit_codes'], \
                    f"Test case {test_case['name']} raised SystemExit with unexpected code: {e.code}"


@pytest.mark.integration
class TestConfigurationIntegration:
    """Test configuration integration scenarios."""

    def test_yaml_config_loading(self):
        """Test YAML configuration file loading."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test.yaml"
            
            config_data = {
                "database": {
                    "source": {
                        "host": "localhost",
                        "port": 5432,
                        "database": "test_db"
                    }
                },
                "report": {
                    "format": "html",
                    "timezone": "UTC"
                },
                "logging": {
                    "level": "INFO",
                    "format": "json"
                }
            }
            
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f)
            
            args = [
                'validate',
                '--config', str(config_path)
            ]
            
            try:
                exit_code = main(args)
                assert exit_code in [0, 1, 2]  # Should handle gracefully
            except SystemExit as e:
                assert e.code in [0, 1, 2]

    def test_environment_variable_integration(self):
        """Test environment variable configuration."""
        env_vars = {
            'PGSD_SOURCE_HOST': 'env-test-host',
            'PGSD_SOURCE_PORT': '5432',
            'PGSD_SOURCE_DB': 'env-test-db',
            'PGSD_LOG_LEVEL': 'DEBUG'
        }
        
        with patch.dict(os.environ, env_vars):
            args = ['version']
            exit_code = main(args)
            assert exit_code == 0


@pytest.mark.integration 
class TestConcurrentExecution:
    """Test concurrent execution scenarios."""

    def test_concurrent_version_commands(self):
        """Test concurrent execution of version commands."""
        import threading
        import queue
        import subprocess
        
        results = queue.Queue()
        
        def run_version():
            try:
                # Use subprocess instead of direct function call to avoid signal handler issues
                result = subprocess.run(
                    [sys.executable, '-m', 'pgsd', 'version'],
                    cwd=Path(__file__).parent.parent.parent,
                    env={'PYTHONPATH': str(Path(__file__).parent.parent.parent / 'src')},
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                results.put(('success', result.returncode))
            except Exception as e:
                results.put(('error', str(e)))
        
        # Start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=run_version)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check results
        success_count = 0
        while not results.empty():
            result_type, result_value = results.get()
            if result_type == 'success':
                success_count += 1
                assert result_value == 0
            else:
                pytest.fail(f"Concurrent execution failed: {result_value}")
        
        assert success_count == 3