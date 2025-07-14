"""Schema information collection module for PGSD application.

This module provides functionality to collect comprehensive schema information
from PostgreSQL databases for comparison operations.

Components:
- SchemaInformationCollector: Main collector for schema information

Usage:
    from pgsd.schema import SchemaInformationCollector
    
    # Initialize collector
    collector = SchemaInformationCollector(database_manager)
    
    # Collect schema information
    schema_info = await collector.collect_schema_info("public", "source")
    
    # Get available schemas
    schemas = await collector.get_available_schemas("source")
"""

from .collector import SchemaInformationCollector

# Export main classes
__all__ = [
    'SchemaInformationCollector'
]

# Version information
__version__ = '1.0.0'

# Module metadata
__author__ = 'PGSD Development Team'
__description__ = 'Schema information collection for PostgreSQL databases'
__license__ = 'MIT'
