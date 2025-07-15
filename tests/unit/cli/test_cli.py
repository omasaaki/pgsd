"""Unit tests for CLI interface.

This module tests the CLI functionality including argument parsing,
command execution, and configuration integration.
"""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from argparse import Namespace

from src.pgsd.cli.main import CLIManager
from src.pgsd.cli.commands import CompareCommand, ListSchemasCommand, ValidateCommand, VersionCommand
from src.pgsd.config.schema import PGSDConfiguration, DatabaseConfig, OutputFormat
from src.pgsd.exceptions.config import ConfigurationError


class TestCLIManager:
    """Test cases for CLIManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cli_manager = CLIManager()

    def test_parser_creation(self):
        """Test that argument parser is created correctly."""
        assert self.cli_manager.parser is not None
        assert hasattr(self.cli_manager.parser, 'parse_args')

    def test_subcommands_registered(self):
        """Test that all subcommands are registered."""
        # Get subparsers
        subparsers_actions = [
            action for action in self.cli_manager.parser._actions
            if hasattr(action, 'choices')
        ]
        
        assert len(subparsers_actions) > 0
        subcommands = subparsers_actions[0].choices
        
        expected_commands = {'compare', 'list-schemas', 'validate', 'version'}
        assert set(subcommands.keys()) == expected_commands

    def test_parse_compare_command_basic(self):
        """Test parsing basic compare command."""
        args = [
            'compare',
            '--source-host', 'localhost',
            '--source-db', 'source_db',
            '--target-host', 'localhost', 
            '--target-db', 'target_db'
        ]
        
        parsed_args = self.cli_manager.parser.parse_args(args)
        
        assert parsed_args.command == 'compare'
        assert parsed_args.source_host == 'localhost'
        assert parsed_args.source_db == 'source_db'
        assert parsed_args.target_host == 'localhost'
        assert parsed_args.target_db == 'target_db'

    def test_parse_compare_command_with_options(self):
        """Test parsing compare command with optional arguments."""
        args = [
            'compare',
            '--source-host', 'localhost',
            '--source-db', 'source_db',
            '--target-host', 'localhost',
            '--target-db', 'target_db',
            '--schema', 'public',
            '--output', '/tmp/reports',
            '--format', 'html,json',
            '--config', 'config.yaml',
            '--verbose'
        ]
        
        parsed_args = self.cli_manager.parser.parse_args(args)
        
        assert parsed_args.schema == 'public'
        assert parsed_args.output == '/tmp/reports'
        assert parsed_args.format == 'html,json'
        assert parsed_args.config == 'config.yaml'
        assert parsed_args.verbose is True

    def test_parse_list_schemas_command(self):
        """Test parsing list-schemas command."""
        args = [
            'list-schemas',
            '--host', 'localhost',
            '--db', 'test_db'
        ]
        
        parsed_args = self.cli_manager.parser.parse_args(args)
        
        assert parsed_args.command == 'list-schemas'
        assert parsed_args.host == 'localhost'
        assert parsed_args.db == 'test_db'

    def test_parse_validate_command(self):
        """Test parsing validate command."""
        args = ['validate', '--config', 'config.yaml']
        
        parsed_args = self.cli_manager.parser.parse_args(args)
        
        assert parsed_args.command == 'validate'
        assert parsed_args.config == 'config.yaml'

    def test_parse_version_command(self):
        """Test parsing version command."""
        args = ['version']
        
        parsed_args = self.cli_manager.parser.parse_args(args)
        
        assert parsed_args.command == 'version'

    def test_missing_required_arguments(self):
        """Test error handling for missing required arguments."""
        args = ['compare']  # Missing required database arguments
        
        with pytest.raises(SystemExit):
            self.cli_manager.parser.parse_args(args)

    @patch('src.pgsd.cli.commands.CompareCommand')
    def test_run_compare_command(self, mock_compare_command):
        """Test running compare command."""
        mock_command = Mock()
        mock_compare_command.return_value = mock_command
        mock_command.execute.return_value = 0
        
        args = [
            'compare',
            '--source-host', 'localhost',
            '--source-db', 'source_db',
            '--target-host', 'localhost',
            '--target-db', 'target_db'
        ]
        
        result = self.cli_manager.run(args)
        
        assert result == 0
        mock_compare_command.assert_called_once()
        mock_command.execute.assert_called_once()

    @patch('src.pgsd.cli.main.ConfigurationManager')
    def test_configuration_integration(self, mock_config_manager):
        """Test configuration manager integration."""
        mock_config = Mock(spec=PGSDConfiguration)
        mock_config_manager.return_value.load_configuration.return_value = mock_config
        
        args = [
            'compare',
            '--source-host', 'localhost',
            '--source-db', 'source_db',
            '--target-host', 'localhost',
            '--target-db', 'target_db',
            '--config', 'test_config.yaml'
        ]
        
        with patch('src.pgsd.cli.commands.CompareCommand') as mock_compare_command:
            mock_command = Mock()
            mock_compare_command.return_value = mock_command
            mock_command.execute.return_value = 0
            
            result = self.cli_manager.run(args)
            
            assert result == 0
            mock_config_manager.assert_called_once_with('test_config.yaml')

    def test_error_handling(self):
        """Test error handling in CLI execution."""
        with patch('src.pgsd.cli.commands.CompareCommand') as mock_compare_command:
            mock_command = Mock()
            mock_compare_command.return_value = mock_command
            mock_command.execute.side_effect = Exception("Test error")
            
            args = [
                'compare',
                '--source-host', 'localhost',
                '--source-db', 'source_db',
                '--target-host', 'localhost',
                '--target-db', 'target_db'
            ]
            
            result = self.cli_manager.run(args)
            
            assert result == 1  # Error exit code

    @patch('sys.exit')
    def test_keyboard_interrupt_handling(self, mock_exit):
        """Test handling of keyboard interrupt."""
        with patch('src.pgsd.cli.commands.CompareCommand') as mock_compare_command:
            mock_command = Mock()
            mock_compare_command.return_value = mock_command
            mock_command.execute.side_effect = KeyboardInterrupt()
            
            args = [
                'compare',
                '--source-host', 'localhost',
                '--source-db', 'source_db',
                '--target-host', 'localhost',
                '--target-db', 'target_db'
            ]
            
            self.cli_manager.run(args)
            
            mock_exit.assert_called_once_with(130)  # SIGINT exit code


class TestCompareCommand:
    """Test cases for CompareCommand class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_config = Mock(spec=PGSDConfiguration)
        self.mock_args = Mock(spec=Namespace)
        self.mock_args.source_host = 'localhost'
        self.mock_args.source_db = 'source_db'
        self.mock_args.target_host = 'localhost'
        self.mock_args.target_db = 'target_db'
        self.mock_args.schema = 'public'
        self.mock_args.output = './reports'
        self.mock_args.format = 'html'
        self.mock_args.verbose = False
        self.mock_args.dry_run = False

    def test_initialization(self):
        """Test CompareCommand initialization."""
        command = CompareCommand(self.mock_args, self.mock_config)
        
        assert command.args == self.mock_args
        assert command.config == self.mock_config

    @patch('src.pgsd.cli.commands.SchemaComparisonEngine')
    @patch('src.pgsd.cli.commands.create_reporter')
    def test_execute_successful(self, mock_create_reporter, mock_schema_engine):
        """Test successful execution of compare command."""
        # Setup mocks
        mock_engine = Mock()
        mock_schema_engine.return_value = mock_engine
        mock_diff_result = Mock()
        
        # Mock async methods
        async def mock_initialize():
            pass
        async def mock_compare():
            return mock_diff_result
            
        mock_engine.initialize = mock_initialize
        mock_engine.compare_schemas = mock_compare
        
        mock_reporter = Mock()
        mock_create_reporter.return_value = mock_reporter
        mock_reporter.generate_report.return_value = Path('./reports/report.html')
        
        command = CompareCommand(self.mock_args, self.mock_config)
        result = command.execute()
        
        assert result == 0
        mock_reporter.generate_report.assert_called_once()

    @patch('src.pgsd.cli.commands.SchemaComparisonEngine')
    def test_execute_with_dry_run(self, mock_schema_engine):
        """Test execute with dry run option."""
        self.mock_args.dry_run = True
        
        command = CompareCommand(self.mock_args, self.mock_config)
        result = command.execute()
        
        assert result == 0
        mock_schema_engine.assert_not_called()

    def test_validate_arguments_success(self):
        """Test successful argument validation."""
        command = CompareCommand(self.mock_args, self.mock_config)
        
        # Should not raise any exception
        command._validate_arguments()

    def test_validate_arguments_missing_source_db(self):
        """Test argument validation with missing source database."""
        self.mock_args.source_db = None
        
        command = CompareCommand(self.mock_args, self.mock_config)
        
        with pytest.raises(ValueError, match="Source database is required"):
            command._validate_arguments()

    def test_validate_arguments_missing_target_db(self):
        """Test argument validation with missing target database."""
        self.mock_args.target_db = None
        
        command = CompareCommand(self.mock_args, self.mock_config)
        
        with pytest.raises(ValueError, match="Target database is required"):
            command._validate_arguments()


