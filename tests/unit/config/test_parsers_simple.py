"""Simple tests for configuration parsers."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from pgsd.config.parsers import YAMLParser, EnvironmentParser, CLIParser
from pgsd.exceptions.config import ConfigurationError


class TestYAMLParser:
    """Test cases for YAMLParser class."""

    def test_init_success(self):
        """Test successful YAML parser initialization."""
        with patch('pgsd.config.parsers.yaml', Mock()):
            parser = YAMLParser()
            assert parser.logger is not None

    def test_init_no_yaml(self):
        """Test YAML parser initialization without PyYAML."""
        with patch('pgsd.config.parsers.yaml', None):
            with pytest.raises(ConfigurationError, match="PyYAML is required"):
                YAMLParser()

    def test_parse_simple_yaml(self):
        """Test parsing simple YAML file."""
        yaml_content = """
        database:
          host: localhost
          port: 5432
        """
        
        with patch('pgsd.config.parsers.yaml') as mock_yaml:
            mock_yaml.safe_load.return_value = {
                'database': {
                    'host': 'localhost',
                    'port': 5432
                }
            }
            
            parser = YAMLParser()
            
            with patch('builtins.open', mock_open(read_data=yaml_content)):
                result = parser.parse(Path("/fake/path.yaml"))
            
            expected = {
                'database': {
                    'host': 'localhost',
                    'port': 5432
                }
            }
            assert result == expected

    def test_parse_empty_yaml(self):
        """Test parsing empty YAML file."""
        with patch('pgsd.config.parsers.yaml') as mock_yaml:
            mock_yaml.safe_load.return_value = None
            
            parser = YAMLParser()
            
            with patch('builtins.open', mock_open(read_data="")):
                result = parser.parse(Path("/fake/empty.yaml"))
            
            assert result == {}

    def test_parse_yaml_error(self):
        """Test parsing invalid YAML file."""
        with patch('pgsd.config.parsers.yaml') as mock_yaml:
            yaml_error = type('YAMLError', (Exception,), {})
            mock_yaml.YAMLError = yaml_error
            mock_yaml.safe_load.side_effect = yaml_error("Invalid YAML")
            
            parser = YAMLParser()
            
            with patch('builtins.open', mock_open(read_data="invalid: yaml: content")):
                with pytest.raises(ConfigurationError, match="Invalid YAML"):
                    parser.parse(Path("/fake/invalid.yaml"))

    def test_parse_file_not_found(self):
        """Test parsing non-existent file."""
        with patch('pgsd.config.parsers.yaml', Mock()):
            parser = YAMLParser()
            
            with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
                with pytest.raises(ConfigurationError, match="Failed to read"):
                    parser.parse(Path("/fake/nonexistent.yaml"))

    def test_parse_permission_error(self):
        """Test parsing file with permission error."""
        with patch('pgsd.config.parsers.yaml', Mock()):
            parser = YAMLParser()
            
            with patch('builtins.open', side_effect=PermissionError("Permission denied")):
                with pytest.raises(ConfigurationError, match="Failed to read"):
                    parser.parse(Path("/fake/noperm.yaml"))

    def test_parse_complex_yaml(self):
        """Test parsing complex YAML structure."""
        complex_data = {
            'databases': {
                'source': {
                    'host': 'source.example.com',
                    'port': 5432,
                    'ssl': True
                },
                'target': {
                    'host': 'target.example.com',
                    'port': 5433,
                    'ssl': False
                }
            },
            'output': {
                'format': 'html',
                'file': 'report.html'
            },
            'options': ['verbose', 'detailed']
        }
        
        with patch('pgsd.config.parsers.yaml') as mock_yaml:
            mock_yaml.safe_load.return_value = complex_data
            
            parser = YAMLParser()
            
            with patch('builtins.open', mock_open()):
                result = parser.parse(Path("/fake/complex.yaml"))
            
            assert result == complex_data


class TestCLIParser:
    """Test cases for CLIParser class."""

    def test_init(self):
        """Test CLI parser initialization."""
        parser = CLIParser()
        assert parser.logger is not None

    def test_parse_simple_args(self):
        """Test parsing simple CLI arguments."""
        args = Mock()
        args.source_host = 'localhost'
        args.source_port = 5432
        args.target_host = 'target.example.com'
        args.output_format = 'html'
        
        parser = CLIParser()
        result = parser.parse(args)
        
        assert 'source' in result
        assert result['source']['host'] == 'localhost'
        assert result['source']['port'] == 5432
        assert 'target' in result
        assert result['target']['host'] == 'target.example.com'

    def test_parse_empty_args(self):
        """Test parsing empty CLI arguments."""
        args = Mock()
        # Set all attributes to None to simulate no CLI args provided
        for attr in ['source_host', 'source_port', 'target_host', 'output_format']:
            setattr(args, attr, None)
        
        parser = CLIParser()
        result = parser.parse(args)
        
        # Should return empty dict when no relevant args provided
        assert isinstance(result, dict)

    def test_parse_partial_args(self):
        """Test parsing partial CLI arguments."""
        args = Mock()
        args.source_host = 'localhost'
        args.source_port = None
        args.target_host = None
        args.output_format = 'json'
        
        parser = CLIParser()
        result = parser.parse(args)
        
        # Should include provided args and skip None values
        assert result['source']['host'] == 'localhost'
        assert result.get('output', {}).get('format') == 'json'


class TestEnvironmentParser:
    """Test cases for EnvironmentParser class."""

    def test_init(self):
        """Test environment parser initialization."""
        parser = EnvironmentParser()
        assert parser.logger is not None

    def test_parse_basic_env_vars(self):
        """Test parsing basic environment variables."""
        env_vars = {
            'PGSD_SOURCE_HOST': 'source.example.com',
            'PGSD_SOURCE_PORT': '5432',
            'PGSD_TARGET_HOST': 'target.example.com',
            'PGSD_OUTPUT_FORMAT': 'html'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            parser = EnvironmentParser()
            result = parser.parse()
        
        expected = {
            'source': {
                'host': 'source.example.com',
                'port': 5432
            },
            'target': {
                'host': 'target.example.com'
            },
            'output': {
                'format': 'html'
            }
        }
        assert result == expected

    def test_parse_no_env_vars(self):
        """Test parsing with no PGSD environment variables."""
        with patch.dict(os.environ, {}, clear=True):
            parser = EnvironmentParser()
            result = parser.parse()
        
        assert result == {}

    def test_parse_custom_prefix(self):
        """Test parsing with custom prefix."""
        env_vars = {
            'CUSTOM_SOURCE_HOST': 'example.com',
            'CUSTOM_SOURCE_PORT': '5432',
            'OTHER_VAR': 'ignored'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            parser = EnvironmentParser(prefix='CUSTOM_')
            result = parser.parse()
        
        expected = {
            'source': {
                'host': 'example.com',
                'port': 5432
            }
        }
        assert result == expected

    def test_parse_boolean_values(self):
        """Test parsing boolean environment variables."""
        env_vars = {
            'PGSD_SOURCE_SSL': 'true',
            'PGSD_TARGET_SSL': 'false',
            'PGSD_DEBUG': 'yes',
            'PGSD_VERBOSE': 'no'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            parser = EnvironmentParser()
            result = parser.parse()
        
        expected = {
            'source': {'ssl': True},
            'target': {'ssl': False},
            'debug': True,
            'verbose': False
        }
        assert result == expected

    def test_parse_nested_keys(self):
        """Test parsing nested configuration keys."""
        env_vars = {
            'PGSD_DATABASE_SOURCE_HOST': 'src.example.com',
            'PGSD_DATABASE_SOURCE_PORT': '5432',
            'PGSD_DATABASE_TARGET_HOST': 'tgt.example.com',
            'PGSD_OUTPUT_FORMAT': 'json',
            'PGSD_OUTPUT_FILE': 'report.json'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            parser = EnvironmentParser()
            result = parser.parse()
        
        expected = {
            'database': {
                'source': {
                    'host': 'src.example.com',
                    'port': 5432
                },
                'target': {
                    'host': 'tgt.example.com'
                }
            },
            'output': {
                'format': 'json',
                'file': 'report.json'
            }
        }
        assert result == expected

    def test_parse_invalid_integer(self):
        """Test parsing invalid integer values."""
        env_vars = {
            'PGSD_SOURCE_PORT': 'invalid_port'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            parser = EnvironmentParser()
            result = parser.parse()
        
        # Should keep as string if not a valid integer
        expected = {
            'source': {
                'port': 'invalid_port'
            }
        }
        assert result == expected

    def test_parse_edge_case_values(self):
        """Test parsing edge case values."""
        env_vars = {
            'PGSD_EMPTY_VAR': '',
            'PGSD_ZERO_VALUE': '0',
            'PGSD_NEGATIVE_VALUE': '-1',
            'PGSD_FLOAT_VALUE': '3.14'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            parser = EnvironmentParser()
            result = parser.parse()
        
        expected = {
            'empty': {'var': ''},
            'zero': {'value': 0},
            'negative': {'value': -1},
            'float': {'value': 3.14}  # Should be converted to float
        }
        assert result == expected

    def test_parse_complex_nested_structure(self):
        """Test parsing complex nested structure."""
        env_vars = {
            'PGSD_CONFIG_DATABASE_SOURCE_CONNECTION_HOST': 'src.example.com',
            'PGSD_CONFIG_DATABASE_SOURCE_CONNECTION_PORT': '5432',
            'PGSD_CONFIG_DATABASE_TARGET_CONNECTION_HOST': 'tgt.example.com',
            'PGSD_CONFIG_OUTPUT_REPORT_FORMAT': 'html',
            'PGSD_CONFIG_OUTPUT_REPORT_FILE': 'report.html'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            parser = EnvironmentParser()
            result = parser.parse()
        
        expected = {
            'config': {
                'database': {
                    'source': {
                        'connection': {
                            'host': 'src.example.com',
                            'port': 5432
                        }
                    },
                    'target': {
                        'connection': {
                            'host': 'tgt.example.com'
                        }
                    }
                },
                'output': {
                    'report': {
                        'format': 'html',
                        'file': 'report.html'
                    }
                }
            }
        }
        assert result == expected