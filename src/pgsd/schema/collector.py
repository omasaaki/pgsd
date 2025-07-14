"""Schema information collector for PGSD application."""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from ..database.manager import DatabaseManager
from ..database.version_detector import VersionDetector
from ..database.connector import DatabaseConnector
from ..constants.database import QueryConstants
from ..exceptions.database import (
    DatabaseQueryError,
    DatabasePermissionError,
    SchemaCollectionError
)
from ..models.database import PostgreSQLVersion


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
    
    async def collect_schema_info(self, schema_name: str, database_type: str = "source") -> Dict[str, Any]:
        """Collect complete schema information.
        
        Args:
            schema_name: Schema name to collect information for
            database_type: Database type ('source' or 'target')
            
        Returns:
            Dictionary with complete schema information
            
        Raises:
            SchemaCollectionError: If schema collection fails
        """
        cache_key = f"{database_type}:{schema_name}"
        
        # Check cache
        if self._is_cached(cache_key):
            self.logger.debug(f"Using cached schema info for {cache_key}")
            return self._schema_cache[cache_key]
        
        try:
            self.logger.info(f"Collecting schema information for {schema_name} ({database_type})")
            
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
                        schema=schema_name
                    )
                
                # Collect all schema information
                schema_info = {
                    "schema_name": schema_name,
                    "database_type": database_type,
                    "collection_time": datetime.utcnow().isoformat(),
                    "tables": await self._collect_tables(connector, schema_name),
                    "views": await self._collect_views(connector, schema_name),
                    "sequences": await self._collect_sequences(connector, schema_name),
                    "functions": await self._collect_functions(connector, schema_name),
                    "indexes": await self._collect_indexes(connector, schema_name),
                    "triggers": await self._collect_triggers(connector, schema_name),
                    "constraints": await self._collect_constraints(connector, schema_name)
                }
                
                # Cache the results
                self._schema_cache[cache_key] = schema_info
                self._cache_timestamps[cache_key] = datetime.utcnow()
                
                self.logger.info(f"Schema information collected for {schema_name}", extra={
                    "schema_name": schema_name,
                    "database_type": database_type,
                    "tables_count": len(schema_info["tables"]),
                    "views_count": len(schema_info["views"]),
                    "sequences_count": len(schema_info["sequences"])
                })
                
                return schema_info
                
            finally:
                # Return connection to pool
                if database_type == "source":
                    self.database_manager.return_source_connection(connector)
                else:
                    self.database_manager.return_target_connection(connector)
                    
        except Exception as e:
            self.logger.error(f"Schema collection failed for {schema_name}", extra={
                "schema_name": schema_name,
                "database_type": database_type,
                "error": str(e)
            })
            
            if isinstance(e, (DatabaseQueryError, DatabasePermissionError)):
                raise SchemaCollectionError(
                    f"Schema collection failed for {schema_name}: {str(e)}",
                    schema=schema_name,
                    database_type=database_type,
                    original_error=e
                )
            else:
                raise SchemaCollectionError(
                    f"Unexpected error during schema collection: {str(e)}",
                    schema=schema_name,
                    database_type=database_type,
                    original_error=e
                )
    
    async def _collect_tables(self, connector: DatabaseConnector, schema_name: str) -> List[Dict[str, Any]]:
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
        LEFT JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = t.table_schema
        WHERE t.table_schema = %s
        AND t.table_type = 'BASE TABLE'
        ORDER BY t.table_name
        """
        
        tables = await connector.execute_query(query, (schema_name,))
        
        # Collect columns for each table
        for table in tables:
            table["columns"] = await self._collect_columns(connector, schema_name, table["table_name"])
        
        return tables
    
    async def _collect_columns(self, connector: DatabaseConnector, schema_name: str, table_name: str) -> List[Dict[str, Any]]:
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
        LEFT JOIN pg_namespace pgn ON pgn.oid = pgc.relnamespace AND pgn.nspname = c.table_schema
        WHERE c.table_schema = %s AND c.table_name = %s
        ORDER BY c.ordinal_position
        """
        
        return await connector.execute_query(query, (schema_name, table_name))
    
    async def _collect_views(self, connector: DatabaseConnector, schema_name: str) -> List[Dict[str, Any]]:
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
        LEFT JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = v.table_schema
        WHERE v.table_schema = %s
        ORDER BY v.table_name
        """
        
        views = await connector.execute_query(query, (schema_name,))
        
        # Collect columns for each view
        for view in views:
            view["columns"] = await self._collect_columns(connector, schema_name, view["view_name"])
        
        return views
    
    async def _collect_sequences(self, connector: DatabaseConnector, schema_name: str) -> List[Dict[str, Any]]:
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
        LEFT JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = s.sequence_schema
        WHERE s.sequence_schema = %s
        ORDER BY s.sequence_name
        """
        
        return await connector.execute_query(query, (schema_name,))
    
    async def _collect_functions(self, connector: DatabaseConnector, schema_name: str) -> List[Dict[str, Any]]:
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
        LEFT JOIN pg_namespace n ON n.oid = p.pronamespace AND n.nspname = r.routine_schema
        WHERE r.routine_schema = %s
        ORDER BY r.routine_name
        """
        
        return await connector.execute_query(query, (schema_name,))
    
    async def _collect_indexes(self, connector: DatabaseConnector, schema_name: str) -> List[Dict[str, Any]]:
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
        JOIN pg_namespace n ON n.oid = t.relnamespace AND n.nspname = i.schemaname
        LEFT JOIN pg_index idx ON idx.indexrelid = (SELECT oid FROM pg_class WHERE relname = i.indexname)
        LEFT JOIN pg_am am ON am.oid = (SELECT c.relam FROM pg_class c WHERE c.oid = idx.indexrelid)
        WHERE i.schemaname = %s
        ORDER BY i.tablename, i.indexname
        """
        
        return await connector.execute_query(query, (schema_name,))
    
    async def _collect_triggers(self, connector: DatabaseConnector, schema_name: str) -> List[Dict[str, Any]]:
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
    
    async def _collect_constraints(self, connector: DatabaseConnector, schema_name: str) -> List[Dict[str, Any]]:
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
            "oldest_cache_age": min([
                (datetime.utcnow() - ts).total_seconds() 
                for ts in self._cache_timestamps.values()
            ]) if self._cache_timestamps else None
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
            schemas = await connector.execute_query(QueryConstants.GET_ACCESSIBLE_SCHEMAS)
            return [schema["schema_name"] for schema in schemas]
        finally:
            # Return connection to pool
            if database_type == "source":
                self.database_manager.return_source_connection(connector)
            else:
                self.database_manager.return_target_connection(connector)