class TestListSchemasCommand:
    """Test cases for ListSchemasCommand class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_config = Mock(spec=PGSDConfiguration)
        self.mock_args = Mock(spec=Namespace)
        self.mock_args.host = 'localhost'
        self.mock_args.db = 'test_db'

    @patch('src.pgsd.cli.commands.DatabaseManager')
    def test_execute_successful(self, mock_db_manager):
        """Test successful execution of list-schemas command."""
        mock_manager = Mock()
        mock_db_manager.return_value = mock_manager
        mock_manager.list_schemas.return_value = ['public', 'test_schema']
        
        command = ListSchemasCommand(self.mock_args, self.mock_config)
        result = command.execute()
        
        assert result == 0
        mock_manager.list_schemas.assert_called_once()

    @patch('src.pgsd.cli.commands.DatabaseManager')
    def test_execute_with_connection_error(self, mock_db_manager):
        """Test execution with database connection error."""
        mock_manager = Mock()
        mock_db_manager.return_value = mock_manager
        mock_manager.list_schemas.side_effect = Exception("Connection failed")
        
        command = ListSchemasCommand(self.mock_args, self.mock_config)
        result = command.execute()
        
        assert result == 1


class TestValidateCommand:
    """Test cases for ValidateCommand class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_config = Mock(spec=PGSDConfiguration)
        self.mock_args = Mock(spec=Namespace)
        self.mock_args.config = 'test_config.yaml'

    @patch('src.pgsd.cli.commands.ConfigurationManager')
    def test_execute_valid_config(self, mock_config_manager):
        """Test execution with valid configuration."""
        mock_manager = Mock()
        mock_config_manager.return_value = mock_manager
        mock_manager.load_configuration.return_value = self.mock_config
        
        command = ValidateCommand(self.mock_args, self.mock_config)
        result = command.execute()
        
        assert result == 0

    @patch('src.pgsd.cli.commands.ConfigurationManager')
    def test_execute_invalid_config(self, mock_config_manager):
        """Test execution with invalid configuration."""
        mock_manager = Mock()
        mock_config_manager.return_value = mock_manager
        mock_manager.load_configuration.side_effect = ConfigurationError("Invalid config")
        
        command = ValidateCommand(self.mock_args, self.mock_config)
        result = command.execute()
        
        assert result == 1


