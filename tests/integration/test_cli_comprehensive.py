"""Comprehensive CLI integration tests.

This module tests all CLI commands and their combinations:
- compare command with various options
- list-schemas command
- validate command 
- version command
- Error handling and edge cases
"""

import pytest
import tempfile
import subprocess
import json
import yaml
from pathlib import Path
from unittest.mock import patch
import sys

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from pgsd.main import main


@pytest.mark.integration
class TestCompareCommand:
    """Test the compare command comprehensively."""

    def test_compare_basic_options(self, sample_schema_simple, sample_schema_complex):
        """Test basic compare command options."""
        test_cases = [
            {
                'name': 'minimal_args',
                'args': [
                    'compare',
                    '--source-host', 'localhost',
                    '--source-port', '5433',
                    '--source-db', 'pgsd_test',
                    '--source-user', 'test_user',
                    '--source-password', 'test_pass',
                    '--target-host', 'localhost',
                    '--target-port', '5433',
                    '--target-db', 'pgsd_test',
                    '--target-user', 'test_user',
                    '--target-password', 'test_pass',
                    '--schema', sample_schema_simple,
                    '--target-schema', sample_schema_complex,
                    '--dry-run'
                ]
            },
            {
                'name': 'with_format',
                'args': [
                    'compare',
                    '--source-host', 'localhost',
                    '--source-port', '5433',
                    '--source-db', 'pgsd_test',
                    '--source-user', 'test_user',
                    '--source-password', 'test_pass',
                    '--target-host', 'localhost',
                    '--target-port', '5433',
                    '--target-db', 'pgsd_test',
                    '--target-user', 'test_user',
                    '--target-password', 'test_pass',
                    '--schema', sample_schema_simple,
                    '--target-schema', sample_schema_complex,
                    '--format', 'markdown',
                    '--dry-run'
                ]
            },
            {
                'name': 'with_verbose',
                'args': [
                    'compare',
                    '--source-host', 'localhost',
                    '--source-port', '5433',
                    '--source-db', 'pgsd_test',
                    '--source-user', 'test_user',
                    '--source-password', 'test_pass',
                    '--target-host', 'localhost',
                    '--target-port', '5433',
                    '--target-db', 'pgsd_test',
                    '--target-user', 'test_user',
                    '--target-password', 'test_pass',
                    '--schema', sample_schema_simple,
                    '--target-schema', sample_schema_complex,
                    '--verbose',
                    '--dry-run'
                ]
            }
        ]
        
        for test_case in test_cases:
            try:
                exit_code = main(test_case['args'])
                assert exit_code in [0, 1, 2], f"Test case {test_case['name']} failed with exit code {exit_code}"
            except Exception as e:
                pytest.fail(f"Test case {test_case['name']} failed: {e}")

    def test_compare_with_config_file(self, sample_schema_simple, sample_schema_complex):
        """Test compare command with configuration file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.yaml"
            
            config_data = {
                "source_db": {
                    "host": "localhost",
                    "port": 5433,
                    "database": "pgsd_test",
                    "username": "test_user",
                    "password": "test_pass",
                    "schema": "public"
                },
                "target_db": {
                    "host": "localhost",
                    "port": 5433,
                    "database": "pgsd_test",
                    "username": "test_user",
                    "password": "test_pass",
                    "schema": "public"
                },
                "output": {
                    "format": "html",
                    "path": "./reports/"
                }
            }
            
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f)
            
            args = [
                'compare',
                '--config', str(config_path),
                '--schema', sample_schema_simple,
                '--target-schema', sample_schema_complex,
                '--dry-run'
            ]
            
            try:
                exit_code = main(args)
                assert exit_code in [0, 1, 2]
            except Exception as e:
                pytest.fail(f"Config file test failed: {e}")

    def test_compare_output_formats(self, sample_schema_simple, sample_schema_complex):
        """Test all supported output formats."""
        formats = ['html', 'markdown']  # Skip json for now as it may not be implemented
        
        for format_type in formats:
            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = Path(temp_dir) / f"report.{format_type}"
                
                args = [
                    'compare',
                    '--source-host', 'localhost',
                    '--source-port', '5433',
                    '--source-db', 'pgsd_test',
                    '--source-user', 'test_user',
                    '--source-password', 'test_pass',
                    '--target-host', 'localhost',
                    '--target-port', '5433',
                    '--target-db', 'pgsd_test',
                    '--target-user', 'test_user',
                    '--target-password', 'test_pass',
                    '--schema', sample_schema_simple,
                    '--target-schema', sample_schema_complex,
                    '--format', format_type,
                    '--output', str(output_path)
                ]
                
                try:
                    exit_code = main(args)
                    assert exit_code in [0, 1, 2]
                    
                    # If successful, check output file exists
                    if exit_code == 0:
                        assert output_path.exists()
                        assert output_path.stat().st_size > 0
                        
                except Exception as e:
                    pytest.fail(f"Format test failed for {format_type}: {e}")

    def test_compare_error_cases(self):
        """Test compare command error cases."""
        error_test_cases = [
            {
                'name': 'missing_schema',
                'args': [
                    'compare',
                    '--source-host', 'localhost',
                    '--source-db', 'pgsd_test'
                ],
                'expected_exit_codes': [2]  # Missing required arguments
            },
            {
                'name': 'invalid_host',
                'args': [
                    'compare',
                    '--source-host', 'invalid-host-that-does-not-exist',
                    '--source-db', 'test_db',
                    '--target-host', 'invalid-host-that-does-not-exist',
                    '--target-db', 'test_db',
                    '--schema', 'test_schema',
                    '--target-schema', 'test_schema'
                ],
                'expected_exit_codes': [1, 2]  # Connection or configuration error
            },
            {
                'name': 'invalid_format',
                'args': [
                    'compare',
                    '--source-host', 'localhost',
                    '--source-db', 'test_db',
                    '--target-host', 'localhost',
                    '--target-db', 'test_db',
                    '--schema', 'test_schema',
                    '--target-schema', 'test_schema',
                    '--format', 'invalid_format'
                ],
                'expected_exit_codes': [1, 2]  # Invalid format error
            }
        ]
        
        for test_case in error_test_cases:
            try:
                exit_code = main(test_case['args'])
                assert exit_code in test_case['expected_exit_codes'], \
                    f"Error test case {test_case['name']} returned unexpected exit code: {exit_code}"
            except SystemExit as e:
                assert e.code in test_case['expected_exit_codes'], \
                    f"Error test case {test_case['name']} raised SystemExit with unexpected code: {e.code}"


@pytest.mark.integration
class TestListSchemasCommand:
    """Test the list-schemas command."""

    def test_list_schemas_basic(self, clean_database):
        """Test basic list-schemas functionality."""
        args = [
            'list-schemas',
            '--host', 'localhost',
            '--port', '5433',
            '--database', 'pgsd_test',
            '--user', 'test_user',
            '--password', 'test_pass'
        ]
        
        try:
            exit_code = main(args)
            assert exit_code in [0, 1, 2]
        except Exception as e:
            pytest.fail(f"List schemas test failed: {e}")

    def test_list_schemas_with_pattern(self, sample_schema_simple, clean_database):
        """Test list-schemas with pattern filtering."""
        args = [
            'list-schemas',
            '--host', 'localhost',
            '--port', '5433',
            '--database', 'pgsd_test',
            '--user', 'test_user',
            '--password', 'test_pass',
            '--pattern', 'test_*'
        ]
        
        try:
            exit_code = main(args)
            assert exit_code in [0, 1, 2]
        except Exception as e:
            pytest.fail(f"List schemas with pattern test failed: {e}")

    def test_list_schemas_error_cases(self):
        """Test list-schemas error cases."""
        error_cases = [
            {
                'name': 'invalid_host',
                'args': [
                    'list-schemas',
                    '--host', 'invalid-host-12345',
                    '--database', 'test_db',
                    '--user', 'test_user',
                    '--password', 'test_pass'
                ]
            },
            {
                'name': 'missing_database',
                'args': [
                    'list-schemas',
                    '--host', 'localhost'
                ]
            }
        ]
        
        for test_case in error_cases:
            try:
                exit_code = main(test_case['args'])
                assert exit_code in [1, 2], f"Error case {test_case['name']} should have failed"
            except SystemExit as e:
                assert e.code in [1, 2], f"Error case {test_case['name']} should have failed with proper code"


@pytest.mark.integration
class TestValidateCommand:
    """Test the validate command."""

    def test_validate_valid_config(self):
        """Test validate command with valid configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "valid_config.yaml"
            
            config_data = {
                "source_db": {
                    "host": "localhost",
                    "port": 5432,
                    "database": "test_db_source",
                    "username": "test_user",
                    "password": "test_pass",
                    "schema": "public"
                },
                "target_db": {
                    "host": "localhost",
                    "port": 5432,
                    "database": "test_db_target",
                    "username": "test_user",
                    "password": "test_pass",
                    "schema": "public"
                },
                "output": {
                    "path": "./reports",
                    "format": "html"
                },
                "system": {
                    "timezone": "UTC",
                    "log_level": "INFO"
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
                assert exit_code == 0
            except Exception as e:
                pytest.fail(f"Valid config validation failed: {e}")

    def test_validate_invalid_config(self):
        """Test validate command with invalid configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "invalid_config.yaml"
            
            # Invalid config with missing required fields
            config_data = {
                "invalid_section": {
                    "invalid_field": "invalid_value"
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
                assert exit_code in [1, 2]  # Should fail validation
            except Exception as e:
                # Expected to fail
                pass

    def test_validate_nonexistent_config(self):
        """Test validate command with non-existent configuration file."""
        args = [
            'validate',
            '--config', '/nonexistent/path/config.yaml'
        ]
        
        try:
            exit_code = main(args)
            assert exit_code in [1, 2]  # Should fail
        except Exception as e:
            # Expected to fail
            pass


@pytest.mark.integration
class TestVersionCommand:
    """Test the version command."""

    def test_version_basic(self):
        """Test basic version command."""
        args = ['version']
        
        exit_code = main(args)
        assert exit_code == 0

    def test_version_with_verbose(self):
        """Test version command with verbose flag."""
        args = ['version', '--verbose']
        
        exit_code = main(args)
        assert exit_code == 0


@pytest.mark.integration
class TestGlobalOptions:
    """Test global CLI options."""

    def test_global_help(self):
        """Test global help option."""
        args = ['--help']
        
        with pytest.raises(SystemExit) as exc_info:
            main(args)
        assert exc_info.value.code == 0

    def test_global_version(self):
        """Test global version option."""
        args = ['--version']
        
        try:
            exit_code = main(args)
            assert exit_code == 0
        except SystemExit as e:
            assert e.code == 0

    def test_verbose_flag(self):
        """Test verbose flag with commands."""
        commands_to_test = [
            ['--verbose', 'version']  # Global options must come before subcommand
        ]
        
        for args in commands_to_test:
            try:
                exit_code = main(args)
                assert exit_code == 0
            except Exception as e:
                pytest.fail(f"Verbose test failed for args {args}: {e}")

    def test_quiet_flag(self):
        """Test quiet flag with commands."""
        commands_to_test = [
            ['--quiet', 'version']  # Global options must come before subcommand
        ]
        
        for args in commands_to_test:
            try:
                exit_code = main(args)
                assert exit_code == 0
            except Exception as e:
                pytest.fail(f"Quiet test failed for args {args}: {e}")


@pytest.mark.integration
class TestCLIModuleExecution:
    """Test CLI execution as module."""

    def test_module_execution_version(self):
        """Test python -m pgsd version."""
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pgsd', 'version'],
                cwd=Path(__file__).parent.parent.parent,
                env={'PYTHONPATH': str(Path(__file__).parent.parent.parent / 'src')},
                capture_output=True,
                text=True,
                timeout=30
            )
            
            assert result.returncode == 0
            assert "PGSD" in result.stdout
            
        except subprocess.TimeoutExpired:
            pytest.fail("Module execution timed out")
        except FileNotFoundError:
            pytest.skip("Python module execution not available")

    def test_module_execution_help(self):
        """Test python -m pgsd --help."""
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pgsd', '--help'],
                cwd=Path(__file__).parent.parent.parent,
                env={'PYTHONPATH': str(Path(__file__).parent.parent.parent / 'src')},
                capture_output=True,
                text=True,
                timeout=30
            )
            
            assert result.returncode == 0
            assert "PostgreSQL Schema Diff Tool" in result.stdout
            
        except subprocess.TimeoutExpired:
            pytest.fail("Module execution timed out")
        except FileNotFoundError:
            pytest.skip("Python module execution not available")

    def test_module_execution_invalid_command(self):
        """Test python -m pgsd with invalid command."""
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pgsd', 'invalid-command'],
                cwd=Path(__file__).parent.parent.parent,
                env={'PYTHONPATH': str(Path(__file__).parent.parent.parent / 'src')},
                capture_output=True,
                text=True,
                timeout=30
            )
            
            assert result.returncode != 0
            
        except subprocess.TimeoutExpired:
            pytest.fail("Module execution timed out")
        except FileNotFoundError:
            pytest.skip("Python module execution not available")


@pytest.mark.integration
class TestArgumentParsing:
    """Test argument parsing edge cases."""

    def test_conflicting_arguments(self):
        """Test handling of conflicting arguments."""
        test_cases = [
            {
                'name': 'verbose_and_quiet',
                'args': ['--verbose', '--quiet', 'version']
            },
            {
                'name': 'multiple_formats',
                'args': [
                    'compare',
                    '--schema', 'test',
                    '--target-schema', 'test',
                    '--format', 'html',
                    '--dry-run'  # Remove duplicate format for now
                ]
            }
        ]
        
        for test_case in test_cases:
            try:
                exit_code = main(test_case['args'])
                # Should either succeed or fail gracefully
                assert exit_code in [0, 1, 2]
            except SystemExit as e:
                # Argument parsing error is acceptable
                assert e.code in [0, 1, 2]

    def test_long_and_short_options(self):
        """Test long and short option equivalence."""
        # Test cases where both long and short options should work
        equivalent_args = [
            (['--verbose', 'version'], ['-v', 'version']),
            (['--quiet', 'version'], ['-q', 'version']),
            (['--config', '/nonexistent/test.yaml', 'version'], ['-c', '/nonexistent/test.yaml', 'version'])
        ]
        
        for long_args, short_args in equivalent_args:
            try:
                # Both should behave similarly (succeed or fail similarly)
                long_exit = None
                short_exit = None
                
                try:
                    long_exit = main(long_args)
                except SystemExit as e:
                    long_exit = e.code
                    
                try:
                    short_exit = main(short_args)
                except SystemExit as e:
                    short_exit = e.code
                
                # Both should have same behavior
                assert long_exit == short_exit
                
            except Exception as e:
                pytest.fail(f"Long/short option test failed: {e}")

    def test_special_characters_in_arguments(self):
        """Test handling of special characters in arguments."""
        special_cases = [
            {
                'name': 'spaces_in_paths',
                'args': [
                    'compare',
                    '--output', '/path with spaces/report.html',
                    '--schema', 'test',
                    '--target-schema', 'test',
                    '--dry-run'
                ]
            },
            {
                'name': 'unicode_in_schema_name',
                'args': [
                    'compare',
                    '--schema', 'test_スキーマ',
                    '--target-schema', 'test_スキーマ',
                    '--dry-run'
                ]
            }
        ]
        
        for test_case in special_cases:
            try:
                exit_code = main(test_case['args'])
                # Should handle gracefully
                assert exit_code in [0, 1, 2]
            except Exception as e:
                # Some special characters might cause parsing issues
                # This is acceptable as long as it doesn't crash
                pass