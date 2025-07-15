"""Command implementations for PGSD CLI.

This module contains the implementation of individual CLI commands including
compare, list-schemas, validate, and version commands.
"""

import logging
from abc import ABC, abstractmethod
from argparse import Namespace
from pathlib import Path
from typing import List

from ..config.schema import PGSDConfiguration, DatabaseConfig, OutputFormat
from ..core.engine import SchemaComparisonEngine
from ..database.manager import DatabaseManager
from ..reports import create_reporter, ReportFormat
from ..exceptions.base import PGSDError
from ..exceptions.database import DatabaseConnectionError
from ..exceptions.config import ConfigurationError
from .progress import ProgressReporter


logger = logging.getLogger(__name__)


class BaseCommand(ABC):
    """Base class for CLI commands."""

    def __init__(self, args: Namespace, config: PGSDConfiguration):
        """Initialize command.
        
        Args:
            args: Parsed command line arguments
            config: Application configuration
        """
        self.args = args
        self.config = config
        self.progress_reporter = ProgressReporter()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def execute(self) -> int:
        """Execute the command.
        
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        pass


class CompareCommand(BaseCommand):
    """Command to compare schemas between two databases."""

    def execute(self) -> int:
        """Execute schema comparison.
        
        Returns:
            Exit code
        """
        try:
            self.logger.info("Starting schema comparison")
            
            # Validate arguments
            self._validate_arguments()
            
            if self.args.dry_run:
                self._show_dry_run_info()
                return 0
            
            # Create database configurations
            source_config = self._create_source_db_config()
            target_config = self._create_target_db_config()
            
            # Initialize core engine
            self.progress_reporter.show_progress("Initializing engine", 10)
            from ..config.schema import PGSDConfiguration
            config = PGSDConfiguration(
                source_db=source_config,
                target_db=target_config
            )
            engine = SchemaComparisonEngine(config)
            
            # Perform schema analysis
            self.progress_reporter.show_progress("Analyzing schemas", 30)
            import asyncio
            
            async def run_comparison():
                await engine.initialize()
                return await engine.compare_schemas(
                    source_schema=self.args.schema,
                    target_schema=self.args.schema
                )
            
            diff_result = asyncio.run(run_comparison())
            
            # Generate reports
            self.progress_reporter.show_progress("Generating reports", 70)
            output_paths = self._generate_reports(diff_result)
            
            # Show results
            self.progress_reporter.show_progress("Complete", 100)
            self._show_results(diff_result, output_paths)
            
            self.logger.info("Schema comparison completed successfully")
            return 0
            
        except Exception as e:
            self.logger.error(f"Schema comparison failed: {e}")
            return 1

    def _validate_arguments(self) -> None:
        """Validate command arguments."""
        if not self.args.source_db:
            raise ValueError("Source database is required")
        if not self.args.target_db:
            raise ValueError("Target database is required")

    def _show_dry_run_info(self) -> None:
        """Show dry run information."""
        print("DRY RUN MODE - No actual comparison will be performed")
        print(f"Source: {self.args.source_host}:{self.args.source_port}/{self.args.source_db}")
        print(f"Target: {self.args.target_host}:{self.args.target_port}/{self.args.target_db}")
        print(f"Schema: {self.args.schema}")
        print(f"Output: {self.args.output}")
        print(f"Format: {self.args.format}")

    def _create_source_db_config(self) -> DatabaseConfig:
        """Create source database configuration."""
        return DatabaseConfig(
            host=self.args.source_host,
            port=self.args.source_port,
            database=self.args.source_db,
            username=getattr(self.args, 'source_user', '') or '',
            password=getattr(self.args, 'source_password', '') or '',
            schema=self.args.schema
        )

    def _create_target_db_config(self) -> DatabaseConfig:
        """Create target database configuration."""
        return DatabaseConfig(
            host=self.args.target_host,
            port=self.args.target_port,
            database=self.args.target_db,
            username=getattr(self.args, 'target_user', '') or '',
            password=getattr(self.args, 'target_password', '') or '',
            schema=self.args.schema
        )

    def _generate_reports(self, diff_result) -> List[Path]:
        """Generate reports in specified formats.
        
        Args:
            diff_result: Schema comparison results
            
        Returns:
            List of generated report file paths
        """
        output_paths = []
        output_dir = Path(self.args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Parse format string
        formats = [f.strip().lower() for f in self.args.format.split(',')]
        
        for format_str in formats:
            try:
                # Map format string to ReportFormat enum
                format_map = {
                    'html': ReportFormat.HTML,
                    'markdown': ReportFormat.MARKDOWN,
                    'json': ReportFormat.JSON,
                    'xml': ReportFormat.XML,
                }
                
                report_format = format_map.get(format_str)
                if not report_format:
                    self.logger.warning(f"Unknown format: {format_str}")
                    continue
                
                # Create reporter and generate report
                reporter = create_reporter(report_format)
                output_path = reporter.generate_report(diff_result, output_dir)
                output_paths.append(output_path)
                
                self.logger.info(f"Generated {format_str} report: {output_path}")
                
            except Exception as e:
                self.logger.error(f"Failed to generate {format_str} report: {e}")
        
        return output_paths

    def _show_results(self, diff_result, output_paths: List[Path]) -> None:
        """Show comparison results summary.
        
        Args:
            diff_result: Schema comparison results
            output_paths: Generated report file paths
        """
        # Show summary
        summary = diff_result.summary
        total_changes = summary.get('total_changes', 0)
        
        print(f"\nSchema Comparison Results:")
        print(f"Total Changes: {total_changes}")
        
        if hasattr(diff_result, 'tables'):
            tables_added = len(diff_result.tables.get('added', []))
            tables_removed = len(diff_result.tables.get('removed', []))
            tables_modified = len(diff_result.tables.get('modified', []))
            print(f"Tables: +{tables_added} -{tables_removed} ~{tables_modified}")
        
        # Show generated reports
        if output_paths:
            print(f"\nGenerated Reports:")
            for path in output_paths:
                print(f"  {path}")
        else:
            print("\nNo reports were generated")


class ListSchemasCommand(BaseCommand):
    """Command to list available schemas in a database."""

    def execute(self) -> int:
        """Execute schema listing.
        
        Returns:
            Exit code
        """
        try:
            self.logger.info("Listing database schemas")
            
            # Create database configuration
            db_config = self._create_db_config()
            
            # Connect to database and list schemas
            db_manager = DatabaseManager(db_config)
            schemas = db_manager.list_schemas()
            
            # Display results
            print(f"Available schemas in {self.args.host}:{self.args.port}/{self.args.db}:")
            for schema in schemas:
                print(f"  {schema}")
            
            self.logger.info(f"Found {len(schemas)} schemas")
            return 0
            
        except DatabaseConnectionError as e:
            self.logger.error(f"Database connection failed: {e}")
            return 1
        except Exception as e:
            self.logger.error(f"Failed to list schemas: {e}")
            return 1

    def _create_db_config(self) -> DatabaseConfig:
        """Create database configuration."""
        return DatabaseConfig(
            host=self.args.host,
            port=self.args.port,
            database=self.args.db,
            username=getattr(self.args, 'user', '') or '',
            password=getattr(self.args, 'password', '') or ''
        )


class ValidateCommand(BaseCommand):
    """Command to validate configuration file."""

    def execute(self) -> int:
        """Execute configuration validation.
        
        Returns:
            Exit code
        """
        try:
            self.logger.info(f"Validating configuration file: {self.args.config}")
            
            from ..config.manager import ConfigurationManager
            
            # Load and validate configuration
            config_manager = ConfigurationManager(self.args.config)
            config = config_manager.load_configuration()
            
            print(f"Configuration file '{self.args.config}' is valid")
            
            # Show configuration summary
            print("\nConfiguration Summary:")
            if hasattr(config, 'source_db'):
                print(f"Source Database: {config.source_db.host}:{config.source_db.port}")
            if hasattr(config, 'target_db'):
                print(f"Target Database: {config.target_db.host}:{config.target_db.port}")
            
            self.logger.info("Configuration validation completed")
            return 0
            
        except ConfigurationError as e:
            self.logger.error(f"Configuration validation failed: {e}")
            print(f"Configuration file '{self.args.config}' is invalid: {e}")
            return 1
        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            return 1


class VersionCommand(BaseCommand):
    """Command to display version information."""

    def execute(self) -> int:
        """Execute version display.
        
        Returns:
            Exit code
        """
        try:
            from .. import __version__
            
            print(f"PGSD (PostgreSQL Schema Diff) {__version__}")
            print("Copyright (c) 2025 PGSD Development Team")
            print("License: MIT")
            print("Repository: https://github.com/omasaaki/pgsd")
            
            # Show additional version info
            import sys
            import platform
            
            print(f"\nRuntime Information:")
            print(f"Python: {sys.version}")
            print(f"Platform: {platform.platform()}")
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Failed to display version: {e}")
            return 1