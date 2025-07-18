"""Schema information collector for PGSD application."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..database.manager import DatabaseManager
from ..database.version_detector import VersionDetector
from ..database.connector import DatabaseConnector
from ..constants.database import QueryConstants
from ..models.schema import (
    SchemaInfo,
    TableInfo,
    ViewInfo,
    SequenceInfo,
    FunctionInfo,
    IndexInfo,
    TriggerInfo,
    ConstraintInfo,
    ColumnInfo,
)
from ..exceptions.database import (
    DatabaseQueryError,
    DatabasePermissionError,
    SchemaCollectionError,
)


class SchemaInformationCollector:
    """PostgreSQL schema information collector."""

    def __init__(self, database_manager: DatabaseManager):
        """Initialize schema information collector.

        Args:
            database_manager: Database manager instance
        """
        self.database_manager = database_manager
        self.version_detector = VersionDetector(database_manager)
        self.logger = logging.getLogger(__name__)

        # Cache for schema information
        self._schema_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._cache_ttl = 300  # 5 minutes

        self.logger.info("Schema information collector initialized")

    async def collect_schema_info(
        self, schema_name: str, database_type: str = "source"
    ) -> SchemaInfo:
        """Collect complete schema information.

        Args:
            schema_name: Schema name to collect information for
            database_type: Database type ('source' or 'target')

        Returns:
            SchemaInfo object with complete schema information

        Raises:
            SchemaCollectionError: If schema collection fails
        """
        cache_key = f"{database_type}:{schema_name}"

        # Check cache
        if self._is_cached(cache_key):
            self.logger.debug(f"Using cached schema info for {cache_key}")
            cached_data = self._schema_cache[cache_key]
            return SchemaInfo.from_dict(cached_data)

        try:
            self.logger.info(
                f"Collecting schema information for {schema_name} ({database_type})"
            )

            # Get database connection
            if database_type == "source":
                connector = await self.database_manager.get_source_connection()
            else:
                connector = await self.database_manager.get_target_connection()

            try:
                # Verify schema access
                if not await connector.verify_schema_access(schema_name):
                    raise DatabasePermissionError(
                        f"No access to schema '{schema_name}'",
                        operation="access_schema",
                        object_name=schema_name,
                    )

                # Collect all schema information
                collection_time = datetime.utcnow()
                
                # Collect raw data
                tables_data = await self._collect_tables(connector, schema_name)
                views_data = await self._collect_views(connector, schema_name)
                sequences_data = await self._collect_sequences(connector, schema_name)
                functions_data = await self._collect_functions(connector, schema_name)
                indexes_data = await self._collect_indexes(connector, schema_name)
                triggers_data = await self._collect_triggers(connector, schema_name)
                constraints_data = await self._collect_constraints(connector, schema_name)
                
                # Convert to model objects
                schema_info = SchemaInfo(
                    schema_name=schema_name,
                    database_type=database_type,
                    collection_time=collection_time,
                    tables=[self._convert_table_data(table_data) for table_data in tables_data],
                    views=[self._convert_view_data(view_data) for view_data in views_data],
                    sequences=[self._convert_sequence_data(seq_data) for seq_data in sequences_data],
                    functions=[self._convert_function_data(func_data) for func_data in functions_data],
                    indexes=[self._convert_index_data(idx_data) for idx_data in indexes_data],
                    triggers=[self._convert_trigger_data(trig_data) for trig_data in triggers_data],
                    constraints=[self._convert_constraint_data(cons_data) for cons_data in constraints_data],
                )

                # Cache the results as dictionary for backward compatibility
                cache_data = schema_info.to_dict()
                self._schema_cache[cache_key] = cache_data
                self._cache_timestamps[cache_key] = collection_time

                self.logger.info(
                    f"Schema information collected for {schema_name}",
                    extra={
                        "schema_name": schema_name,
                        "database_type": database_type,
                        "tables_count": len(schema_info.tables),
                        "views_count": len(schema_info.views),
                        "sequences_count": len(schema_info.sequences),
                    },
                )

                return schema_info

            finally:
                # Return connection to pool
                if database_type == "source":
                    self.database_manager.return_source_connection(connector)
                else:
                    self.database_manager.return_target_connection(connector)

        except Exception as e:
            self.logger.error(
                f"Schema collection failed for {schema_name}",
                extra={
                    "schema_name": schema_name,
                    "database_type": database_type,
                    "error": str(e),
                },
            )

            if isinstance(e, (DatabaseQueryError, DatabasePermissionError)):
                raise SchemaCollectionError(
                    f"Schema collection failed for {schema_name}: {str(e)}",
                    schema=schema_name,
                    database_type=database_type,
                    original_error=e,
                )
            else:
                raise SchemaCollectionError(
                    f"Unexpected error during schema collection: {str(e)}",
                    schema=schema_name,
                    database_type=database_type,
                    original_error=e,
                )

    async def _collect_tables(
        self, connector: DatabaseConnector, schema_name: str
    ) -> List[Dict[str, Any]]:
        """Collect table information.

        Args:
            connector: Database connector
            schema_name: Schema name

        Returns:
            List of table information
        """
        query = """
        SELECT
            t.table_name,
            t.table_type,
            t.table_schema,
            obj_description(c.oid, 'pg_class') as table_comment,
            c.reltuples::bigint as estimated_rows,
            pg_size_pretty(pg_total_relation_size(c.oid)) as table_size
        FROM information_schema.tables t
        LEFT JOIN pg_class c ON c.relname = t.table_name
        LEFT JOIN pg_namespace n ON n.oid = c.relnamespace
            AND n.nspname = t.table_schema
        WHERE t.table_schema = %s
        AND t.table_type = 'BASE TABLE'
        ORDER BY t.table_name
        """

        tables = await connector.execute_query(query, (schema_name,))

        # Collect columns for each table
        for table in tables:
            table["columns"] = await self._collect_columns(
                connector, schema_name, table["table_name"]
            )

        return tables

    async def _collect_columns(
        self, connector: DatabaseConnector, schema_name: str, table_name: str
    ) -> List[Dict[str, Any]]:
        """Collect column information for a table.

        Args:
            connector: Database connector
            schema_name: Schema name
            table_name: Table name

        Returns:
            List of column information
        """
        query = """
        SELECT
            c.column_name,
            c.ordinal_position,
            c.column_default,
            c.is_nullable,
            c.data_type,
            c.character_maximum_length,
            c.numeric_precision,
            c.numeric_scale,
            c.udt_name,
            col_description(pgc.oid, c.ordinal_position) as column_comment
        FROM information_schema.columns c
        LEFT JOIN pg_class pgc ON pgc.relname = c.table_name
        LEFT JOIN pg_namespace pgn ON pgn.oid = pgc.relnamespace
            AND pgn.nspname = c.table_schema
        WHERE c.table_schema = %s AND c.table_name = %s
        ORDER BY c.ordinal_position
        """

        return await connector.execute_query(query, (schema_name, table_name))

    async def _collect_views(
        self, connector: DatabaseConnector, schema_name: str
    ) -> List[Dict[str, Any]]:
        """Collect view information.

        Args:
            connector: Database connector
            schema_name: Schema name

        Returns:
            List of view information
        """
        query = """
        SELECT
            v.table_name as view_name,
            v.view_definition,
            v.is_updatable,
            v.is_insertable_into,
            obj_description(c.oid, 'pg_class') as view_comment
        FROM information_schema.views v
        LEFT JOIN pg_class c ON c.relname = v.table_name
        LEFT JOIN pg_namespace n ON n.oid = c.relnamespace
            AND n.nspname = v.table_schema
        WHERE v.table_schema = %s
        ORDER BY v.table_name
        """

        views = await connector.execute_query(query, (schema_name,))

        # Collect columns for each view
        for view in views:
            view["columns"] = await self._collect_columns(
                connector, schema_name, view["view_name"]
            )

        return views

    async def _collect_sequences(
        self, connector: DatabaseConnector, schema_name: str
    ) -> List[Dict[str, Any]]:
        """Collect sequence information.

        Args:
            connector: Database connector
            schema_name: Schema name

        Returns:
            List of sequence information
        """
        query = """
        SELECT
            s.sequence_name,
            s.data_type,
            s.start_value,
            s.minimum_value,
            s.maximum_value,
            s.increment,
            s.cycle_option,
            obj_description(c.oid, 'pg_class') as sequence_comment
        FROM information_schema.sequences s
        LEFT JOIN pg_class c ON c.relname = s.sequence_name
        LEFT JOIN pg_namespace n ON n.oid = c.relnamespace
            AND n.nspname = s.sequence_schema
        WHERE s.sequence_schema = %s
        ORDER BY s.sequence_name
        """

        return await connector.execute_query(query, (schema_name,))

    async def _collect_functions(
        self, connector: DatabaseConnector, schema_name: str
    ) -> List[Dict[str, Any]]:
        """Collect function information.

        Args:
            connector: Database connector
            schema_name: Schema name

        Returns:
            List of function information
        """
        query = """
        SELECT
            r.routine_name as function_name,
            r.routine_type,
            r.data_type as return_type,
            r.routine_definition,
            r.external_language,
            obj_description(p.oid, 'pg_proc') as function_comment
        FROM information_schema.routines r
        LEFT JOIN pg_proc p ON p.proname = r.routine_name
        LEFT JOIN pg_namespace n ON n.oid = p.pronamespace
            AND n.nspname = r.routine_schema
        WHERE r.routine_schema = %s
        ORDER BY r.routine_name
        """

        return await connector.execute_query(query, (schema_name,))

    async def _collect_indexes(
        self, connector: DatabaseConnector, schema_name: str
    ) -> List[Dict[str, Any]]:
        """Collect index information.

        Args:
            connector: Database connector
            schema_name: Schema name

        Returns:
            List of index information
        """
        query = """
        SELECT
            i.indexname as index_name,
            i.tablename as table_name,
            i.indexdef as index_definition,
            idx.indisunique as is_unique,
            idx.indisprimary as is_primary,
            am.amname as index_type,
            obj_description(idx.indexrelid, 'pg_class') as index_comment
        FROM pg_indexes i
        JOIN pg_class t ON t.relname = i.tablename
        JOIN pg_namespace n ON n.oid = t.relnamespace
            AND n.nspname = i.schemaname
        LEFT JOIN pg_index idx ON idx.indexrelid = (
            SELECT oid FROM pg_class WHERE relname = i.indexname
        )
        LEFT JOIN pg_am am ON am.oid = (
            SELECT c.relam FROM pg_class c WHERE c.oid = idx.indexrelid
        )
        WHERE i.schemaname = %s
        ORDER BY i.tablename, i.indexname
        """

        return await connector.execute_query(query, (schema_name,))

    async def _collect_triggers(
        self, connector: DatabaseConnector, schema_name: str
    ) -> List[Dict[str, Any]]:
        """Collect trigger information.

        Args:
            connector: Database connector
            schema_name: Schema name

        Returns:
            List of trigger information
        """
        query = """
        SELECT
            t.trigger_name,
            t.event_object_table as table_name,
            t.event_manipulation,
            t.action_timing,
            t.action_statement,
            obj_description(tr.oid, 'pg_trigger') as trigger_comment
        FROM information_schema.triggers t
        LEFT JOIN pg_trigger tr ON tr.tgname = t.trigger_name
        LEFT JOIN pg_class c ON c.oid = tr.tgrelid
        LEFT JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE t.trigger_schema = %s
        ORDER BY t.event_object_table, t.trigger_name
        """

        return await connector.execute_query(query, (schema_name,))

    async def _collect_constraints(
        self, connector: DatabaseConnector, schema_name: str
    ) -> List[Dict[str, Any]]:
        """Collect constraint information.

        Args:
            connector: Database connector
            schema_name: Schema name

        Returns:
            List of constraint information
        """
        query = """
        SELECT
            tc.constraint_name,
            tc.table_name,
            tc.constraint_type,
            kcu.column_name,
            ccu.table_name as foreign_table_name,
            ccu.column_name as foreign_column_name,
            cc.check_clause,
            obj_description(con.oid, 'pg_constraint') as constraint_comment
        FROM information_schema.table_constraints tc
        LEFT JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        LEFT JOIN information_schema.constraint_column_usage ccu
            ON tc.constraint_name = ccu.constraint_name
            AND tc.table_schema = ccu.table_schema
        LEFT JOIN information_schema.check_constraints cc
            ON tc.constraint_name = cc.constraint_name
        LEFT JOIN pg_constraint con ON con.conname = tc.constraint_name
        WHERE tc.table_schema = %s
        ORDER BY tc.table_name, tc.constraint_name
        """

        return await connector.execute_query(query, (schema_name,))

    def _is_cached(self, cache_key: str) -> bool:
        """Check if schema information is cached and still valid.

        Args:
            cache_key: Cache key to check

        Returns:
            True if cached and valid, False otherwise
        """
        if cache_key not in self._schema_cache:
            return False

        cache_time = self._cache_timestamps.get(cache_key)
        if not cache_time:
            return False

        age = (datetime.utcnow() - cache_time).total_seconds()
        return age < self._cache_ttl

    def clear_cache(self, schema_name: Optional[str] = None):
        """Clear schema information cache.

        Args:
            schema_name: Specific schema to clear, or None for all
        """
        if schema_name:
            # Clear specific schema
            keys_to_remove = [k for k in self._schema_cache.keys() if schema_name in k]
            for key in keys_to_remove:
                self._schema_cache.pop(key, None)
                self._cache_timestamps.pop(key, None)
        else:
            # Clear all cache
            self._schema_cache.clear()
            self._cache_timestamps.clear()

        self.logger.info(f"Schema cache cleared for {schema_name or 'all schemas'}")

    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "cached_schemas": len(self._schema_cache),
            "cache_keys": list(self._schema_cache.keys()),
            "cache_ttl_seconds": self._cache_ttl,
            "oldest_cache_age": (
                min(
                    [
                        (datetime.utcnow() - ts).total_seconds()
                        for ts in self._cache_timestamps.values()
                    ]
                )
                if self._cache_timestamps
                else None
            ),
        }

    async def get_available_schemas(self, database_type: str = "source") -> List[str]:
        """Get list of available schemas.

        Args:
            database_type: Database type ('source' or 'target')

        Returns:
            List of available schema names
        """
        # Get database connection
        if database_type == "source":
            connector = await self.database_manager.get_source_connection()
        else:
            connector = await self.database_manager.get_target_connection()

        try:
            schemas = await connector.execute_query(
                QueryConstants.GET_ACCESSIBLE_SCHEMAS
            )
            return [schema["schema_name"] for schema in schemas]
        finally:
            # Return connection to pool
            if database_type == "source":
                self.database_manager.return_source_connection(connector)
            else:
                self.database_manager.return_target_connection(connector)

    def _convert_table_data(self, table_data: Dict[str, Any]) -> TableInfo:
        """Convert table dictionary data to TableInfo object."""
        columns = [self._convert_column_data(col) for col in table_data.get("columns", [])]
        
        return TableInfo(
            table_name=table_data["table_name"],
            table_type=table_data["table_type"],
            table_schema=table_data["table_schema"],
            table_comment=table_data.get("table_comment"),
            estimated_rows=table_data.get("estimated_rows", 0),
            table_size=table_data.get("table_size", "0 bytes"),
            columns=columns,
            constraints=[],  # Will be populated separately
            indexes=[],      # Will be populated separately  
            triggers=[],     # Will be populated separately
        )

    def _convert_column_data(self, column_data: Dict[str, Any]) -> ColumnInfo:
        """Convert column dictionary data to ColumnInfo object."""
        return ColumnInfo(
            column_name=column_data["column_name"],
            ordinal_position=column_data["ordinal_position"],
            column_default=column_data.get("column_default"),
            is_nullable=column_data.get("is_nullable", True),
            data_type=column_data.get("data_type", ""),
            character_maximum_length=column_data.get("character_maximum_length"),
            numeric_precision=column_data.get("numeric_precision"),
            numeric_scale=column_data.get("numeric_scale"),
            udt_name=column_data.get("udt_name"),
            column_comment=column_data.get("column_comment"),
        )

    def _convert_view_data(self, view_data: Dict[str, Any]) -> ViewInfo:
        """Convert view dictionary data to ViewInfo object."""
        columns = [self._convert_column_data(col) for col in view_data.get("columns", [])]
        
        return ViewInfo(
            view_name=view_data["view_name"],
            view_definition=view_data["view_definition"],
            is_updatable=view_data["is_updatable"],
            is_insertable_into=view_data["is_insertable_into"],
            view_comment=view_data.get("view_comment"),
            columns=columns,
        )

    def _convert_sequence_data(self, sequence_data: Dict[str, Any]) -> SequenceInfo:
        """Convert sequence dictionary data to SequenceInfo object."""
        return SequenceInfo(
            sequence_name=sequence_data["sequence_name"],
            data_type=sequence_data["data_type"],
            start_value=sequence_data["start_value"],
            minimum_value=sequence_data["minimum_value"],
            maximum_value=sequence_data["maximum_value"],
            increment=sequence_data["increment"],
            cycle_option=sequence_data["cycle_option"],
            sequence_comment=sequence_data.get("sequence_comment"),
        )

    def _convert_function_data(self, function_data: Dict[str, Any]) -> FunctionInfo:
        """Convert function dictionary data to FunctionInfo object."""
        return FunctionInfo(
            function_name=function_data["function_name"],
            function_type=function_data.get("routine_type", "FUNCTION"),
            return_type=function_data.get("return_type", "void"),
            function_definition=function_data.get("routine_definition", ""),
            argument_types=[],  # Could be enhanced later
            argument_names=[],  # Could be enhanced later
            function_comment=function_data.get("function_comment"),
        )

    def _convert_index_data(self, index_data: Dict[str, Any]) -> IndexInfo:
        """Convert index dictionary data to IndexInfo object."""
        return IndexInfo(
            index_name=index_data["index_name"],
            table_name=index_data["table_name"],
            index_type=index_data.get("index_type", "btree"),
            is_unique=index_data.get("is_unique", False),
            is_primary=index_data.get("is_primary", False),
            column_names=[],  # Could be enhanced later
            index_definition=index_data.get("index_definition"),
            condition=None,  # Could be enhanced later
            index_comment=index_data.get("index_comment"),
        )

    def _convert_trigger_data(self, trigger_data: Dict[str, Any]) -> TriggerInfo:
        """Convert trigger dictionary data to TriggerInfo object."""
        return TriggerInfo(
            trigger_name=trigger_data["trigger_name"],
            table_name=trigger_data["table_name"],
            trigger_event=trigger_data.get("event_manipulation", ""),
            trigger_timing=trigger_data.get("action_timing", ""),
            function_name=trigger_data.get("action_statement", ""),
            trigger_definition=trigger_data.get("action_statement"),
            trigger_comment=trigger_data.get("trigger_comment"),
        )

    def _convert_constraint_data(self, constraint_data: Dict[str, Any]) -> ConstraintInfo:
        """Convert constraint dictionary data to ConstraintInfo object."""
        return ConstraintInfo(
            constraint_name=constraint_data["constraint_name"],
            table_name=constraint_data["table_name"],
            constraint_type=constraint_data["constraint_type"],
            column_name=constraint_data.get("column_name"),
            foreign_table_name=constraint_data.get("foreign_table_name"),
            foreign_column_name=constraint_data.get("foreign_column_name"),
            check_clause=constraint_data.get("check_clause"),
            constraint_comment=constraint_data.get("constraint_comment"),
        )
