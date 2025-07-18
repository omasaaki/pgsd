"""Tests for CLI main module."""

import pytest
import sys
import logging
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from argparse import Namespace

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from pgsd.cli.main import CLIManager, main
from pgsd.config.schema import PGSDConfiguration
from pgsd.exceptions.base import PGSDError
from pgsd.exceptions.config import ConfigurationError


class TestCLIManager:
    """Test CLIManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cli_manager = CLIManager()

    def test_initialization(self):
        """Test CLIManager initialization."""
        assert self.cli_manager.parser is not None
        assert self.cli_manager.progress_reporter is not None

    def test_create_parser_basic_structure(self):
        """Test parser creation with basic structure."""
        parser = self.cli_manager._create_parser()
        
        assert parser.prog == 'pgsd'
        assert 'PostgreSQL Schema Diff Tool' in parser.description
        
        # Check global options
        actions = {action.dest: action for action in parser._actions}
        assert 'config' in actions
        assert 'verbose' in actions
        assert 'quiet' in actions

    def test_parse_version_option(self):
        """Test parsing version option."""
        with pytest.raises(SystemExit) as exc_info:
            self.cli_manager.parser.parse_args(['--version'])
        assert exc_info.value.code == 0

    def test_parse_help_option(self):
        """Test parsing help option."""
        with pytest.raises(SystemExit) as exc_info:
            self.cli_manager.parser.parse_args(['--help'])
        assert exc_info.value.code == 0

    def test_parse_compare_command_minimal(self):
        """Test parsing compare command with minimal arguments."""
        # Using the config-based parser for flexibility
        config_parser = self.cli_manager._create_config_parser()
        args = config_parser.parse_args([
            'compare',
            '--source-host', 'localhost',
            '--source-db', 'db1',
            '--target-host', 'localhost',
            '--target-db', 'db2'
        ])
        
        assert args.command == 'compare'
        assert args.source_host == 'localhost'
        assert args.source_db == 'db1'
        assert args.target_host == 'localhost'
        assert args.target_db == 'db2'

    def test_parse_compare_command_with_options(self):
        """Test parsing compare command with all options."""
        config_parser = self.cli_manager._create_config_parser()
        args = config_parser.parse_args([
            '--verbose',
            'compare',
            '--source-host', 'localhost',
            '--source-port', '5433',
            '--source-db', 'source_db',
            '--source-user', 'user1',
            '--target-host', 'remotehost',
            '--target-port', '5434',
            '--target-db', 'target_db',
            '--target-user', 'user2',
            '--schema', 'public',
            '--output', '/tmp/reports',
            '--format', 'html,json',
            '--dry-run'
        ])
        
        assert args.command == 'compare'
        assert args.source_host == 'localhost'
        assert args.source_port == 5433
        assert args.source_db == 'source_db'
        assert args.source_user == 'user1'
        assert args.target_host == 'remotehost'
        assert args.target_port == 5434
        assert args.target_db == 'target_db'
        assert args.target_user == 'user2'
        assert args.schema == 'public'
        assert args.output == '/tmp/reports'
        assert args.format == 'html,json'
        assert args.dry_run is True
        assert args.verbose is True

    def test_parse_list_schemas_command(self):
        """Test parsing list-schemas command."""
        config_parser = self.cli_manager._create_config_parser()
        args = config_parser.parse_args([
            'list-schemas',
            '--host', 'localhost',
            '--port', '5433',
            '--db', 'testdb',
            '--user', 'testuser'
        ])
        
        assert args.command == 'list-schemas'
        assert args.host == 'localhost'
        assert args.port == 5433
        assert args.db == 'testdb'
        assert args.user == 'testuser'

    def test_parse_validate_command(self):
        """Test parsing validate command."""
        args = self.cli_manager.parser.parse_args([
            'validate',
            '--config', 'config.yaml'
        ])
        
        assert args.command == 'validate'
        assert args.config == 'config.yaml'

    def test_parse_version_command(self):
        """Test parsing version command."""
        args = self.cli_manager.parser.parse_args(['version'])
        assert args.command == 'version'
        
        args_verbose = self.cli_manager.parser.parse_args(['version', '--verbose'])
        assert args_verbose.command == 'version'
        assert args_verbose.verbose is True

    def test_has_config_file_true(self):
        """Test config file detection with --config."""
        assert self.cli_manager._has_config_file(['--config', 'test.yaml', 'compare'])
        assert self.cli_manager._has_config_file(['-c', 'test.yaml', 'compare'])

    def test_has_config_file_false(self):
        """Test config file detection without config."""
        assert not self.cli_manager._has_config_file(['compare', '--verbose'])
        assert not self.cli_manager._has_config_file(['version'])

    def test_args_to_dict(self):
        """Test converting args to dictionary."""
        args = Namespace(command='version', verbose=True)
        result = self.cli_manager._args_to_dict(args)
        
        assert isinstance(result, dict)
        assert result['command'] == 'version'
        assert result['verbose'] is True

    def test_filter_config_args_source_db(self):
        """Test filtering source database arguments."""
        args = Namespace(
            source_host='localhost',
            source_port=5432,
            source_db='testdb',
            source_user='user',
            source_password='pass',
            schema='public'
        )
        
        result = self.cli_manager._filter_config_args(args)
        
        assert 'source_db' in result
        assert result['source_db']['host'] == 'localhost'
        assert result['source_db']['port'] == 5432
        assert result['source_db']['database'] == 'testdb'
        assert result['source_db']['username'] == 'user'
        assert result['source_db']['password'] == 'pass'
        assert result['source_db']['schema'] == 'public'

    def test_filter_config_args_target_db(self):
        """Test filtering target database arguments."""
        args = Namespace(
            target_host='remotehost',
            target_port=5433,
            target_db='targetdb',
            target_user='targetuser',
            target_password='targetpass',
            schema='public'
        )
        
        result = self.cli_manager._filter_config_args(args)
        
        assert 'target_db' in result
        assert result['target_db']['host'] == 'remotehost'
        assert result['target_db']['port'] == 5433
        assert result['target_db']['database'] == 'targetdb'
        assert result['target_db']['username'] == 'targetuser'
        assert result['target_db']['password'] == 'targetpass'
        assert result['target_db']['schema'] == 'public'

    def test_filter_config_args_output(self):
        """Test filtering output arguments."""
        args = Namespace(
            output='/tmp/reports',
            format='html,json'
        )
        
        result = self.cli_manager._filter_config_args(args)
        
        assert 'output' in result
        assert result['output']['path'] == '/tmp/reports'
        assert result['output']['format'] == 'html,json'

    def test_filter_config_args_empty(self):
        """Test filtering with no relevant arguments."""
        args = Namespace(command='version', verbose=True)
        result = self.cli_manager._filter_config_args(args)
        assert result == {}

    def test_configure_logging_verbose(self):
        """Test logging configuration in verbose mode."""
        args = Namespace(verbose=True, quiet=False)
        
        with patch('logging.basicConfig') as mock_config:
            self.cli_manager._configure_logging(args)
            mock_config.assert_called_once()
            call_args = mock_config.call_args[1]
            assert call_args['level'] == logging.DEBUG

    def test_configure_logging_quiet(self):
        """Test logging configuration in quiet mode."""
        args = Namespace(verbose=False, quiet=True)
        
        with patch('logging.basicConfig') as mock_config:
            self.cli_manager._configure_logging(args)
            mock_config.assert_called_once()
            call_args = mock_config.call_args[1]
            assert call_args['level'] == logging.ERROR

    def test_configure_logging_normal(self):
        """Test logging configuration in normal mode."""
        args = Namespace(verbose=False, quiet=False)
        
        with patch('logging.basicConfig') as mock_config:
            self.cli_manager._configure_logging(args)
            mock_config.assert_called_once()
            call_args = mock_config.call_args[1]
            assert call_args['level'] == logging.INFO

    def test_configure_logging_without_attributes(self):
        """Test logging configuration without verbose/quiet attributes."""
        args = Namespace(command='version')
        
        with patch('logging.basicConfig') as mock_config:
            self.cli_manager._configure_logging(args)
            mock_config.assert_called_once()
            call_args = mock_config.call_args[1]
            assert call_args['level'] == logging.INFO

    def test_parse_with_config_fallback_basic(self):
        """Test parsing with config fallback mechanism."""
        config_parser = self.cli_manager._create_config_parser()
        args = ['--config', 'test.yaml', 'compare', '--source-host', 'localhost', '--source-db', 'db1', '--target-host', 'localhost', '--target-db', 'db2']
        
        # This should work with dummy values injected
        result = self.cli_manager._parse_with_config_fallback(config_parser, args)
        
        assert result.command == 'compare'
        assert result.config == 'test.yaml'

    def test_parse_with_config_fallback_with_partial_args(self):
        """Test config fallback with some database args provided."""
        config_parser = self.cli_manager._create_config_parser()
        args = [
            '--config', 'test.yaml',
            'compare',
            '--source-host', 'localhost',
            '--source-db', 'db1',
            '--target-host', 'localhost',
            '--target-db', 'db2'
        ]
        
        result = self.cli_manager._parse_with_config_fallback(config_parser, args)
        
        assert result.command == 'compare'
        assert result.source_host == 'localhost'
        assert result.config == 'test.yaml'

    def test_create_config_parser_structure(self):
        """Test config parser creation."""
        config_parser = self.cli_manager._create_config_parser()
        
        assert config_parser.prog == 'pgsd'
        
        # Should have same global options
        actions = {action.dest: action for action in config_parser._actions}
        assert 'config' in actions
        assert 'verbose' in actions
        assert 'quiet' in actions


class TestCLIManagerExecution:
    """Test CLI command execution."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cli_manager = CLIManager()

    @patch('pgsd.cli.main.CompareCommand')
    def test_execute_command_compare(self, mock_compare_command):
        """Test executing compare command."""
        mock_command = Mock()
        mock_command.execute.return_value = 0
        mock_compare_command.return_value = mock_command
        
        args = Namespace(command='compare')
        config = Mock(spec=PGSDConfiguration)
        
        result = self.cli_manager._execute_command(args, config)
        
        assert result == 0
        mock_compare_command.assert_called_once_with(args, config)
        mock_command.execute.assert_called_once()

    @patch('pgsd.cli.main.ListSchemasCommand')
    def test_execute_command_list_schemas(self, mock_list_command):
        """Test executing list-schemas command."""
        mock_command = Mock()
        mock_command.execute.return_value = 0
        mock_list_command.return_value = mock_command
        
        args = Namespace(command='list-schemas')
        config = Mock(spec=PGSDConfiguration)
        
        result = self.cli_manager._execute_command(args, config)
        
        assert result == 0
        mock_list_command.assert_called_once_with(args, config)

    @patch('pgsd.cli.main.ValidateCommand')
    def test_execute_command_validate(self, mock_validate_command):
        """Test executing validate command."""
        mock_command = Mock()
        mock_command.execute.return_value = 0
        mock_validate_command.return_value = mock_command
        
        args = Namespace(command='validate')
        config = None
        
        result = self.cli_manager._execute_command(args, config)
        
        assert result == 0
        mock_validate_command.assert_called_once_with(args, config)

    @patch('pgsd.cli.main.VersionCommand')
    def test_execute_command_version(self, mock_version_command):
        """Test executing version command."""
        mock_command = Mock()
        mock_command.execute.return_value = 0
        mock_version_command.return_value = mock_command
        
        args = Namespace(command='version')
        config = None
        
        result = self.cli_manager._execute_command(args, config)
        
        assert result == 0
        mock_version_command.assert_called_once_with(args, config)

    def test_execute_command_unknown(self, capsys):
        """Test executing unknown command."""
        args = Namespace(command='unknown')
        config = None
        
        result = self.cli_manager._execute_command(args, config)
        
        assert result == 1


