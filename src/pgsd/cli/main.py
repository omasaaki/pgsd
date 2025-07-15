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
        
        # Source database options
        source_group = compare_parser.add_argument_group('Source Database')
        source_group.add_argument(
            '--source-host',
            required=True,
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
            required=True,
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
        
        # Target database options
        target_group = compare_parser.add_argument_group('Target Database')
        target_group.add_argument(
            '--target-host',
            required=True,
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
            required=True,
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
            help='Schema to compare (default: public)'
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
        subparsers.add_parser(
            'version',
            help='Show version information',
            description='''
Show PGSD version, build information, and supported PostgreSQL versions.

Examples:
  pgsd version
            ''',
            epilog='Useful for troubleshooting and bug reports.'
        )

    def run(self, args: Optional[List[str]] = None) -> int:
        """Run CLI with given arguments.
        
        Args:
            args: Command line arguments (defaults to sys.argv[1:])
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            # Parse arguments
            parsed_args = self.parser.parse_args(args)
            
            # Configure logging
            self._configure_logging(parsed_args)
            
            # Check if command was provided
            if not hasattr(parsed_args, 'command') or parsed_args.command is None:
                self.parser.print_help()
                return 2
            
            # Load configuration (skip for version command)
            if parsed_args.command == 'version':
                config = None
            else:
                config_manager = ConfigurationManager(parsed_args.config)
                cli_args = self._args_to_dict(parsed_args)
                config = config_manager.load_configuration(cli_args)
            
            # Execute command
            return self._execute_command(parsed_args, config)
            
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