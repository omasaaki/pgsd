"""Database module for PGSD application.

This module provides comprehensive database connectivity and management
for PostgreSQL schema comparison operations.

Components:
- DatabaseManager: High-level database management
- ConnectionPool: Connection pooling for efficient resource usage
- DatabaseConnector: Low-level connection operations
- ConnectionFactory: Connection creation and configuration
- VersionManager: PostgreSQL version management
- HealthMonitor: Connection health monitoring

Usage:
    from pgsd.database import DatabaseManager
    
    # Initialize database manager
    manager = DatabaseManager(config)
    await manager.initialize()
    
    # Get connections
    source_conn = await manager.get_source_connection()
    target_conn = await manager.get_target_connection()
    
    # Use connections...
    
    # Return connections
    manager.return_source_connection(source_conn)
    manager.return_target_connection(target_conn)
    
    # Cleanup
    await manager.close_all()
"""

from .manager import DatabaseManager
from .connector import DatabaseConnector
from .factory import ConnectionFactory
from .pool import ConnectionPool, PooledConnection
from .version import VersionManager
from .version_detector import VersionDetector
from .health import HealthMonitor

# Export main classes
__all__ = [
    'DatabaseManager',
    'DatabaseConnector',
    'ConnectionFactory',
    'ConnectionPool',
    'PooledConnection',
    'VersionManager',
    'VersionDetector',
    'HealthMonitor'
]

# Version information
__version__ = '1.0.0'

# Module metadata
__author__ = 'PGSD Development Team'
__description__ = 'Database connectivity and management for PostgreSQL schema comparison'
__license__ = 'MIT'
