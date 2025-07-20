"""Simple tests for environment variable substitution."""

import pytest
import os
from unittest.mock import Mock, patch, mock_open

from pgsd.config.substitutor import EnvironmentSubstitutor
from pgsd.exceptions.config import InvalidConfigurationError


class TestEnvironmentSubstitutor:
    """Test cases for EnvironmentSubstitutor class."""

    def test_init_default(self):
        """Test EnvironmentSubstitutor initialization with defaults."""
        with patch.object(EnvironmentSubstitutor, '_load_dotenv'):
            substitutor = EnvironmentSubstitutor()
            assert substitutor.logger is not None

    def test_init_no_dotenv(self):
        """Test EnvironmentSubstitutor initialization without dotenv loading."""
        with patch.object(EnvironmentSubstitutor, '_load_dotenv') as mock_load:
            substitutor = EnvironmentSubstitutor(load_dotenv=False)
            mock_load.assert_not_called()

    def test_substitute_simple_variable(self):
        """Test substituting simple environment variable."""
        config = {
            'database': {
                'host': '${DB_HOST}',
                'port': 5432
            }
        }
        
        env_vars = {'DB_HOST': 'localhost'}
        
        with patch.dict(os.environ, env_vars, clear=False):
            substitutor = EnvironmentSubstitutor(load_dotenv=False)
            result = substitutor.substitute(config)
        
        expected = {
            'database': {
                'host': 'localhost',
                'port': 5432
            }
        }
        assert result == expected

    def test_substitute_with_default_value(self):
        """Test substituting variable with default value."""
        config = {
            'database': {
                'host': '${DB_HOST:localhost}',
                'port': '${DB_PORT:5432}'
            }
        }
        
        # DB_HOST is not set, should use default
        # DB_PORT is not set, should use default
        with patch.dict(os.environ, {}, clear=True):
            substitutor = EnvironmentSubstitutor(load_dotenv=False)
            result = substitutor.substitute(config)
        
        expected = {
            'database': {
                'host': 'localhost',
                'port': '5432'
            }
        }
        assert result == expected

    def test_substitute_env_overrides_default(self):
        """Test environment variable overrides default value."""
        config = {
            'database': {
                'host': '${DB_HOST:localhost}',
                'port': '${DB_PORT:5432}'
            }
        }
        
        env_vars = {
            'DB_HOST': 'production.example.com',
            'DB_PORT': '5433'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            substitutor = EnvironmentSubstitutor(load_dotenv=False)
            result = substitutor.substitute(config)
        
        expected = {
            'database': {
                'host': 'production.example.com',
                'port': '5433'
            }
        }
        assert result == expected

    def test_substitute_missing_required_variable(self):
        """Test substituting missing required environment variable."""
        config = {
            'database': {
                'password': '${DB_PASSWORD}'  # No default value
            }
        }
        
        with patch.dict(os.environ, {}, clear=True):
            substitutor = EnvironmentSubstitutor(load_dotenv=False)
            
            with pytest.raises(InvalidConfigurationError, match="Invalid configuration value"):
                substitutor.substitute(config)

    def test_substitute_nested_structure(self):
        """Test substituting in nested configuration structure."""
        config = {
            'databases': {
                'source': {
                    'host': '${SOURCE_HOST}',
                    'port': '${SOURCE_PORT:5432}',
                    'database': '${SOURCE_DB}'
                },
                'target': {
                    'host': '${TARGET_HOST}',
                    'port': '${TARGET_PORT:5432}',
                    'database': '${TARGET_DB}'
                }
            },
            'output': {
                'file': '${OUTPUT_FILE:report.html}'
            }
        }
        
        env_vars = {
            'SOURCE_HOST': 'source.example.com',
            'SOURCE_DB': 'source_db',
            'TARGET_HOST': 'target.example.com',
            'TARGET_DB': 'target_db',
            'OUTPUT_FILE': 'custom_report.html'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            substitutor = EnvironmentSubstitutor(load_dotenv=False)
            result = substitutor.substitute(config)
        
        expected = {
            'databases': {
                'source': {
                    'host': 'source.example.com',
                    'port': '5432',
                    'database': 'source_db'
                },
                'target': {
                    'host': 'target.example.com',
                    'port': '5432',
                    'database': 'target_db'
                }
            },
            'output': {
                'file': 'custom_report.html'
            }
        }
        assert result == expected

    def test_substitute_list_values(self):
        """Test substituting environment variables in list values."""
        config = {
            'servers': [
                '${SERVER1}',
                '${SERVER2:default.example.com}',
                'static.example.com'
            ],
            'ports': [
                '${PORT1:8080}',
                '${PORT2}',
                9000
            ]
        }
        
        env_vars = {
            'SERVER1': 'dynamic.example.com',
            'PORT2': '8081'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            substitutor = EnvironmentSubstitutor(load_dotenv=False)
            result = substitutor.substitute(config)
        
        expected = {
            'servers': [
                'dynamic.example.com',
                'default.example.com',
                'static.example.com'
            ],
            'ports': [
                '8080',
                '8081',
                9000
            ]
        }
        assert result == expected

    def test_substitute_mixed_content(self):
        """Test substituting variables in mixed content."""
        config = {
            'connection_string': 'postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST:localhost}:${DB_PORT:5432}/${DB_NAME}',
            'log_file': '/var/log/${APP_NAME:pgsd}/app.log'
        }
        
        env_vars = {
            'DB_USER': 'postgres',
            'DB_PASSWORD': 'secret',
            'DB_HOST': 'prod.example.com',
            'DB_NAME': 'production',
            'APP_NAME': 'pgsd-prod'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            substitutor = EnvironmentSubstitutor(load_dotenv=False)
            result = substitutor.substitute(config)
        
        expected = {
            'connection_string': 'postgresql://postgres:secret@prod.example.com:5432/production',
            'log_file': '/var/log/pgsd-prod/app.log'
        }
        assert result == expected

    def test_substitute_non_string_values(self):
        """Test that non-string values are preserved."""
        config = {
            'database': {
                'port': 5432,
                'ssl': True,
                'timeout': 30.5,
                'options': None
            },
            'settings': {
                'debug': False,
                'retries': 3
            }
        }
        
        substitutor = EnvironmentSubstitutor(load_dotenv=False)
        result = substitutor.substitute(config)
        
        # Non-string values should be unchanged
        assert result == config

    def test_substitute_empty_default(self):
        """Test substituting with empty default value."""
        config = {
            'optional_setting': '${OPTIONAL_VAR:}'
        }
        
        with patch.dict(os.environ, {}, clear=True):
            substitutor = EnvironmentSubstitutor(load_dotenv=False)
            result = substitutor.substitute(config)
        
        expected = {
            'optional_setting': ''
        }
        assert result == expected

    def test_substitute_complex_default(self):
        """Test substituting with complex default value."""
        config = {
            'connection_string': '${CONNECTION_STRING:postgresql://user:pass@localhost:5432/db}',
            'config_path': '${CONFIG_PATH:/etc/pgsd/config.yaml}'
        }
        
        with patch.dict(os.environ, {}, clear=True):
            substitutor = EnvironmentSubstitutor(load_dotenv=False)
            result = substitutor.substitute(config)
        
        expected = {
            'connection_string': 'postgresql://user:pass@localhost:5432/db',
            'config_path': '/etc/pgsd/config.yaml'
        }
        assert result == expected

    def test_substitute_special_characters_in_default(self):
        """Test substituting with special characters in default value."""
        config = {
            'special_chars': '${SPECIAL:default with spaces and $pecial ch@rs!}',
            'colon_in_default': '${COLON_VAR:http://example.com:8080/path}'
        }
        
        with patch.dict(os.environ, {}, clear=True):
            substitutor = EnvironmentSubstitutor(load_dotenv=False)
            result = substitutor.substitute(config)
        
        expected = {
            'special_chars': 'default with spaces and $pecial ch@rs!',
            'colon_in_default': 'http://example.com:8080/path'
        }
        assert result == expected

    def test_substitute_multiple_vars_in_string(self):
        """Test substituting multiple variables in single string."""
        config = {
            'combined': '${PART1}_${PART2:default}_${PART3}',
            'url': 'https://${HOST}:${PORT:443}/${PATH:api/v1}'
        }
        
        env_vars = {
            'PART1': 'prefix',
            'PART3': 'suffix',
            'HOST': 'api.example.com',
            'PATH': 'custom/path'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            substitutor = EnvironmentSubstitutor(load_dotenv=False)
            result = substitutor.substitute(config)
        
        expected = {
            'combined': 'prefix_default_suffix',
            'url': 'https://api.example.com:443/custom/path'
        }
        assert result == expected

    @patch('pathlib.Path.exists')
    @patch('builtins.open')
    def test_load_dotenv_file_exists(self, mock_open_func, mock_exists):
        """Test loading .env file when it exists."""
        mock_exists.return_value = True
        mock_open_func.return_value.__enter__.return_value.readlines.return_value = [
            'DB_HOST=localhost\n',
            'DB_PORT=5432\n',
            '# Comment line\n',
            'DB_USER=postgres\n'
        ]
        
        with patch.dict(os.environ, {}, clear=True):
            substitutor = EnvironmentSubstitutor(load_dotenv=True)
        
        # Test that initialization succeeded without error
        assert substitutor is not None

    @patch('pathlib.Path.exists')
    def test_load_dotenv_file_not_exists(self, mock_exists):
        """Test loading .env file when it doesn't exist."""
        mock_exists.return_value = False
        
        # Should not raise error when .env file doesn't exist
        substitutor = EnvironmentSubstitutor(load_dotenv=True)
        assert substitutor is not None

    def test_substitute_preserves_original_config(self):
        """Test that original configuration is not modified."""
        original_config = {
            'database': {
                'host': '${DB_HOST:localhost}',
                'port': 5432
            }
        }
        
        config_copy = original_config.copy()
        
        substitutor = EnvironmentSubstitutor(load_dotenv=False)
        result = substitutor.substitute(config_copy)
        
        # Original config should be unchanged
        assert original_config == {
            'database': {
                'host': '${DB_HOST:localhost}',
                'port': 5432
            }
        }
        
        # Result should have substituted values
        assert result['database']['host'] == 'localhost'