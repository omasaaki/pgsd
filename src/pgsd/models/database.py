"""Database models for PGSD application."""

from dataclasses import dataclass
from typing import Dict, Optional, List, Any
from enum import Enum
from datetime import datetime


class DatabaseType(Enum):
    """Database type enumeration."""

    POSTGRESQL = "postgresql"


class ConnectionStatus(Enum):
    """Connection status enumeration."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    CONNECTING = "connecting"


@dataclass
class PostgreSQLVersion:
    """PostgreSQL version information."""

    major: int
    minor: int
    patch: int
    full_version: str
    server_version_num: int

    @classmethod
    def parse(cls, version_string: str) -> "PostgreSQLVersion":
        """Parse version string to PostgreSQLVersion.

        Args:
            version_string: Version string like "14.5" or "PostgreSQL 14.5"

        Returns:
            PostgreSQLVersion instance
        """
        # Remove "PostgreSQL" prefix if present and extract version number
        clean_version = version_string.replace("PostgreSQL", "").strip()
        
        # Extract version number before any additional info (e.g., "(Ubuntu ...")
        import re
        version_match = re.match(r'(\d+)\.(\d+)(?:\.(\d+))?', clean_version)
        if not version_match:
            raise ValueError(f"Unable to parse PostgreSQL version from: {version_string}")
        
        major = int(version_match.group(1))
        minor = int(version_match.group(2)) if version_match.group(2) else 0
        patch = int(version_match.group(3)) if version_match.group(3) else 0

        # Calculate server_version_num (PostgreSQL format)
        server_version_num = major * 10000 + minor * 100 + patch

        return cls(
            major=major,
            minor=minor,
            patch=patch,
            full_version=clean_version,
            server_version_num=server_version_num,
        )

    def __str__(self) -> str:
        """String representation."""
        return f"{self.major}.{self.minor}.{self.patch}"

    def is_compatible(self, min_version: str) -> bool:
        """Check if version is compatible with minimum requirement.

        Args:
            min_version: Minimum version string

        Returns:
            True if compatible, False otherwise
        """
        min_ver = self.parse(min_version)
        return self.server_version_num >= min_ver.server_version_num

    def __eq__(self, other) -> bool:
        """Equality comparison."""
        if not isinstance(other, PostgreSQLVersion):
            return False
        return self.server_version_num == other.server_version_num

    def __lt__(self, other) -> bool:
        """Less than comparison."""
        if not isinstance(other, PostgreSQLVersion):
            return NotImplemented
        return self.server_version_num < other.server_version_num

    def __le__(self, other) -> bool:
        """Less than or equal comparison."""
        if not isinstance(other, PostgreSQLVersion):
            return NotImplemented
        return self.server_version_num <= other.server_version_num

    def __gt__(self, other) -> bool:
        """Greater than comparison."""
        if not isinstance(other, PostgreSQLVersion):
            return NotImplemented
        return self.server_version_num > other.server_version_num

    def __ge__(self, other) -> bool:
        """Greater than or equal comparison."""
        if not isinstance(other, PostgreSQLVersion):
            return NotImplemented
        return self.server_version_num >= other.server_version_num


@dataclass
class DatabasePermissions:
    """Database permissions information."""

    can_connect: bool = False
    can_read_schema: bool = False
    can_read_tables: bool = False
    can_read_views: bool = False
    can_read_constraints: bool = False
    can_read_indexes: bool = False
    can_read_triggers: bool = False
    can_read_procedures: bool = False
    accessible_schemas: List[str] = None

    def __post_init__(self):
        """Initialize accessible_schemas if None."""
        if self.accessible_schemas is None:
            self.accessible_schemas = []

    def has_required_permissions(self) -> bool:
        """Check if all required permissions are available.

        Returns:
            True if all required permissions are available
        """
        return (
            self.can_connect
            and self.can_read_schema
            and self.can_read_tables
            and self.can_read_views
            and self.can_read_constraints
        )

    def get_missing_permissions(self) -> List[str]:
        """Get list of missing permissions.

        Returns:
            List of missing permission names
        """
        missing = []
        if not self.can_connect:
            missing.append("CONNECT")
        if not self.can_read_schema:
            missing.append("USAGE on schema")
        if not self.can_read_tables:
            missing.append("SELECT on tables")
        if not self.can_read_views:
            missing.append("SELECT on views")
        if not self.can_read_constraints:
            missing.append("SELECT on constraints")

        return missing


@dataclass
class ConnectionInfo:
    """Connection information and metadata."""

    connection_id: str
    database_name: str
    host: str
    port: int
    username: str
    schema: str
    status: ConnectionStatus
    version: Optional[PostgreSQLVersion] = None
    permissions: Optional[DatabasePermissions] = None
    connection_time: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    error_message: Optional[str] = None

    def is_healthy(self) -> bool:
        """Check if connection is healthy.

        Returns:
            True if connection is healthy
        """
        return (
            self.status == ConnectionStatus.CONNECTED
            and self.version is not None
            and self.permissions is not None
            and self.permissions.has_required_permissions()
        )

    def get_connection_string(self, mask_password: bool = True) -> str:
        """Get connection string representation.

        Args:
            mask_password: Whether to mask password in output

        Returns:
            Connection string
        """
        password_display = "***" if mask_password else "<password>"
        return f"postgresql://{self.username}:{password_display}@{self.host}:{self.port}/{self.database_name}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary representation
        """
        return {
            "connection_id": self.connection_id,
            "database_name": self.database_name,
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "schema": self.schema,
            "status": self.status.value,
            "version": str(self.version) if self.version else None,
            "permissions": {
                "has_required": (
                    self.permissions.has_required_permissions()
                    if self.permissions
                    else False
                ),
                "missing": (
                    self.permissions.get_missing_permissions()
                    if self.permissions
                    else []
                ),
            },
            "connection_time": (
                self.connection_time.isoformat() if self.connection_time else None
            ),
            "last_activity": (
                self.last_activity.isoformat() if self.last_activity else None
            ),
            "error_message": self.error_message,
            "is_healthy": self.is_healthy(),
        }


@dataclass
class PoolHealth:
    """Connection pool health information."""

    total_connections: int
    active_connections: int
    idle_connections: int
    max_connections: int
    healthy_connections: int
    failed_connections: int
    average_connection_time: float
    last_health_check: datetime

    def utilization_percentage(self) -> float:
        """Calculate pool utilization percentage.

        Returns:
            Utilization percentage (0-100)
        """
        if self.max_connections == 0:
            return 0.0
        return (self.active_connections / self.max_connections) * 100

    def is_healthy(self) -> bool:
        """Check if pool is healthy.

        Returns:
            True if pool is healthy
        """
        return (
            self.failed_connections == 0
            and self.healthy_connections == self.total_connections
            and self.utilization_percentage() < 90  # Not overloaded
        )

    def get_status_summary(self) -> str:
        """Get human-readable status summary.

        Returns:
            Status summary string
        """
        if self.is_healthy():
            return f"Healthy ({self.active_connections}/{self.max_connections} active)"
        elif self.failed_connections > 0:
            return f"Unhealthy ({self.failed_connections} failed connections)"
        elif self.utilization_percentage() >= 90:
            return f"Overloaded ({self.utilization_percentage():.1f}% utilization)"
        else:
            return f"Degraded ({self.healthy_connections}/{self.total_connections} healthy)"
