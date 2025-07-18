"""Tests for configuration manager."""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from pgsd.config.manager import ConfigurationManager
from pgsd.config.schema import PGSDConfiguration, DatabaseConfig, OutputConfig, OutputFormat
from pgsd.exceptions.config import ConfigurationError, MissingConfigurationError


class TestConfigurationManager:
    """Test ConfigurationManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ConfigurationManager()

    def test_initialization(self):
        """Test ConfigurationManager initialization."""
        assert self.manager.config_file is None
        assert self.manager.validator is not None
        assert self.manager.substitutor is not None
        assert self.manager._config is None
        assert self.manager._config_sources == {}

    def test_initialization_with_config_file(self):
        """Test initialization with config file."""
        config_file = "/path/to/config.yaml"
        manager = ConfigurationManager(config_file)
        assert manager.config_file == config_file

    def test_find_config_file_explicit(self):
        """Test finding explicitly specified config file."""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as temp_file:
            temp_path = temp_file.name
            
        try:
            manager = ConfigurationManager(temp_path)
            found_path = manager._find_config_file()
            assert found_path == Path(temp_path).resolve()
        finally:
            os.unlink(temp_path)

    def test_find_config_file_explicit_missing(self):
        """Test error when explicitly specified config file is missing."""
        manager = ConfigurationManager("/nonexistent/config.yaml")
        
        with pytest.raises(MissingConfigurationError):
            manager._find_config_file()

    def test_find_config_file_search_paths(self):
        """Test finding config file in search paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "pgsd_config.yaml"
            config_file.write_text("test: value")
            
            # Mock the search paths to include our temp directory
            with patch.object(ConfigurationManager, 'CONFIG_SEARCH_PATHS', [str(config_file)]):
                manager = ConfigurationManager()
                found_path = manager._find_config_file()
                assert found_path == config_file

    def test_find_config_file_not_found(self):
        """Test when no config file is found."""
        with patch.object(ConfigurationManager, 'CONFIG_SEARCH_PATHS', ["/nonexistent/path"]):
            manager = ConfigurationManager()
            found_path = manager._find_config_file()
            assert found_path is None

    def test_load_file_config_success(self):
        """Test successful file config loading."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            temp_file.write("database:\n  source:\n    host: localhost\n")
            temp_path = temp_file.name
            
        try:
            manager = ConfigurationManager(temp_path)
            config, source = manager._load_file_config()
            
            assert isinstance(config, dict)
            assert 'database' in config
            assert source == str(Path(temp_path).resolve())
        finally:
            os.unlink(temp_path)

    def test_load_file_config_no_file(self):
        """Test file config loading when no file exists."""
        manager = ConfigurationManager()
        
        with patch.object(manager, '_find_config_file', return_value=None):
            config, source = manager._load_file_config()
            
            assert config == {}
            assert source is None

    def test_load_file_config_parse_error(self):
        """Test file config loading with parse error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            temp_file.write("invalid: yaml: content: [")
            temp_path = temp_file.name
            
        try:
            manager = ConfigurationManager(temp_path)
            
            with pytest.raises(ConfigurationError) as exc_info:
                manager._load_file_config()
            
            assert "Failed to load configuration file" in str(exc_info.value)
        finally:
            os.unlink(temp_path)

    @patch('pgsd.config.manager.EnvironmentParser')
    def test_load_env_config_success(self, mock_parser_class):
        """Test successful environment config loading."""
        mock_parser = Mock()
        mock_parser.parse.return_value = {'database': {'source': {'host': 'env_host'}}}
        mock_parser_class.return_value = mock_parser
        
        manager = ConfigurationManager()
        config = manager._load_env_config("PGSD_")
        
        assert isinstance(config, dict)
        mock_parser_class.assert_called_once_with("PGSD_")
        mock_parser.parse.assert_called_once()

    @patch('pgsd.config.manager.EnvironmentParser')
    def test_load_env_config_empty(self, mock_parser_class):
        """Test environment config loading with no variables."""
        mock_parser = Mock()
        mock_parser.parse.return_value = {}
        mock_parser_class.return_value = mock_parser
        
        manager = ConfigurationManager()
        config = manager._load_env_config("PGSD_")
        
        assert config == {}

    def test_deep_update_basic(self):
        """Test basic deep update functionality."""
        base = {'a': 1, 'b': {'c': 2}}
        update = {'b': {'d': 3}, 'e': 4}
        
        manager = ConfigurationManager()
        manager._deep_update(base, update)
        
        assert base == {'a': 1, 'b': {'c': 2, 'd': 3}, 'e': 4}

    def test_deep_update_overwrite(self):
        """Test deep update with overwriting."""
        base = {'a': 1, 'b': {'c': 2}}
        update = {'a': 10, 'b': {'c': 20}}
        
        manager = ConfigurationManager()
        manager._deep_update(base, update)
        
        assert base == {'a': 10, 'b': {'c': 20}}

    def test_deep_update_nested(self):
        """Test deep update with nested dictionaries."""
        base = {'level1': {'level2': {'level3': 'original'}}}
        update = {'level1': {'level2': {'level3': 'updated', 'new': 'value'}}}
        
        manager = ConfigurationManager()
        manager._deep_update(base, update)
        
        assert base == {'level1': {'level2': {'level3': 'updated', 'new': 'value'}}}

    def test_merge_configurations_all_sources(self):
        """Test merging configurations from all sources."""
        file_config = {'database': {'source': {'host': 'file_host'}}}
        env_config = {'database': {'source': {'port': 5432}}}
        cli_config = {'database': {'target': {'host': 'cli_host'}}}
        
        manager = ConfigurationManager()
        result = manager._merge_configurations(file_config, env_config, cli_config)
        
        expected = {
            'database': {
                'source': {'host': 'file_host', 'port': 5432},
                'target': {'host': 'cli_host'}
            }
        }
        assert result == expected

    def test_merge_configurations_priority(self):
        """Test configuration merge priority (CLI > Env > File)."""
        file_config = {'database': {'source': {'host': 'file_host'}}}
        env_config = {'database': {'source': {'host': 'env_host'}}}
        cli_config = {'database': {'source': {'host': 'cli_host'}}}
        
        manager = ConfigurationManager()
        result = manager._merge_configurations(file_config, env_config, cli_config)
        
        # CLI should have highest priority
        assert result['database']['source']['host'] == 'cli_host'

    def test_merge_configurations_empty_sources(self):
        """Test merging with empty sources."""
        manager = ConfigurationManager()
        result = manager._merge_configurations({}, {}, {})
        
        assert result == {}

    def test_get_configuration_not_loaded(self):
        """Test getting configuration when not loaded."""
        manager = ConfigurationManager()
        
        with pytest.raises(ConfigurationError) as exc_info:
            manager.get_configuration()
        
        assert "Configuration not loaded" in str(exc_info.value)

    def test_get_masked_configuration_not_loaded(self):
        """Test getting masked configuration when not loaded."""
        manager = ConfigurationManager()
        
        with pytest.raises(ConfigurationError) as exc_info:
            manager.get_masked_configuration()
        
        assert "Configuration not loaded" in str(exc_info.value)

    def test_get_configuration_sources_empty(self):
        """Test getting configuration sources when empty."""
        manager = ConfigurationManager()
        sources = manager.get_configuration_sources()
        
        assert sources == {}

    def test_get_configuration_sources_copy(self):
        """Test that configuration sources returns a copy."""
        manager = ConfigurationManager()
        manager._config_sources = {'test': 'value'}
        
        sources = manager.get_configuration_sources()
        sources['modified'] = 'changed'
        
        assert 'modified' not in manager._config_sources

    def test_validate_environment_variables_not_loaded(self):
        """Test environment variable validation when config not loaded."""
        manager = ConfigurationManager()
        result = manager.validate_environment_variables()
        
        assert result == ["Configuration not loaded"]

    def test_create_sample_config_file(self):
        """Test creating sample config file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "sample_config.yaml"
            
            manager = ConfigurationManager()
            manager.create_sample_config_file(str(output_path))
            
            assert output_path.exists()
            content = output_path.read_text()
            assert "PGSD Configuration File" in content
            assert "database:" in content
            assert "output:" in content

    def test_create_sample_config_file_creates_directory(self):
        """Test that sample config file creation creates directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "nested" / "dir" / "sample_config.yaml"
            
            manager = ConfigurationManager()
            manager.create_sample_config_file(str(output_path))
            
            assert output_path.exists()
            assert output_path.parent.exists()

    def test_create_sample_config_file_error(self):
        """Test error handling in sample config file creation."""
        manager = ConfigurationManager()
        
        with pytest.raises(ConfigurationError) as exc_info:
            manager.create_sample_config_file("/invalid/path/\x00/config.yaml")
        
        assert "Failed to create sample config file" in str(exc_info.value)

    def test_create_sample_env_file(self):
        """Test creating sample .env file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "sample.env"
            
            manager = ConfigurationManager()
            manager.create_sample_env_file(str(output_path))
            
            assert output_path.exists()
            content = output_path.read_text()
            assert "PGSD Environment Variables Example" in content
            assert "PGSD_SOURCE_PASSWORD" in content
            assert "PGSD_TARGET_PASSWORD" in content

    def test_create_sample_env_file_creates_directory(self):
        """Test that sample .env file creation creates directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "nested" / "dir" / "sample.env"
            
            manager = ConfigurationManager()
            manager.create_sample_env_file(str(output_path))
            
            assert output_path.exists()
            assert output_path.parent.exists()

    def test_create_sample_env_file_error(self):
        """Test error handling in sample .env file creation."""
        manager = ConfigurationManager()
        
        with pytest.raises(ConfigurationError) as exc_info:
            manager.create_sample_env_file("/invalid/path/\x00/sample.env")
        
        assert "Failed to create sample .env file" in str(exc_info.value)


