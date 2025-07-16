"""Main CLI interface for PGSD.

This module provides the primary command-line interface for the PostgreSQL
Schema Diff tool, including argument parsing and command routing.
"""

import sys
import logging
from argparse import ArgumentParser, Namespace
from typing import List, Optional, Dict, Any

from ..config.manager import ConfigurationManager
from ..config.schema import PGSDConfiguration, OutputFormat
from .commands import CompareCommand, ListSchemasCommand, ValidateCommand, VersionCommand
from .progress import ProgressReporter
from ..exceptions.base import PGSDError
from ..exceptions.config import ConfigurationError


logger = logging.getLogger(__name__)


class CLIManager:
    """Main CLI interface manager.
    
    Handles argument parsing, configuration loading, and command execution
    for the PostgreSQL Schema Diff tool.
    """

    def __init__(self):
        """Initialize CLI manager."""
        self.parser = self._create_parser()
        self.progress_reporter = ProgressReporter()

    def _create_parser(self) -> ArgumentParser:
        """Create and configure argument parser.
        
        Returns:
            Configured ArgumentParser instance
        """
        parser = ArgumentParser(
            prog='pgsd',
            description='PostgreSQL Schema Diff Tool',
            epilog='For more information, visit: https://github.com/omasaaki/pgsd'
        )
        
        # Global options
        parser.add_argument(
            '--version',
            action='version',
            version='%(prog)s 1.0.0'
        )
        
        parser.add_argument(
            '--config', '-c',
            type=str,
            help='Configuration file path'
        )
        
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose output'
        )
        
        parser.add_argument(
            '--quiet', '-q',
            action='store_true',
            help='Suppress non-error output'
        )
        
        # Create subparsers
        subparsers = parser.add_subparsers(
            dest='command',
            help='Available commands',
            metavar='COMMAND'
        )
        
        self._add_compare_parser(subparsers)
        self._add_list_schemas_parser(subparsers)
        self._add_validate_parser(subparsers)
        self._add_version_parser(subparsers)
        
        return parser

    def _add_compare_parser(self, subparsers):
        """Add compare command parser."""
        compare_parser = subparsers.add_parser(
            'compare',
            help='Compare schemas between two databases',
            description='''
Compare PostgreSQL schemas between two databases and generate a detailed report.

Examples:
  pgsd compare --source-host localhost --source-db db1 --target-host localhost --target-db db2
  pgsd compare --config config.yaml --schema public --format html
  pgsd compare --source-host prod.example.com --source-db prod --target-host staging.example.com --target-db staging --output ./reports
            ''',
            epilog='For more examples, see: https://github.com/omasaaki/pgsd/blob/main/docs/EXAMPLES.md'
        )
        
        # Source database options (made optional for config file compatibility)
        source_group = compare_parser.add_argument_group('Source Database')
        source_group.add_argument(
            '--source-host',
            help='Source database host'
        )
        source_group.add_argument(
            '--source-port',
            type=int,
            default=5432,
            help='Source database port (default: 5432)'
        )
        source_group.add_argument(
            '--source-db',
            help='Source database name'
        )
        source_group.add_argument(
            '--source-user',
            help='Source database username'
        )
        source_group.add_argument(
            '--source-password',
            help='Source database password'
        )
        
        # Target database options (made optional for config file compatibility)
        target_group = compare_parser.add_argument_group('Target Database')
        target_group.add_argument(
            '--target-host',
            help='Target database host'
        )
        target_group.add_argument(
            '--target-port',
            type=int,
            default=5432,
            help='Target database port (default: 5432)'
        )
        target_group.add_argument(
            '--target-db',
            help='Target database name'
        )
        target_group.add_argument(
            '--target-user',
            help='Target database username'
        )
        target_group.add_argument(
            '--target-password',
            help='Target database password'
        )
        
        # Comparison options
        compare_group = compare_parser.add_argument_group('Comparison Options')
        compare_group.add_argument(
            '--schema',
            default='public',
            help='Schema to compare for both databases (default: public)'
        )
        compare_group.add_argument(
            '--source-schema',
            help='Source database schema name (overrides --schema for source)'
        )
        compare_group.add_argument(
            '--target-schema',
            help='Target database schema name (overrides --schema for target)'
        )
        compare_group.add_argument(
            '--output', '-o',
            default='./reports',
            help='Output directory for reports (default: ./reports)'
        )
        compare_group.add_argument(
            '--format', '-f',
            default='html',
            help='Report format: html,markdown,json,xml (default: html)'
        )
        compare_group.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without executing'
        )

    def _add_list_schemas_parser(self, subparsers):
        """Add list-schemas command parser."""
        list_parser = subparsers.add_parser(
            'list-schemas',
            help='List available schemas in a database',
            description='''
List all schemas available in a PostgreSQL database.

Examples:
  pgsd list-schemas --host localhost --db mydb --user postgres
  pgsd list-schemas --host prod.example.com --db maindb
            ''',
            epilog='Use this to discover available schemas before comparison.'
        )
        
        list_parser.add_argument(
            '--host',
            required=True,
            help='Database host'
        )
        list_parser.add_argument(
            '--port',
            type=int,
            default=5432,
            help='Database port (default: 5432)'
        )
        list_parser.add_argument(
            '--db',
            required=True,
            help='Database name'
        )
        list_parser.add_argument(
            '--user',
            help='Database username'
        )
        list_parser.add_argument(
            '--password',
            help='Database password'
        )

    def _add_validate_parser(self, subparsers):
        """Add validate command parser."""
        validate_parser = subparsers.add_parser(
            'validate',
            help='Validate configuration file',
            description='''
Validate a PGSD configuration file for syntax and content errors.

Examples:
  pgsd validate --config config.yaml
  pgsd validate --config /etc/pgsd/production.yml
            ''',
            epilog='Returns exit code 0 for valid config, 1 for errors.'
        )
        
        validate_parser.add_argument(
            '--config', '-c',
            required=True,
            help='Configuration file to validate'
        )

    def _add_version_parser(self, subparsers):
        """Add version command parser."""
        version_parser = subparsers.add_parser(
            'version',
            help='Show version information',
            description='''
Show PGSD version, build information, and supported PostgreSQL versions.

Examples:
  pgsd version
  pgsd version --verbose
            ''',
            epilog='Useful for troubleshooting and bug reports.'
        )
        
        version_parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Show detailed version information'
        )

    def run(self, args: Optional[List[str]] = None) -> int:
        """Run CLI with given arguments.
        
        Args:
            args: Command line arguments (defaults to sys.argv[1:])
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            # Simple approach: try normal parsing first, then fallback if needed
            parsed_args = self.parser.parse_args(args)
            
            # Configure logging
            self._configure_logging(parsed_args)
            
            # Check if command was provided
            if not hasattr(parsed_args, 'command') or parsed_args.command is None:
                self.parser.print_help()
                return 2
            
            # Load configuration (skip for version and validate commands)
            if parsed_args.command in ('version', 'validate'):
                config = None
            else:
                config_manager = ConfigurationManager(getattr(parsed_args, 'config', None))
                cli_args = self._filter_config_args(parsed_args)
                config = config_manager.load_configuration(cli_args)
            
            # Execute command
            return self._execute_command(parsed_args, config)
        except SystemExit as e:
            # If we get a SystemExit during parsing, check if we have config file
            actual_args = args if args is not None else sys.argv[1:]
            if self._has_config_file(actual_args):
                try:
                    # Create a config-friendly parser and try again
                    config_parser = self._create_config_parser()
                    parsed_args = self._parse_with_config_fallback(config_parser, actual_args)
                    self._configure_logging(parsed_args)
                except SystemExit:
                    # Re-raise the original SystemExit
                    raise e
            else:
                # Re-raise the SystemExit if no config file
                raise
            
        except KeyboardInterrupt:
            logger.info("Operation cancelled by user")
            sys.exit(130)  # 128 + SIGINT
        except ConfigurationError as e:
            logger.error(f"Configuration error: {e}")
            return 1
        except PGSDError as e:
            logger.error(f"PGSD error: {e}")
            return 1
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            if logger.isEnabledFor(logging.DEBUG):
                logger.exception("Full traceback:")
            return 1

    def _has_config_file(self, args: List[str]) -> bool:
        """Check if config file is specified in arguments.
        
        Args:
            args: Command line arguments
            
        Returns:
            True if config file is specified
        """
        return '--config' in args or '-c' in args

    def _parse_with_config_fallback(self, parser: ArgumentParser, args: List[str]) -> Namespace:
        """Parse arguments with config file support.
        
        Args:
            parser: Parser with optional database arguments
            args: Command line arguments
            
        Returns:
            Parsed arguments namespace
        """
        # Add dummy values for required arguments if missing
        args_copy = list(args)
        
        # Find the command position
        command_idx = None
        for i, arg in enumerate(args_copy):
            if arg in ['compare', 'list-schemas', 'validate', 'version']:
                command_idx = i
                break
        
        if command_idx is not None:
            # Insert dummy values before the command if not already present
            required_args = ['--source-host', '--source-db', '--target-host', '--target-db']
            dummy_args = []
            
            for req_arg in required_args:
                if req_arg not in args_copy:
                    dummy_args.extend([req_arg, 'from_config'])
            
            if dummy_args:
                args_copy = args_copy[:command_idx] + dummy_args + args_copy[command_idx:]
        
        # Parse with the config-friendly parser
        parsed_args = parser.parse_args(args_copy)
        
        # Clean up dummy values
        dummy_value = 'from_config'
        for attr in ['source_host', 'source_db', 'target_host', 'target_db']:
            if hasattr(parsed_args, attr) and getattr(parsed_args, attr) == dummy_value:
                setattr(parsed_args, attr, None)
        
        return parsed_args


    def _create_config_parser(self) -> ArgumentParser:
        """Create parser for when config file is present.
        
        Returns:
            Parser with optional database arguments
        """
        # Create a new parser similar to the original but with optional database args
        parser = ArgumentParser(
            prog='pgsd',
            description='PostgreSQL Schema Diff Tool',
            epilog='For more information, visit: https://github.com/omasaaki/pgsd'
        )
        
        # Add global options
        parser.add_argument(
            '--version',
            action='version',
            version='%(prog)s 1.0.0'
        )
        
        parser.add_argument(
            '--config', '-c',
            type=str,
            help='Configuration file path'
        )
        
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose output'
        )
        
        parser.add_argument(
            '--quiet', '-q',
            action='store_true',
            help='Suppress non-error output'
        )
        
        # Create subparsers
        subparsers = parser.add_subparsers(
            dest='command',
            help='Available commands',
            metavar='COMMAND'
        )
        
        # Add compare command with optional database arguments
        self._add_compare_parser_optional(subparsers)
        self._add_list_schemas_parser(subparsers)
        self._add_validate_parser(subparsers)
        self._add_version_parser(subparsers)
        
        return parser

    def _add_compare_parser_optional(self, subparsers):
        """Add compare command parser with optional database arguments."""
        compare_parser = subparsers.add_parser(
            'compare',
            help='Compare schemas between two databases',
            description='''
Compare PostgreSQL schemas between two databases and generate a detailed report.

Examples:
  pgsd compare --source-host localhost --source-db db1 --target-host localhost --target-db db2
  pgsd compare --config config.yaml --schema public --format html
  pgsd compare --source-host prod.example.com --source-db prod --target-host staging.example.com --target-db staging --output ./reports
            ''',
            epilog='For more examples, see: https://github.com/omasaaki/pgsd/blob/main/docs/EXAMPLES.md'
        )
        
        # Source database options (all optional)
        source_group = compare_parser.add_argument_group('Source Database')
        source_group.add_argument(
            '--source-host',
            help='Source database host'
        )
        source_group.add_argument(
            '--source-port',
            type=int,
            default=5432,
            help='Source database port (default: 5432)'
        )
        source_group.add_argument(
            '--source-db',
            help='Source database name'
        )
        source_group.add_argument(
            '--source-user',
            help='Source database username'
        )
        source_group.add_argument(
            '--source-password',
            help='Source database password'
        )
        
        # Target database options (all optional)
        target_group = compare_parser.add_argument_group('Target Database')
        target_group.add_argument(
            '--target-host',
            help='Target database host'
        )
        target_group.add_argument(
            '--target-port',
            type=int,
            default=5432,
            help='Target database port (default: 5432)'
        )
        target_group.add_argument(
            '--target-db',
            help='Target database name'
        )
        target_group.add_argument(
            '--target-user',
            help='Target database username'
        )
        target_group.add_argument(
            '--target-password',
            help='Target database password'
        )
        
        # Comparison options
        compare_group = compare_parser.add_argument_group('Comparison Options')
        compare_group.add_argument(
            '--schema',
            default='public',
            help='Schema to compare for both databases (default: public)'
        )
        compare_group.add_argument(
            '--source-schema',
            help='Source database schema name (overrides --schema for source)'
        )
        compare_group.add_argument(
            '--target-schema',
            help='Target database schema name (overrides --schema for target)'
        )
        compare_group.add_argument(
            '--output', '-o',
            default='./reports',
            help='Output directory for reports (default: ./reports)'
        )
        compare_group.add_argument(
            '--format', '-f',
            default='html',
            help='Report format: html,markdown,json,xml (default: html)'
        )
        compare_group.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without executing'
        )

    def _configure_logging(self, args: Namespace) -> None:
        """Configure logging based on CLI arguments.
        
        Args:
            args: Parsed command line arguments
        """
        if hasattr(args, 'verbose') and args.verbose:
            log_level = logging.DEBUG
        elif hasattr(args, 'quiet') and args.quiet:
            log_level = logging.ERROR
        else:
            log_level = logging.INFO
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def _args_to_dict(self, args: Namespace) -> Dict[str, Any]:
        """Convert parsed arguments to dictionary.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            Dictionary representation of arguments
        """
        return vars(args)

    def _filter_config_args(self, args: Namespace) -> Dict[str, Any]:
        """Filter CLI arguments to only include configuration-related ones.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            Dictionary with only configuration-related arguments
        """
        # CLI引数から設定に関連するものをフィルタリング
        # 現在、設定ファイルから設定を読み込んでいるので、CLI引数はオーバーライドとして機能する
        config_args = {}
        
        # データベース接続関連の引数
        if hasattr(args, 'source_host') and args.source_host:
            config_args.setdefault('source_db', {})['host'] = args.source_host
        if hasattr(args, 'source_port') and args.source_port:
            config_args.setdefault('source_db', {})['port'] = args.source_port
        if hasattr(args, 'source_db') and args.source_db:
            config_args.setdefault('source_db', {})['database'] = args.source_db
        if hasattr(args, 'source_user') and args.source_user:
            config_args.setdefault('source_db', {})['username'] = args.source_user
        if hasattr(args, 'source_password') and args.source_password:
            config_args.setdefault('source_db', {})['password'] = args.source_password
        if hasattr(args, 'schema') and args.schema:
            config_args.setdefault('source_db', {})['schema'] = args.schema
            
        if hasattr(args, 'target_host') and args.target_host:
            config_args.setdefault('target_db', {})['host'] = args.target_host
        if hasattr(args, 'target_port') and args.target_port:
            config_args.setdefault('target_db', {})['port'] = args.target_port
        if hasattr(args, 'target_db') and args.target_db:
            config_args.setdefault('target_db', {})['database'] = args.target_db
        if hasattr(args, 'target_user') and args.target_user:
            config_args.setdefault('target_db', {})['username'] = args.target_user
        if hasattr(args, 'target_password') and args.target_password:
            config_args.setdefault('target_db', {})['password'] = args.target_password
        if hasattr(args, 'schema') and args.schema:
            config_args.setdefault('target_db', {})['schema'] = args.schema
            
        # 出力関連の引数
        if hasattr(args, 'output') and args.output:
            config_args.setdefault('output', {})['path'] = args.output
        if hasattr(args, 'format') and args.format:
            config_args.setdefault('output', {})['format'] = args.format
            
        return config_args

    def _execute_command(self, args: Namespace, config: Optional[PGSDConfiguration]) -> int:
        """Execute the specified command.
        
        Args:
            args: Parsed command line arguments
            config: Loaded configuration
            
        Returns:
            Exit code from command execution
        """
        command_map = {
            'compare': CompareCommand,
            'list-schemas': ListSchemasCommand,
            'validate': ValidateCommand,
            'version': VersionCommand,
        }
        
        command_class = command_map.get(args.command)
        if not command_class:
            logger.error(f"Unknown command: {args.command}")
            return 1
        
        command = command_class(args, config)
        return command.execute()


def main() -> int:
    """Main entry point for CLI.
    
    Returns:
        Exit code
    """
    cli_manager = CLIManager()
    return cli_manager.run()


if __name__ == '__main__':
    sys.exit(main())