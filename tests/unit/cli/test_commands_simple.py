"""Simple tests for CLI commands."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from argparse import Namespace
from pathlib import Path

from pgsd.cli.commands import BaseCommand, CompareCommand, ListSchemasCommand, ValidateCommand, VersionCommand
from pgsd.config.schema import PGSDConfiguration, DatabaseConfig, OutputFormat
from pgsd.exceptions.base import PGSDError
from pgsd.exceptions.database import DatabaseConnectionError
from pgsd.exceptions.config import ConfigurationError


class TestBaseCommand:
    """Test cases for BaseCommand class."""

    def create_test_config(self):
        """Create test configuration."""
        source_db = DatabaseConfig(
            host="source.example.com",
            port=5432,
            database="source_db",
            username="source_user",
            password="source_pass"
        )
        target_db = DatabaseConfig(
            host="target.example.com",
            port=5432,
            database="target_db",
            username="target_user",
            password="target_pass"
        )
        return PGSDConfiguration(source_db=source_db, target_db=target_db)

    def test_init(self):
        """Test BaseCommand initialization."""
        args = Namespace(verbose=False)
        config = self.create_test_config()
        
        # Can't instantiate abstract class directly, so we'll test through a concrete subclass
        class TestCommand(BaseCommand):
            def execute(self):
                return 0
        
        command = TestCommand(args, config)
        
        assert command.args == args
        assert command.config == config
        assert command.progress_reporter is not None
        assert command.logger is not None


class TestCompareCommand:
    """Test cases for CompareCommand class."""

    def create_test_config(self):
        """Create test configuration."""
        source_db = DatabaseConfig(
            host="source.example.com",
            port=5432,
            database="source_db",
            username="source_user",
            password="source_pass"
        )
        target_db = DatabaseConfig(
            host="target.example.com",
            port=5432,
            database="target_db",
            username="target_user",
            password="target_pass"
        )
        return PGSDConfiguration(source_db=source_db, target_db=target_db)

    def test_init(self):
        """Test CompareCommand initialization."""
        args = Namespace(
            output_file="test.html",
            format="html",
            verbose=False
        )
        config = self.create_test_config()
        
        command = CompareCommand(args, config)
        
        assert command.args == args
        assert command.config == config

    @patch('pgsd.cli.commands.DatabaseManager')
    @patch('pgsd.cli.commands.SchemaComparisonEngine')
    @patch('pgsd.cli.commands.create_reporter')
    def test_execute_success(self, mock_create_reporter, mock_engine_class, mock_manager_class):
        """Test successful command execution."""
        args = Namespace(
            output_file="test.html",
            format="html",
            verbose=False
        )
        config = self.create_test_config()
        
        # Mock database manager
        mock_manager = Mock()
        mock_manager.__aenter__ = Mock(return_value=mock_manager)
        mock_manager.__aexit__ = Mock(return_value=None)
        mock_manager_class.return_value = mock_manager
        
        # Mock comparison engine
        mock_engine = Mock()
        mock_engine.compare_schemas = Mock(return_value={"differences": []})
        mock_engine_class.return_value = mock_engine
        
        # Mock reporter
        mock_reporter = Mock()
        mock_reporter.generate_report = Mock()
        mock_create_reporter.return_value = mock_reporter
        
        command = CompareCommand(args, config)
        
        # Mock the async run
        with patch('asyncio.run') as mock_asyncio_run:
            mock_asyncio_run.return_value = None
            
            result = command.execute()
        
        assert result == 0
        mock_asyncio_run.assert_called_once()

    @patch('pgsd.cli.commands.DatabaseManager')
    def test_execute_database_error(self, mock_manager_class):
        """Test command execution with database error."""
        args = Namespace(
            output_file="test.html",
            format="html",
            verbose=False
        )
        config = self.create_test_config()
        
        # Mock database manager to raise error
        mock_manager = Mock()
        mock_manager.__aenter__ = Mock(side_effect=DatabaseConnectionError("Connection failed"))
        mock_manager_class.return_value = mock_manager
        
        command = CompareCommand(args, config)
        
        with patch('asyncio.run') as mock_asyncio_run:
            mock_asyncio_run.side_effect = DatabaseConnectionError("Connection failed")
            
            result = command.execute()
        
        assert result == 1

    def test_execute_config_error(self):
        """Test command execution with configuration error."""
        args = Namespace(
            output_file="test.html",
            format="html",
            verbose=False
        )
        config = self.create_test_config()
        
        command = CompareCommand(args, config)
        
        with patch('asyncio.run') as mock_asyncio_run:
            mock_asyncio_run.side_effect = ConfigurationError("Invalid config")
            
            result = command.execute()
        
        assert result == 1

    def test_execute_general_error(self):
        """Test command execution with general error."""
        args = Namespace(
            output_file="test.html",
            format="html",
            verbose=False
        )
        config = self.create_test_config()
        
        command = CompareCommand(args, config)
        
        with patch('asyncio.run') as mock_asyncio_run:
            mock_asyncio_run.side_effect = Exception("Unexpected error")
            
            result = command.execute()
        
        assert result == 1

    def test_determine_output_format_from_extension(self):
        """Test output format determination from file extension."""
        args = Namespace(
            output_file="test.json",
            format=None,
            verbose=False
        )
        config = self.create_test_config()
        
        command = CompareCommand(args, config)
        format_result = command._determine_output_format()
        
        assert format_result == OutputFormat.JSON

    def test_determine_output_format_from_args(self):
        """Test output format determination from arguments."""
        args = Namespace(
            output_file="test.txt",
            format="xml",
            verbose=False
        )
        config = self.create_test_config()
        
        command = CompareCommand(args, config)
        format_result = command._determine_output_format()
        
        assert format_result == OutputFormat.XML

    def test_determine_output_format_default(self):
        """Test default output format determination."""
        args = Namespace(
            output_file=None,
            format=None,
            verbose=False
        )
        config = self.create_test_config()
        
        command = CompareCommand(args, config)
        format_result = command._determine_output_format()
        
        assert format_result == OutputFormat.HTML


class TestListSchemasCommand:
    """Test cases for ListSchemasCommand class."""

    def create_test_config(self):
        """Create test configuration."""
        source_db = DatabaseConfig(
            host="source.example.com",
            port=5432,
            database="source_db",
            username="source_user",
            password="source_pass"
        )
        target_db = DatabaseConfig(
            host="target.example.com",
            port=5432,
            database="target_db",
            username="target_user",
            password="target_pass"
        )
        return PGSDConfiguration(source_db=source_db, target_db=target_db)

    def test_init(self):
        """Test ListSchemasCommand initialization."""
        args = Namespace(
            database="source",
            verbose=False
        )
        config = self.create_test_config()
        
        command = ListSchemasCommand(args, config)
        
        assert command.args == args
        assert command.config == config

    @patch('pgsd.cli.commands.DatabaseManager')
    def test_execute_success(self, mock_manager_class):
        """Test successful schema listing."""
        args = Namespace(
            database="source",
            verbose=False
        )
        config = self.create_test_config()
        
        # Mock database manager
        mock_manager = Mock()
        mock_manager.__aenter__ = Mock(return_value=mock_manager)
        mock_manager.__aexit__ = Mock(return_value=None)
        mock_manager.get_source_connection = Mock()
        mock_manager.release_source_connection = Mock()
        mock_manager_class.return_value = mock_manager
        
        # Mock connection
        mock_connection = Mock()
        mock_connection.execute_query = Mock(return_value=[
            {"schema_name": "public"},
            {"schema_name": "test_schema"}
        ])
        mock_manager.get_source_connection.return_value = mock_connection
        
        command = ListSchemasCommand(args, config)
        
        with patch('asyncio.run') as mock_asyncio_run:
            mock_asyncio_run.return_value = None
            
            result = command.execute()
        
        assert result == 0

    @patch('pgsd.cli.commands.DatabaseManager')
    def test_execute_target_database(self, mock_manager_class):
        """Test schema listing for target database."""
        args = Namespace(
            database="target",
            verbose=False
        )
        config = self.create_test_config()
        
        # Mock database manager
        mock_manager = Mock()
        mock_manager.__aenter__ = Mock(return_value=mock_manager)
        mock_manager.__aexit__ = Mock(return_value=None)
        mock_manager.get_target_connection = Mock()
        mock_manager.release_target_connection = Mock()
        mock_manager_class.return_value = mock_manager
        
        # Mock connection
        mock_connection = Mock()
        mock_connection.execute_query = Mock(return_value=[
            {"schema_name": "information_schema"},
            {"schema_name": "pg_catalog"}
        ])
        mock_manager.get_target_connection.return_value = mock_connection
        
        command = ListSchemasCommand(args, config)
        
        with patch('asyncio.run') as mock_asyncio_run:
            mock_asyncio_run.return_value = None
            
            result = command.execute()
        
        assert result == 0

    def test_execute_invalid_database(self):
        """Test schema listing with invalid database."""
        args = Namespace(
            database="invalid",
            verbose=False
        )
        config = self.create_test_config()
        
        command = ListSchemasCommand(args, config)
        
        result = command.execute()
        
        assert result == 1


class TestValidateCommand:
    """Test cases for ValidateCommand class."""

    def create_test_config(self):
        """Create test configuration."""
        source_db = DatabaseConfig(
            host="source.example.com",
            port=5432,
            database="source_db",
            username="source_user",
            password="source_pass"
        )
        target_db = DatabaseConfig(
            host="target.example.com",
            port=5432,
            database="target_db",
            username="target_user",
            password="target_pass"
        )
        return PGSDConfiguration(source_db=source_db, target_db=target_db)

    def test_init(self):
        """Test ValidateCommand initialization."""
        args = Namespace(verbose=False)
        config = self.create_test_config()
        
        command = ValidateCommand(args, config)
        
        assert command.args == args
        assert command.config == config

    @patch('pgsd.cli.commands.DatabaseManager')
    def test_execute_success(self, mock_manager_class):
        """Test successful configuration validation."""
        args = Namespace(verbose=False)
        config = self.create_test_config()
        
        # Mock database manager
        mock_manager = Mock()
        mock_manager.test_connections = Mock(return_value={
            "source": True,
            "target": True
        })
        mock_manager_class.return_value = mock_manager
        
        command = ValidateCommand(args, config)
        
        with patch('asyncio.run') as mock_asyncio_run:
            mock_asyncio_run.return_value = None
            
            result = command.execute()
        
        assert result == 0

    @patch('pgsd.cli.commands.DatabaseManager')
    def test_execute_connection_failure(self, mock_manager_class):
        """Test validation with connection failure."""
        args = Namespace(verbose=False)
        config = self.create_test_config()
        
        # Mock database manager
        mock_manager = Mock()
        mock_manager.test_connections = Mock(return_value={
            "source": True,
            "target": False
        })
        mock_manager_class.return_value = mock_manager
        
        command = ValidateCommand(args, config)
        
        with patch('asyncio.run') as mock_asyncio_run:
            mock_asyncio_run.return_value = None
            
            result = command.execute()
        
        assert result == 1

    def test_execute_exception(self):
        """Test validation with exception."""
        args = Namespace(verbose=False)
        config = self.create_test_config()
        
        command = ValidateCommand(args, config)
        
        with patch('asyncio.run') as mock_asyncio_run:
            mock_asyncio_run.side_effect = Exception("Validation error")
            
            result = command.execute()
        
        assert result == 1


class TestVersionCommand:
    """Test cases for VersionCommand class."""

    def create_test_config(self):
        """Create test configuration."""
        source_db = DatabaseConfig(
            host="source.example.com",
            port=5432,
            database="source_db",
            username="source_user",
            password="source_pass"
        )
        target_db = DatabaseConfig(
            host="target.example.com",
            port=5432,
            database="target_db",
            username="target_user",
            password="target_pass"
        )
        return PGSDConfiguration(source_db=source_db, target_db=target_db)

    def test_init(self):
        """Test VersionCommand initialization."""
        args = Namespace(verbose=False)
        config = self.create_test_config()
        
        command = VersionCommand(args, config)
        
        assert command.args == args
        assert command.config == config

    def test_execute_success(self):
        """Test successful version display."""
        args = Namespace(verbose=False)
        config = self.create_test_config()
        
        command = VersionCommand(args, config)
        
        with patch('builtins.print') as mock_print:
            result = command.execute()
        
        assert result == 0
        mock_print.assert_called()

    def test_execute_with_verbose(self):
        """Test version display with verbose output."""
        args = Namespace(verbose=True)
        config = self.create_test_config()
        
        command = VersionCommand(args, config)
        
        with patch('builtins.print') as mock_print:
            result = command.execute()
        
        assert result == 0
        # Should print more information in verbose mode
        assert mock_print.call_count > 1