class TestConfigurationManagerIntegration:
    """Integration tests for ConfigurationManager."""

    @patch('pgsd.config.manager.ConfigurationValidator')
    @patch('pgsd.config.manager.EnvironmentSubstitutor')
    def test_load_configuration_success(self, mock_substitutor_class, mock_validator_class):
        """Test successful configuration loading."""
        # Setup mocks
        mock_validator = Mock()
        mock_config = Mock(spec=PGSDConfiguration)
        mock_config.source_db = Mock()
        mock_config.source_db.host = "localhost"
        mock_config.source_db.port = 5432
        mock_config.source_db.database = "testdb"
        mock_config.target_db = Mock()
        mock_config.target_db.host = "localhost"
        mock_config.target_db.port = 5432
        mock_config.target_db.database = "testdb2"
        mock_config.output = Mock()
        mock_config.output.format = Mock()
        mock_config.output.format.value = "html"
        mock_config.output.path = "./reports"
        mock_config.system = Mock()
        mock_config.system.log_level = Mock()
        mock_config.system.log_level.value = "INFO"
        
        mock_validator.validate.return_value = mock_config
        mock_validator_class.return_value = mock_validator
        
        mock_substitutor = Mock()
        mock_substitutor.substitute.return_value = {'test': 'config'}
        mock_substitutor_class.return_value = mock_substitutor
        
        manager = ConfigurationManager()
        
        # Mock the private methods
        with patch.object(manager, '_load_file_config', return_value=({}, None)):
            with patch.object(manager, '_load_env_config', return_value={}):
                result = manager.load_configuration()
                
                assert result == mock_config
                assert manager._config == mock_config
                mock_validator.validate.assert_called_once()
                mock_substitutor.substitute.assert_called_once()

    @patch('pgsd.config.manager.ConfigurationValidator')
    @patch('pgsd.config.manager.EnvironmentSubstitutor')
    def test_load_configuration_cli_args(self, mock_substitutor_class, mock_validator_class):
        """Test configuration loading with CLI arguments."""
        # Setup mocks
        mock_validator = Mock()
        mock_config = Mock(spec=PGSDConfiguration)
        mock_config.source_db = Mock()
        mock_config.source_db.host = "localhost"
        mock_config.source_db.port = 5432
        mock_config.source_db.database = "testdb"
        mock_config.target_db = Mock()
        mock_config.target_db.host = "localhost"
        mock_config.target_db.port = 5432
        mock_config.target_db.database = "testdb2"
        mock_config.output = Mock()
        mock_config.output.format = Mock()
        mock_config.output.format.value = "html"
        mock_config.output.path = "./reports"
        mock_config.system = Mock()
        mock_config.system.log_level = Mock()
        mock_config.system.log_level.value = "INFO"
        
        mock_validator.validate.return_value = mock_config
        mock_validator_class.return_value = mock_validator
        
        mock_substitutor = Mock()
        mock_substitutor.substitute.return_value = {'test': 'config'}
        mock_substitutor_class.return_value = mock_substitutor
        
        manager = ConfigurationManager()
        cli_args = {'database': {'source': {'host': 'cli_host'}}}
        
        # Mock the private methods
        with patch.object(manager, '_load_file_config', return_value=({}, None)):
            with patch.object(manager, '_load_env_config', return_value={}):
                result = manager.load_configuration(cli_args)
                
                assert result == mock_config
                assert manager._config_sources['cli_args'] is True

    @patch('pgsd.config.manager.ConfigurationValidator')
    @patch('pgsd.config.manager.EnvironmentSubstitutor')
    def test_load_configuration_validation_error(self, mock_substitutor_class, mock_validator_class):
        """Test configuration loading with validation error."""
        mock_validator = Mock()
        mock_validator.validate.side_effect = ConfigurationError("Validation failed")
        mock_validator_class.return_value = mock_validator
        
        mock_substitutor = Mock()
        mock_substitutor.substitute.return_value = {'test': 'config'}
        mock_substitutor_class.return_value = mock_substitutor
        
        manager = ConfigurationManager()
        
        with patch.object(manager, '_load_file_config', return_value=({}, None)):
            with patch.object(manager, '_load_env_config', return_value={}):
                with pytest.raises(ConfigurationError) as exc_info:
                    manager.load_configuration()
                
                assert "Validation failed" in str(exc_info.value)

    @patch('pgsd.config.manager.ConfigurationValidator')
    @patch('pgsd.config.manager.EnvironmentSubstitutor')
    def test_load_configuration_unexpected_error(self, mock_substitutor_class, mock_validator_class):
        """Test configuration loading with unexpected error."""
        mock_validator = Mock()
        mock_validator.validate.side_effect = RuntimeError("Unexpected error")
        mock_validator_class.return_value = mock_validator
        
        mock_substitutor = Mock()
        mock_substitutor.substitute.return_value = {'test': 'config'}
        mock_substitutor_class.return_value = mock_substitutor
        
        manager = ConfigurationManager()
        
        with patch.object(manager, '_load_file_config', return_value=({}, None)):
            with patch.object(manager, '_load_env_config', return_value={}):
                with pytest.raises(ConfigurationError) as exc_info:
                    manager.load_configuration()
                
                assert "Unexpected error during configuration loading" in str(exc_info.value)

    @patch('pgsd.config.manager.ConfigurationValidator')
    @patch('pgsd.config.manager.EnvironmentSubstitutor')
    def test_reload_configuration(self, mock_substitutor_class, mock_validator_class):
        """Test configuration reloading."""
        mock_validator = Mock()
        mock_config = Mock(spec=PGSDConfiguration)
        mock_config.source_db = Mock()
        mock_config.source_db.host = "localhost"
        mock_config.source_db.port = 5432
        mock_config.source_db.database = "testdb"
        mock_config.target_db = Mock()
        mock_config.target_db.host = "localhost"  
        mock_config.target_db.port = 5432
        mock_config.target_db.database = "testdb2"
        mock_config.output = Mock()
        mock_config.output.format = Mock()
        mock_config.output.format.value = "html"
        mock_config.output.path = "./reports"
        mock_config.system = Mock()
        mock_config.system.log_level = Mock()
        mock_config.system.log_level.value = "INFO"
        
        mock_validator.validate.return_value = mock_config
        mock_validator_class.return_value = mock_validator
        
        mock_substitutor = Mock()
        mock_substitutor.substitute.return_value = {'test': 'config'}
        mock_substitutor_class.return_value = mock_substitutor
        
        manager = ConfigurationManager()
        
        # Set some initial state
        manager._config = Mock()
        manager._config_sources = {'test': 'value'}
        
        with patch.object(manager, '_load_file_config', return_value=({}, None)):
            with patch.object(manager, '_load_env_config', return_value={}):
                result = manager.reload_configuration()
                
                assert result == mock_config
                assert manager._config == mock_config

    def test_get_configuration_loaded(self):
        """Test getting configuration when loaded."""
        manager = ConfigurationManager()
        mock_config = Mock(spec=PGSDConfiguration)
        manager._config = mock_config
        
        result = manager.get_configuration()
        assert result == mock_config

    def test_get_masked_configuration_loaded(self):
        """Test getting masked configuration when loaded."""
        manager = ConfigurationManager()
        mock_config = Mock(spec=PGSDConfiguration)
        mock_config.get_masked_dict.return_value = {'masked': 'config'}
        manager._config = mock_config
        
        result = manager.get_masked_configuration()
        assert result == {'masked': 'config'}
        mock_config.get_masked_dict.assert_called_once()

    def test_validate_environment_variables_loaded(self):
        """Test environment variable validation when config loaded."""
        manager = ConfigurationManager()
        mock_config = Mock(spec=PGSDConfiguration)
        mock_config.get_masked_dict.return_value = {'test': 'config'}
        manager._config = mock_config
        
        mock_substitutor = Mock()
        mock_substitutor.validate_substitutions.return_value = []
        manager.substitutor = mock_substitutor
        
        result = manager.validate_environment_variables()
        
        assert result == []
        mock_substitutor.validate_substitutions.assert_called_once_with({'test': 'config'})

    def test_log_configuration_summary_complete(self):
        """Test logging configuration summary with complete config."""
        manager = ConfigurationManager()
        mock_config = Mock(spec=PGSDConfiguration)
        mock_config.source_db = Mock()
        mock_config.source_db.host = "source_host"
        mock_config.source_db.port = 5432
        mock_config.source_db.database = "source_db"
        mock_config.target_db = Mock()
        mock_config.target_db.host = "target_host"
        mock_config.target_db.port = 5433
        mock_config.target_db.database = "target_db"
        mock_config.output = Mock()
        mock_config.output.format = Mock()
        mock_config.output.format.value = "json"
        mock_config.output.path = "/tmp/reports"
        mock_config.system = Mock()
        mock_config.system.log_level = Mock()
        mock_config.system.log_level.value = "DEBUG"
        
        manager._config = mock_config
        manager._config_sources = {
            'file': '/path/to/config.yaml',
            'environment_vars': True,
            'cli_args': True
        }
        
        # Should not raise any errors
        manager._log_configuration_summary()

    def test_log_configuration_summary_no_config(self):
        """Test logging configuration summary with no config."""
        manager = ConfigurationManager()
        manager._config = None
        
        # Should not raise any errors
        manager._log_configuration_summary()

    def test_log_configuration_summary_no_sources(self):
        """Test logging configuration summary with no sources."""
        manager = ConfigurationManager()
        mock_config = Mock(spec=PGSDConfiguration)
        mock_config.source_db = Mock()
        mock_config.source_db.host = "source_host"
        mock_config.source_db.port = 5432
        mock_config.source_db.database = "source_db"
        mock_config.target_db = Mock()
        mock_config.target_db.host = "target_host"
        mock_config.target_db.port = 5433
        mock_config.target_db.database = "target_db"
        mock_config.output = Mock()
        mock_config.output.format = Mock()
        mock_config.output.format.value = "json"
        mock_config.output.path = "/tmp/reports"
        mock_config.system = Mock()
        mock_config.system.log_level = Mock()
        mock_config.system.log_level.value = "DEBUG"
        
        manager._config = mock_config
        manager._config_sources = {}
        
        # Should not raise any errors
        manager._log_configuration_summary()