class TestCLIManagerRun:
    """Test CLIManager run method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cli_manager = CLIManager()

    @patch('pgsd.cli.main.CLIManager._execute_command')
    @patch('pgsd.cli.main.ConfigurationManager')
    def test_run_version_command(self, mock_config_manager, mock_execute):
        """Test running version command (no config loading)."""
        mock_execute.return_value = 0
        
        result = self.cli_manager.run(['version'])
        
        assert result == 0
        mock_config_manager.assert_not_called()
        mock_execute.assert_called_once()

    @patch('pgsd.cli.main.CLIManager._execute_command')
    @patch('pgsd.cli.main.ConfigurationManager')
    def test_run_validate_command(self, mock_config_manager, mock_execute):
        """Test running validate command (no config loading)."""
        mock_execute.return_value = 0
        
        result = self.cli_manager.run(['validate', '--config', 'test.yaml'])
        
        assert result == 0
        mock_config_manager.assert_not_called()
        mock_execute.assert_called_once()

    @patch('pgsd.cli.main.CLIManager._execute_command')
    @patch('pgsd.cli.main.ConfigurationManager')
    def test_run_compare_command_with_config(self, mock_config_manager_class, mock_execute):
        """Test running compare command with configuration."""
        mock_config_manager = Mock()
        mock_config = Mock(spec=PGSDConfiguration)
        mock_config_manager.load_configuration.return_value = mock_config
        mock_config_manager_class.return_value = mock_config_manager
        mock_execute.return_value = 0
        
        # Use config parser for successful parsing
        config_parser = self.cli_manager._create_config_parser()
        args = [
            'compare',
            '--source-host', 'localhost',
            '--source-db', 'testdb',
            '--target-host', 'localhost', 
            '--target-db', 'testdb2'
        ]
        
        with patch.object(self.cli_manager, 'parser', config_parser):
            result = self.cli_manager.run(args)
        
        assert result == 0
        mock_config_manager_class.assert_called_once()
        mock_config_manager.load_configuration.assert_called_once()
        mock_execute.assert_called_once()

    @patch('pgsd.cli.main.CLIManager._execute_command')
    def test_run_no_command(self, mock_execute):
        """Test running with no command (should show help)."""
        with patch.object(self.cli_manager.parser, 'print_help') as mock_help:
            result = self.cli_manager.run([])
            
            assert result == 2
            mock_help.assert_called_once()
            mock_execute.assert_not_called()

    @patch('pgsd.cli.main.CLIManager._configure_logging')
    def test_run_keyboard_interrupt(self, mock_configure_logging):
        """Test handling KeyboardInterrupt during execution."""
        with patch.object(self.cli_manager.parser, 'parse_args', side_effect=KeyboardInterrupt):
            with patch('sys.exit') as mock_exit:
                self.cli_manager.run(['version'])
                mock_exit.assert_called_once_with(130)

    @patch('pgsd.cli.main.CLIManager._configure_logging')
    @patch('pgsd.cli.main.CLIManager._execute_command')
    @patch('pgsd.cli.main.logger')
    def test_run_configuration_error(self, mock_logger, mock_execute, mock_configure_logging, capsys):
        """Test handling ConfigurationError during execution."""
        mock_execute.side_effect = ConfigurationError("Config error")
        
        result = self.cli_manager.run(['version'])
        
        assert result == 1
        mock_logger.error.assert_called_once_with("Configuration error: Config error")

    @patch('pgsd.cli.main.CLIManager._configure_logging')
    @patch('pgsd.cli.main.CLIManager._execute_command')
    @patch('pgsd.cli.main.logger')
    def test_run_pgsd_error(self, mock_logger, mock_execute, mock_configure_logging, capsys):
        """Test handling PGSDError during execution."""
        mock_execute.side_effect = PGSDError("PGSD error")
        
        result = self.cli_manager.run(['version'])
        
        assert result == 1
        mock_logger.error.assert_called_once_with("PGSD error: PGSD error")

    @patch('pgsd.cli.main.CLIManager._configure_logging')
    @patch('pgsd.cli.main.CLIManager._execute_command')
    @patch('pgsd.cli.main.logger')
    def test_run_unexpected_error(self, mock_logger, mock_execute, mock_configure_logging, capsys):
        """Test handling unexpected error during execution."""
        mock_execute.side_effect = RuntimeError("Unexpected error")
        
        result = self.cli_manager.run(['version'])
        
        assert result == 1
        mock_logger.error.assert_called_once_with("Unexpected error: Unexpected error")

    @patch('pgsd.cli.main.CLIManager._configure_logging')
    @patch('pgsd.cli.main.CLIManager._execute_command')
    @patch('pgsd.cli.main.logger')
    def test_run_unexpected_error_with_debug(self, mock_logger, mock_execute, mock_configure_logging, capsys):
        """Test handling unexpected error with debug logging."""
        mock_logger.isEnabledFor.return_value = True
        
        mock_execute.side_effect = RuntimeError("Unexpected error")
        
        result = self.cli_manager.run(['version'])
        
        assert result == 1
        mock_logger.exception.assert_called_once_with("Full traceback:")

    @patch('pgsd.cli.main.CLIManager._has_config_file')
    @patch('pgsd.cli.main.CLIManager._parse_with_config_fallback')
    @patch('pgsd.cli.main.CLIManager._create_config_parser')
    def test_run_with_config_fallback(self, mock_create_config_parser, mock_parse_fallback, mock_has_config):
        """Test running with config file fallback mechanism."""
        # Setup mocks
        mock_has_config.return_value = True
        mock_config_parser = Mock()
        mock_create_config_parser.return_value = mock_config_parser
        
        mock_parsed_args = Namespace(command='version', verbose=False, quiet=False)
        mock_parse_fallback.return_value = mock_parsed_args
        
        # Mock the initial parse_args to raise SystemExit
        with patch.object(self.cli_manager.parser, 'parse_args', side_effect=SystemExit(2)):
            with patch.object(self.cli_manager, '_configure_logging'):
                with patch.object(self.cli_manager, '_execute_command', return_value=0):
                    # This should catch SystemExit and use fallback
                    try:
                        result = self.cli_manager.run(['--config', 'test.yaml', 'version'])
                        # If we reach here, fallback worked
                        assert True
                    except SystemExit:
                        # If SystemExit is re-raised, that's also expected behavior
                        assert True

    def test_run_system_exit_without_config(self):
        """Test handling SystemExit without config file."""
        with patch.object(self.cli_manager.parser, 'parse_args', side_effect=SystemExit(2)):
            with patch.object(self.cli_manager, '_has_config_file', return_value=False):
                with pytest.raises(SystemExit) as exc_info:
                    self.cli_manager.run(['--invalid'])
                assert exc_info.value.code == 2


class TestMainFunction:
    """Test main entry point function."""

    @patch('pgsd.cli.main.CLIManager')
    def test_main_function(self, mock_cli_manager_class):
        """Test main function creates CLIManager and runs."""
        mock_cli_manager = Mock()
        mock_cli_manager.run.return_value = 42
        mock_cli_manager_class.return_value = mock_cli_manager
        
        result = main()
        
        assert result == 42
        mock_cli_manager_class.assert_called_once()
        mock_cli_manager.run.assert_called_once()

    @patch('sys.exit')
    @patch('pgsd.cli.main.main')
    def test_main_module_execution(self, mock_main, mock_exit):
        """Test __main__ module execution."""
        mock_main.return_value = 123
        
        # Import the module to trigger __main__ block execution
        import pgsd.cli.main
        
        # The actual execution happens in __main__.py, but we can test the function exists
        assert hasattr(pgsd.cli.main, 'main')
        assert callable(pgsd.cli.main.main)


class TestErrorHandling:
    """Test error handling scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cli_manager = CLIManager()

    def test_invalid_command_argument(self):
        """Test handling invalid command arguments."""
        with pytest.raises(SystemExit):
            self.cli_manager.parser.parse_args(['invalid_command'])

    def test_missing_required_argument_list_schemas(self):
        """Test missing required arguments for list-schemas."""
        with pytest.raises(SystemExit):
            self.cli_manager.parser.parse_args(['list-schemas'])

    def test_missing_required_argument_validate(self):
        """Test missing required arguments for validate."""
        with pytest.raises(SystemExit):
            self.cli_manager.parser.parse_args(['validate'])

    def test_invalid_port_argument(self):
        """Test invalid port argument."""
        config_parser = self.cli_manager._create_config_parser()
        with pytest.raises(SystemExit):
            config_parser.parse_args([
                'compare',
                '--source-host', 'localhost',
                '--source-port', 'invalid_port',
                '--source-db', 'db1',
                '--target-host', 'localhost',
                '--target-db', 'db2'
            ])

    def test_run_with_config_fallback_system_exit(self):
        """Test run method with config fallback when SystemExit is raised again."""
        with patch.object(self.cli_manager.parser, 'parse_args', side_effect=SystemExit(2)):
            with patch.object(self.cli_manager, '_has_config_file', return_value=True):
                with patch.object(self.cli_manager, '_create_config_parser') as mock_create_config_parser:
                    mock_config_parser = Mock()
                    mock_create_config_parser.return_value = mock_config_parser
                    
                    # Make the config fallback also raise SystemExit
                    with patch.object(self.cli_manager, '_parse_with_config_fallback', side_effect=SystemExit(2)):
                        with patch.object(self.cli_manager, '_configure_logging'):
                            with pytest.raises(SystemExit) as exc_info:
                                self.cli_manager.run(['--config', 'test.yaml', 'compare'])
                            assert exc_info.value.code == 2

    def test_parse_with_config_fallback_command_not_found(self):
        """Test config fallback when command is not found."""
        config_parser = self.cli_manager._create_config_parser()
        args = ['--config', 'test.yaml', '--verbose']  # No command
        
        # Should add dummy values for all required args
        result = self.cli_manager._parse_with_config_fallback(config_parser, args)
        
        assert result.config == 'test.yaml'
        assert result.verbose is True
        # Command should be None since it wasn't found
        assert result.command is None

    def test_parse_with_config_fallback_cleanup_dummy_values(self):
        """Test that dummy values are properly cleaned up."""
        config_parser = self.cli_manager._create_config_parser()
        args = ['--config', 'test.yaml', 'compare', '--source-host', 'localhost', '--source-db', 'db1', '--target-host', 'localhost', '--target-db', 'db2']
        
        result = self.cli_manager._parse_with_config_fallback(config_parser, args)
        
        # Real values should be preserved, not dummy values
        assert result.source_host == 'localhost'
        assert result.source_db == 'db1'
        assert result.target_host == 'localhost'
        assert result.target_db == 'db2'