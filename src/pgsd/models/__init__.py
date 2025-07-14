"""Data models for PGSD application.

This module contains all data models and classes used throughout the application.

Components:
- DatabaseManager: Database connection and management
- DatabaseConnector: Low-level database operations
- ConnectionPool: Database connection pooling
- PostgreSQLVersion: Version information model
- DatabasePermissions: Permission checking model
- ConnectionInfo: Connection configuration model
- PoolHealth: Connection pool health monitoring
- SchemaInfo: Schema information data model
- TableInfo: Table information data model
- ColumnInfo: Column information data model
- ConstraintInfo: Constraint information data model
- IndexInfo: Index information data model
- TriggerInfo: Trigger information data model
- ViewInfo: View information data model
- SequenceInfo: Sequence information data model
- FunctionInfo: Function information data model
- SchemaComparison: Schema comparison result data model

Usage:
    from pgsd.models import PostgreSQLVersion, DatabasePermissions
    from pgsd.models import SchemaInfo, TableInfo, ColumnInfo

    # Create version instance
    version = PostgreSQLVersion(14, 5, 0, "14.5", 140500)

    # Check permissions
    permissions = DatabasePermissions(can_read=True, can_write=False)

    # Create schema info
    schema_info = SchemaInfo(
        schema_name="public",
        database_type="source",
        collection_time=datetime.now()
    )
"""

from .database import (
    DatabaseType,
    ConnectionStatus,
    PostgreSQLVersion,
    DatabasePermissions,
    ConnectionInfo,
    PoolHealth,
)

from .schema import (
    ObjectType,
    ConstraintType,
    IndexType,
    ColumnInfo,
    ConstraintInfo,
    IndexInfo,
    TriggerInfo,
    TableInfo,
    ViewInfo,
    SequenceInfo,
    FunctionInfo,
    SchemaInfo,
    SchemaComparison,
)

# Export main classes
__all__ = [
    # Database models
    "DatabaseType",
    "ConnectionStatus",
    "PostgreSQLVersion",
    "DatabasePermissions",
    "ConnectionInfo",
    "PoolHealth",
    # Schema models
    "ObjectType",
    "ConstraintType",
    "IndexType",
    "ColumnInfo",
    "ConstraintInfo",
    "IndexInfo",
    "TriggerInfo",
    "TableInfo",
    "ViewInfo",
    "SequenceInfo",
    "FunctionInfo",
    "SchemaInfo",
    "SchemaComparison",
]