class TestConfigurationManagerEdgeCases:
    """Test edge cases and error conditions."""

    def test_expanduser_in_config_path(self):
        """Test that config paths with ~ are properly expanded."""
        manager = ConfigurationManager("~/config.yaml")
        
        # Create a temp file in the home directory for testing
        home_dir = Path.home()
        test_config = home_dir / "test_config.yaml"
        test_config.write_text("test: config")
        
        try:
            manager.config_file = str(test_config)
            found_path = manager._find_config_file()
            assert found_path == test_config.resolve()
        finally:
            test_config.unlink()

    def test_config_sources_tracking(self):
        """Test that configuration sources are properly tracked."""
        manager = ConfigurationManager()
        
        # Simulate loading with different sources
        manager._config_sources = {
            'file': '/path/to/config.yaml',
            'environment_vars': True,
            'cli_args': False
        }
        
        sources = manager.get_configuration_sources()
        assert sources['file'] == '/path/to/config.yaml'
        assert sources['environment_vars'] is True
        assert sources['cli_args'] is False

    def test_deep_update_with_none_values(self):
        """Test deep update with None values."""
        base = {'a': {'b': 'original'}}
        update = {'a': {'b': None}}
        
        manager = ConfigurationManager()
        manager._deep_update(base, update)
        
        assert base['a']['b'] is None

    def test_merge_configurations_with_lists(self):
        """Test merge configurations with list values."""
        file_config = {'exclude_tables': ['temp_*']}
        env_config = {'exclude_tables': ['log_*']}
        cli_config = {'exclude_tables': ['audit_*']}
        
        manager = ConfigurationManager()
        result = manager._merge_configurations(file_config, env_config, cli_config)
        
        # Lists should be replaced, not merged
        assert result['exclude_tables'] == ['audit_*']