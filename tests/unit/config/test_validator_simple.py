"""Simple tests for configuration validation."""

import pytest
from unittest.mock import Mock, patch

from pgsd.config.validator import ConfigurationValidator
from pgsd.config.schema import PGSDConfiguration, OutputFormat, LogLevel
from pgsd.exceptions.config import InvalidConfigurationError


class TestConfigurationValidator:
    """Test cases for ConfigurationValidator class."""

    def test_init(self):
        """Test ConfigurationValidator initialization."""
        validator = ConfigurationValidator()
        assert validator.logger is not None

    def test_validate_minimal_config(self):
        """Test validating minimal configuration."""
        config_dict = {
            'source_db': {
                'host': 'source.example.com',
                'database': 'source_db',
                'username': 'user'
            },
            'target_db': {
                'host': 'target.example.com',
                'database': 'target_db',
                'username': 'user'
            }
        }
        
        validator = ConfigurationValidator()
        result = validator.validate(config_dict)
        
        assert isinstance(result, PGSDConfiguration)
        assert result.source_db.host == 'source.example.com'
        assert result.target_db.host == 'target.example.com'

    def test_validate_complete_config(self):
        """Test validating complete configuration."""
        config_dict = {
            'source_db': {
                'host': 'source.example.com',
                'port': 5432,
                'database': 'source_db',
                'username': 'source_user',
                'password': 'source_pass',
                'schema': 'public'
            },
            'target_db': {
                'host': 'target.example.com',
                'port': 5433,
                'database': 'target_db',
                'username': 'target_user',
                'password': 'target_pass',
                'schema': 'public'
            },
            'output': {
                'format': 'html',
                'file': 'report.html',
                'directory': '/tmp/reports'
            },
            'system': {
                'log_level': 'info',
                'timezone': 'UTC'
            }
        }
        
        validator = ConfigurationValidator()
        result = validator.validate(config_dict)
        
        assert isinstance(result, PGSDConfiguration)
        assert result.source_db.port == 5432
        assert result.target_db.port == 5433
        assert result.output.format == OutputFormat.HTML
        assert result.system.log_level == LogLevel.INFO

    def test_validate_with_enum_strings(self):
        """Test validating configuration with enum values as strings."""
        config_dict = {
            'source_db': {
                'host': 'source.example.com',
                'database': 'source_db',
                'username': 'user',
                'ssl_mode': 'require'
            },
            'target_db': {
                'host': 'target.example.com',
                'database': 'target_db',
                'username': 'user',
                'ssl_mode': 'prefer'
            },
            'output': {
                'format': 'json'
            },
            'system': {
                'log_level': 'debug'
            }
        }
        
        validator = ConfigurationValidator()
        result = validator.validate(config_dict)
        
        assert isinstance(result, PGSDConfiguration)
        assert result.output.format == OutputFormat.JSON
        assert result.system.log_level == LogLevel.DEBUG

    def test_validate_missing_source_db(self):
        """Test validation with missing source database configuration."""
        config_dict = {
            'target_db': {
                'host': 'target.example.com',
                'database': 'target_db',
                'username': 'user'
            }
        }
        
        validator = ConfigurationValidator()
        
        with pytest.raises(InvalidConfigurationError, match="Source database configuration is required"):
            validator.validate(config_dict)

    def test_validate_missing_target_db(self):
        """Test validation with missing target database configuration."""
        config_dict = {
            'source_db': {
                'host': 'source.example.com',
                'database': 'source_db',
                'username': 'user'
            }
        }
        
        validator = ConfigurationValidator()
        
        with pytest.raises(InvalidConfigurationError, match="Target database configuration is required"):
            validator.validate(config_dict)

    def test_validate_invalid_enum_value(self):
        """Test validation with invalid enum value."""
        config_dict = {
            'source_db': {
                'host': 'source.example.com',
                'database': 'source_db',
                'username': 'user'
            },
            'target_db': {
                'host': 'target.example.com',
                'database': 'target_db',
                'username': 'user'
            },
            'output': {
                'format': 'invalid_format'
            }
        }
        
        validator = ConfigurationValidator()
        
        with pytest.raises(InvalidConfigurationError):
            validator.validate(config_dict)

    def test_validate_empty_config(self):
        """Test validation with empty configuration."""
        config_dict = {}
        
        validator = ConfigurationValidator()
        
        with pytest.raises(InvalidConfigurationError):
            validator.validate(config_dict)

    def test_validate_config_with_extra_config_key(self):
        """Test validation removes unexpected 'config' key."""
        config_dict = {
            'source_db': {
                'host': 'source.example.com',
                'database': 'source_db',
                'username': 'user'
            },
            'target_db': {
                'host': 'target.example.com',
                'database': 'target_db',
                'username': 'user'
            },
            'config': {
                'extra': 'data'
            }
        }
        
        validator = ConfigurationValidator()
        result = validator.validate(config_dict)
        
        assert isinstance(result, PGSDConfiguration)
        # The 'config' key should have been removed

    def test_normalize_config_output_format(self):
        """Test config normalization for output format."""
        config_dict = {
            'source_db': {
                'host': 'source.example.com',
                'database': 'source_db',
                'username': 'user'
            },
            'target_db': {
                'host': 'target.example.com',
                'database': 'target_db',
                'username': 'user'
            },
            'output': {
                'format': 'HTML'  # Mixed case
            }
        }
        
        validator = ConfigurationValidator()
        result = validator.validate(config_dict)
        
        assert result.output.format == OutputFormat.HTML

    def test_normalize_config_log_level(self):
        """Test config normalization for log level."""
        config_dict = {
            'source_db': {
                'host': 'source.example.com',
                'database': 'source_db',
                'username': 'user'
            },
            'target_db': {
                'host': 'target.example.com',
                'database': 'target_db',
                'username': 'user'
            },
            'system': {
                'log_level': 'WARNING'  # Upper case
            }
        }
        
        validator = ConfigurationValidator()
        result = validator.validate(config_dict)
        
        assert result.system.log_level == LogLevel.WARNING

    def test_validate_additional_validation_success(self):
        """Test additional validation passes."""
        config_dict = {
            'source_db': {
                'host': 'source.example.com',
                'database': 'source_db',
                'username': 'user'
            },
            'target_db': {
                'host': 'target.example.com',
                'database': 'target_db',
                'username': 'user'
            }
        }
        
        validator = ConfigurationValidator()
        
        with patch.object(validator, '_additional_validation') as mock_validation:
            mock_validation.return_value = None  # No errors
            
            result = validator.validate(config_dict)
            
            assert isinstance(result, PGSDConfiguration)
            mock_validation.assert_called_once()

    def test_validate_additional_validation_failure(self):
        """Test additional validation fails."""
        config_dict = {
            'source_db': {
                'host': 'source.example.com',
                'database': 'source_db',
                'username': 'user'
            },
            'target_db': {
                'host': 'target.example.com',
                'database': 'target_db',
                'username': 'user'
            }
        }
        
        validator = ConfigurationValidator()
        
        with patch.object(validator, '_additional_validation') as mock_validation:
            mock_validation.side_effect = InvalidConfigurationError("Additional validation failed")
            
            with pytest.raises(InvalidConfigurationError, match="Additional validation failed"):
                validator.validate(config_dict)

    def test_validate_exception_handling(self):
        """Test exception handling during validation."""
        config_dict = {
            'source_db': {
                'host': 'source.example.com',
                'database': 'source_db',
                'username': 'user'
            },
            'target_db': {
                'host': 'target.example.com',
                'database': 'target_db',
                'username': 'user'
            }
        }
        
        validator = ConfigurationValidator()
        
        # Mock PGSDConfiguration to raise an exception
        with patch('pgsd.config.validator.PGSDConfiguration') as mock_config:
            mock_config.side_effect = ValueError("Invalid configuration")
            
            with pytest.raises(InvalidConfigurationError, match="Configuration validation failed"):
                validator.validate(config_dict)

    def test_normalize_config_nested_structure(self):
        """Test normalization of nested configuration structure."""
        config_dict = {
            'source_db': {
                'host': 'source.example.com',
                'database': 'source_db',
                'username': 'user'
            },
            'target_db': {
                'host': 'target.example.com',
                'database': 'target_db',
                'username': 'user'
            },
            'comparison': {
                'include_data': True,
                'ignore_whitespace': False
            }
        }
        
        validator = ConfigurationValidator()
        result = validator.validate(config_dict)
        
        assert isinstance(result, PGSDConfiguration)
        assert hasattr(result, 'comparison')

    def test_validate_with_boolean_values(self):
        """Test validation with boolean configuration values."""
        config_dict = {
            'source_db': {
                'host': 'source.example.com',
                'database': 'source_db',
                'username': 'user'
            },
            'target_db': {
                'host': 'target.example.com',
                'database': 'target_db',
                'username': 'user'
            },
            'system': {
                'verbose': True,
                'debug': False
            }
        }
        
        validator = ConfigurationValidator()
        result = validator.validate(config_dict)
        
        assert isinstance(result, PGSDConfiguration)

    def test_validate_with_none_values(self):
        """Test validation handles None values appropriately."""
        config_dict = {
            'source_db': {
                'host': 'source.example.com',
                'database': 'source_db',
                'username': 'user',
                'password': None
            },
            'target_db': {
                'host': 'target.example.com',
                'database': 'target_db',
                'username': 'user',
                'password': None
            }
        }
        
        validator = ConfigurationValidator()
        result = validator.validate(config_dict)
        
        assert isinstance(result, PGSDConfiguration)
        assert result.source_db.password is None
        assert result.target_db.password is None