class TestVersionCommand:
    """Test cases for VersionCommand class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_config = Mock(spec=PGSDConfiguration)
        self.mock_args = Mock(spec=Namespace)

    def test_execute(self):
        """Test version command execution."""
        command = VersionCommand(self.mock_args, self.mock_config)
        result = command.execute()
        
        assert result == 0


class TestCLIIntegration:
    """Integration tests for CLI functionality."""

    @patch('src.pgsd.cli.main.ConfigurationManager')
    @patch('src.pgsd.cli.commands.SchemaComparisonEngine')
    @patch('src.pgsd.cli.commands.create_reporter')
    def test_full_cli_workflow(self, mock_create_reporter, mock_schema_engine, mock_config_manager):
        """Test complete CLI workflow from argument parsing to execution."""
        # Setup mocks
        mock_config = Mock(spec=PGSDConfiguration)
        mock_config_manager.return_value.load_configuration.return_value = mock_config
        
        mock_engine = Mock()
        mock_schema_engine.return_value = mock_engine
        mock_diff_result = Mock()
        
        # Mock async methods
        async def mock_initialize():
            pass
        async def mock_compare():
            return mock_diff_result
            
        mock_engine.initialize = mock_initialize
        mock_engine.compare_schemas = mock_compare
        
        mock_reporter = Mock()
        mock_create_reporter.return_value = mock_reporter
        mock_reporter.generate_report.return_value = Path('./reports/report.html')
        
        cli_manager = CLIManager()
        args = [
            'compare',
            '--source-host', 'localhost',
            '--source-db', 'source_db',
            '--target-host', 'localhost',
            '--target-db', 'target_db',
            '--format', 'html'
        ]
        
        result = cli_manager.run(args)
        
        assert result == 0
        mock_config_manager.assert_called()
        mock_reporter.generate_report.assert_called_once()

    def test_help_messages(self):
        """Test that help messages are generated correctly."""
        cli_manager = CLIManager()
        
        # Test main help
        with pytest.raises(SystemExit):
            cli_manager.parser.parse_args(['--help'])
        
        # Test subcommand help
        with pytest.raises(SystemExit):
            cli_manager.parser.parse_args(['compare', '--help'])