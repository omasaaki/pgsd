"""Core schema comparison engine for PGSD application.

This module provides the main engine that orchestrates the entire schema
comparison process by integrating all components:
- Database connection management
- Schema information collection
- Difference analysis
- Result processing

Usage:
    from pgsd.core import SchemaComparisonEngine
    from pgsd.config import ConfigurationManager

    # Initialize engine
    config = ConfigurationManager().load_configuration()
    engine = SchemaComparisonEngine(config)

    # Perform comparison
    result = await engine.compare_schemas(
        source_schema="public",
        target_schema="public"
    )

    # Access results
    print(f"Total changes: {result.summary['total_changes']}")
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from ..config.manager import ConfigurationManager
from ..database import DatabaseManager
from ..schema import SchemaInformationCollector
from ..exceptions.database import DatabaseConnectionError
from ..exceptions.processing import ProcessingError
from .analyzer import DiffAnalyzer, DiffResult


logger = logging.getLogger(__name__)


class SchemaComparisonEngine:
    """Main engine for PostgreSQL schema comparison operations.

    This class orchestrates the entire schema comparison workflow by coordinating
    database connections, schema information collection, and difference analysis.

    Attributes:
        config (ConfigManager): Configuration manager instance
        database_manager (DatabaseManager): Database connection manager
        schema_collector (SchemaInformationCollector): Schema information collector
        diff_analyzer (DiffAnalyzer): Difference analysis engine
    """

    def __init__(self, config: ConfigurationManager):
        """Initialize the schema comparison engine.

        Args:
            config: Configuration manager instance with database and analysis settings

        Raises:
            PGSDError: If initialization fails
        """
        self.config = config
        self.database_manager: Optional[DatabaseManager] = None
        self.schema_collector: Optional[SchemaInformationCollector] = None
        self.diff_analyzer = DiffAnalyzer()
        self._initialized = False

        logger.info("Schema comparison engine initialized")

    async def initialize(self) -> None:
        """Initialize database connections and collectors.

        This method sets up all required components for schema comparison.
        Must be called before performing any comparison operations.

        Raises:
            DatabaseConnectionError: If database initialization fails
            ProcessingError: If collector initialization fails
        """
        try:
            logger.info("Initializing schema comparison engine components")

            # Initialize database manager
            self.database_manager = DatabaseManager(self.config)
            await self.database_manager.initialize()
            logger.debug("Database manager initialized successfully")

            # Initialize schema collector
            self.schema_collector = SchemaInformationCollector(self.database_manager)
            logger.debug("Schema collector initialized successfully")

            self._initialized = True
            logger.info("Schema comparison engine initialization completed")

        except Exception as e:
            logger.error(f"Failed to initialize schema comparison engine: {e}")
            await self.cleanup()
            if isinstance(e, (DatabaseConnectionError, ProcessingError)):
                raise
            raise ProcessingError(f"Engine initialization failed: {str(e)}")

    async def compare_schemas(
        self,
        source_schema: str,
        target_schema: str,
        source_database: str = "source",
        target_database: str = "target",
    ) -> DiffResult:
        """Compare two PostgreSQL schemas and return differences.

        This is the main method that orchestrates the entire comparison process:
        1. Validates inputs and engine state
        2. Collects schema information from both databases
        3. Performs difference analysis
        4. Returns comprehensive comparison results

        Args:
            source_schema: Name of the source schema to compare
            target_schema: Name of the target schema to compare
            source_database: Database identifier for source (default: "source")
            target_database: Database identifier for target (default: "target")

        Returns:
            DiffResult: Comprehensive comparison results with all detected differences

        Raises:
            ProcessingError: If engine not initialized or comparison fails
            DatabaseConnectionError: If database operations fail
        """
        if not self._initialized:
            raise ProcessingError("Engine not initialized. Call initialize() first.")

        logger.info(
            f"Starting schema comparison: {source_database}.{source_schema} -> "
            f"{target_database}.{target_schema}"
        )

        try:
            # Collect source schema information
            logger.debug(f"Collecting source schema information: {source_schema}")
            source_info = await self.schema_collector.collect_schema_info(
                schema_name=source_schema, database_type=source_database
            )
            logger.info(
                f"Source schema collected: {len(source_info.tables)} tables, "
                f"{len(source_info.views)} views, "
                f"{len(source_info.functions)} functions"
            )

            # Collect target schema information
            logger.debug(f"Collecting target schema information: {target_schema}")
            target_info = await self.schema_collector.collect_schema_info(
                schema_name=target_schema, database_type=target_database
            )
            logger.info(
                f"Target schema collected: {len(target_info.tables)} tables, "
                f"{len(target_info.views)} views, "
                f"{len(target_info.functions)} functions"
            )

            # Perform difference analysis
            logger.debug("Starting difference analysis")
            start_time = datetime.now()
            diff_result = self.diff_analyzer.analyze(source_info, target_info)
            analysis_time = (datetime.now() - start_time).total_seconds()

            logger.info(
                f"Difference analysis completed in {analysis_time:.3f}s. "
                f"Total changes detected: {diff_result.summary['total_changes']}"
            )

            # Add metadata to result
            diff_result.metadata = {
                "source_database": source_database,
                "target_database": target_database,
                "source_schema": source_schema,
                "target_schema": target_schema,
                "analysis_time_seconds": analysis_time,
                "comparison_timestamp": datetime.now().isoformat(),
            }

            return diff_result

        except Exception as e:
            logger.error(f"Schema comparison failed: {e}")
            if isinstance(e, (DatabaseConnectionError, ProcessingError)):
                raise
            raise ProcessingError(f"Schema comparison failed: {str(e)}")

    async def get_available_schemas(self, database_type: str = "source") -> list[str]:
        """Get list of available schemas in specified database.

        Args:
            database_type: Database identifier ("source" or "target")

        Returns:
            List of schema names available in the database

        Raises:
            ProcessingError: If engine not initialized
            DatabaseConnectionError: If database operations fail
        """
        if not self._initialized:
            raise ProcessingError("Engine not initialized. Call initialize() first.")

        try:
            logger.debug(f"Retrieving available schemas from {database_type} database")
            schemas = await self.schema_collector.get_available_schemas(database_type)
            logger.info(f"Found {len(schemas)} schemas in {database_type} database")
            return schemas

        except Exception as e:
            logger.error(f"Failed to get available schemas: {e}")
            if isinstance(e, DatabaseConnectionError):
                raise
            raise ProcessingError(f"Failed to get schemas: {str(e)}")

    async def validate_schema_exists(
        self, schema_name: str, database_type: str = "source"
    ) -> bool:
        """Validate that a schema exists in the specified database.

        Args:
            schema_name: Name of the schema to validate
            database_type: Database identifier ("source" or "target")

        Returns:
            True if schema exists, False otherwise

        Raises:
            ProcessingError: If engine not initialized
            DatabaseConnectionError: If database operations fail
        """
        try:
            available_schemas = await self.get_available_schemas(database_type)
            exists = schema_name in available_schemas

            logger.debug(
                f"Schema '{schema_name}' {'exists' if exists else 'does not exist'} "
                f"in {database_type} database"
            )
            return exists

        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            raise

    async def get_schema_summary(
        self, schema_name: str, database_type: str = "source"
    ) -> Dict[str, Any]:
        """Get summary information about a schema.

        Args:
            schema_name: Name of the schema
            database_type: Database identifier ("source" or "target")

        Returns:
            Dictionary with schema summary information

        Raises:
            ProcessingError: If engine not initialized or schema doesn't exist
            DatabaseConnectionError: If database operations fail
        """
        if not self._initialized:
            raise ProcessingError("Engine not initialized. Call initialize() first.")

        try:
            # Validate schema exists
            if not await self.validate_schema_exists(schema_name, database_type):
                raise ProcessingError(
                    f"Schema '{schema_name}' not found in {database_type} database"
                )

            # Collect schema information
            schema_info = await self.schema_collector.collect_schema_info(
                schema_name=schema_name, database_type=database_type
            )

            # Generate summary
            summary = {
                "schema_name": schema_info.schema_name,
                "database_type": schema_info.database_type,
                "collection_time": schema_info.collection_time.isoformat(),
                "object_counts": schema_info.get_object_count(),
                "tables": [
                    {
                        "name": table.table_name,
                        "type": table.table_type,
                        "columns": len(table.columns),
                        "constraints": len(table.constraints),
                        "indexes": len(table.indexes),
                        "estimated_rows": table.estimated_rows,
                        "size": table.table_size,
                    }
                    for table in schema_info.tables
                ],
                "views": [
                    {
                        "name": view.view_name,
                        "is_updatable": view.is_updatable,
                        "is_insertable": view.is_insertable_into,
                    }
                    for view in schema_info.views
                ],
                "functions": [
                    {
                        "name": func.function_name,
                        "return_type": func.return_type,
                        "function_type": func.function_type,
                    }
                    for func in schema_info.functions
                ],
                "sequences": [
                    {
                        "name": seq.sequence_name,
                        "data_type": seq.data_type,
                        "start_value": seq.start_value,
                    }
                    for seq in schema_info.sequences
                ],
            }

            logger.debug(
                f"Generated summary for schema '{schema_name}' "
                f"in {database_type} database"
            )
            return summary

        except Exception as e:
            logger.error(f"Failed to get schema summary: {e}")
            if isinstance(e, (ProcessingError, DatabaseConnectionError)):
                raise
            raise ProcessingError(f"Schema summary generation failed: {str(e)}")

    async def cleanup(self) -> None:
        """Clean up resources and close connections.

        This method should be called when the engine is no longer needed
        to ensure proper cleanup of database connections and resources.
        """
        logger.info("Cleaning up schema comparison engine")

        try:
            if self.database_manager:
                await self.database_manager.close_all()
                logger.debug("Database connections closed")

            logger.info("Schema comparison engine cleanup completed")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            # Don't raise exceptions during cleanup
        finally:
            # Always set initialized to False
            self._initialized = False

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()

    def __repr__(self) -> str:
        """String representation of the engine."""
        status = "initialized" if self._initialized else "not initialized"
        return f"SchemaComparisonEngine(status={status})"
