"""PostgreSQL version detection functionality for PGSD application."""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from ..constants.database import (
    DatabaseConstants,
    LogMessages,
    ErrorMessages
)
from ..exceptions.database import (
    DatabaseVersionError,
    DatabaseConnectionError
)
from ..models.database import PostgreSQLVersion, ConnectionInfo
from .version import VersionManager
from .manager import DatabaseManager


class VersionDetector:
    """PostgreSQL version detection and compatibility checking."""
    
    def __init__(self, database_manager: DatabaseManager):
        """Initialize version detector.
        
        Args:
            database_manager: Database manager instance
        """
        self.database_manager = database_manager
        self.version_manager = VersionManager()
        self.logger = logging.getLogger(__name__)
        
        # Cached version information
        self._source_version: Optional[PostgreSQLVersion] = None
        self._target_version: Optional[PostgreSQLVersion] = None
        self._last_detection_time: Optional[datetime] = None
        
        # Detection results
        self._detection_results: Dict[str, Any] = {}
        
        self.logger.info("Version detector initialized")
    
    async def detect_versions(self, force_refresh: bool = False) -> Dict[str, PostgreSQLVersion]:
        """Detect PostgreSQL versions for both source and target databases.
        
        Args:
            force_refresh: Force refresh of cached version information
            
        Returns:
            Dictionary with source and target versions
            
        Raises:
            DatabaseVersionError: If version detection fails
        """
        try:
            # Check if we need to refresh the cache
            if not force_refresh and self._source_version and self._target_version:
                cache_age = (datetime.utcnow() - self._last_detection_time).total_seconds()
                if cache_age < 300:  # 5 minutes cache
                    self.logger.debug("Using cached version information")
                    return {
                        "source": self._source_version,
                        "target": self._target_version
                    }
            
            self.logger.info("Detecting PostgreSQL versions")
            
            # Detect source version
            try:
                source_conn = await self.database_manager.get_source_connection()
                self._source_version = await source_conn.get_version()
                self.database_manager.return_source_connection(source_conn)
                
                self.logger.info("Source database version detected", extra={
                    "version": str(self._source_version),
                    "database": self.database_manager.config.database.source.database
                })
                
            except Exception as e:
                self.logger.error("Failed to detect source database version", extra={
                    "error": str(e)
                })
                raise DatabaseVersionError(
                    f"Source database version detection failed: {str(e)}",
                    original_error=e
                )
            
            # Detect target version
            try:
                target_conn = await self.database_manager.get_target_connection()
                self._target_version = await target_conn.get_version()
                self.database_manager.return_target_connection(target_conn)
                
                self.logger.info("Target database version detected", extra={
                    "version": str(self._target_version),
                    "database": self.database_manager.config.database.target.database
                })
                
            except Exception as e:
                self.logger.error("Failed to detect target database version", extra={
                    "error": str(e)
                })
                raise DatabaseVersionError(
                    f"Target database version detection failed: {str(e)}",
                    original_error=e
                )
            
            # Update cache timestamp
            self._last_detection_time = datetime.utcnow()
            
            # Store detection results
            self._detection_results = {
                "source_version": str(self._source_version),
                "target_version": str(self._target_version),
                "detection_time": self._last_detection_time.isoformat(),
                "source_version_num": self._source_version.server_version_num,
                "target_version_num": self._target_version.server_version_num
            }
            
            return {
                "source": self._source_version,
                "target": self._target_version
            }
            
        except Exception as e:
            if isinstance(e, DatabaseVersionError):
                raise
            else:
                raise DatabaseVersionError(
                    f"Version detection failed: {str(e)}",
                    original_error=e
                )
    
    async def check_compatibility(self, 
                                source_version: Optional[PostgreSQLVersion] = None,
                                target_version: Optional[PostgreSQLVersion] = None) -> Dict[str, Any]:
        """Check compatibility between source and target versions.
        
        Args:
            source_version: Source database version (auto-detected if None)
            target_version: Target database version (auto-detected if None)
            
        Returns:
            Dictionary with compatibility information
        """
        # Use provided versions or detect if not provided
        if not source_version or not target_version:
            versions = await self.detect_versions()
            source_version = source_version or versions["source"]
            target_version = target_version or versions["target"]
        
        compatibility = {
            "source_version": str(source_version),
            "target_version": str(target_version),
            "is_compatible": True,
            "warnings": [],
            "errors": [],
            "recommendations": [],
            "version_comparison": {},
            "feature_differences": []
        }
        
        try:
            # Check individual version compatibility
            source_compat = self.version_manager.check_version_compatibility(source_version)
            target_compat = self.version_manager.check_version_compatibility(target_version)
            
            # Check source version support
            if not source_compat["is_supported"]:
                compatibility["errors"].append(
                    f"Source database version {source_version} is not supported"
                )
                compatibility["is_compatible"] = False
            
            # Check target version support
            if not target_compat["is_supported"]:
                compatibility["errors"].append(
                    f"Target database version {target_version} is not supported"
                )
                compatibility["is_compatible"] = False
            
            # Add version-specific warnings
            compatibility["warnings"].extend(source_compat["warnings"])
            compatibility["warnings"].extend(target_compat["warnings"])
            
            # Add recommendations
            compatibility["recommendations"].extend(
                self.version_manager.get_version_recommendations(source_version)
            )
            compatibility["recommendations"].extend(
                self.version_manager.get_version_recommendations(target_version)
            )
            
            # Compare versions
            version_comparison = self.version_manager.compare_versions(source_version, target_version)
            compatibility["version_comparison"] = version_comparison
            
            # Check for compatibility concerns
            if version_comparison["compatibility_concerns"]:
                compatibility["warnings"].extend(version_comparison["compatibility_concerns"])
            
            # Check for feature differences
            source_features = self.version_manager.get_feature_support(source_version)
            target_features = self.version_manager.get_feature_support(target_version)
            
            feature_differences = []
            for feature in source_features:
                if source_features[feature] != target_features.get(feature, False):
                    feature_differences.append({
                        "feature": feature,
                        "source_support": source_features[feature],
                        "target_support": target_features.get(feature, False)
                    })
            
            compatibility["feature_differences"] = feature_differences
            
            if feature_differences:
                compatibility["warnings"].append(
                    f"Found {len(feature_differences)} feature differences between versions"
                )
            
            # Remove duplicate warnings and recommendations
            compatibility["warnings"] = list(set(compatibility["warnings"]))
            compatibility["recommendations"] = list(set(compatibility["recommendations"]))
            
            self.logger.info("Version compatibility check completed", extra={
                "source_version": str(source_version),
                "target_version": str(target_version),
                "is_compatible": compatibility["is_compatible"],
                "warnings_count": len(compatibility["warnings"]),
                "errors_count": len(compatibility["errors"])
            })
            
            return compatibility
            
        except Exception as e:
            self.logger.error("Version compatibility check failed", extra={
                "error": str(e)
            })
            raise DatabaseVersionError(
                f"Version compatibility check failed: {str(e)}",
                original_error=e
            )
    
    async def get_version_report(self) -> Dict[str, Any]:
        """Generate comprehensive version report.
        
        Returns:
            Dictionary with version report information
        """
        try:
            # Detect versions if not already done
            versions = await self.detect_versions()
            
            # Check compatibility
            compatibility = await self.check_compatibility()
            
            # Get database connection info
            connection_info = await self.database_manager.get_connection_info()
            
            # Build comprehensive report
            report = {
                "report_timestamp": datetime.utcnow().isoformat(),
                "detection_results": self._detection_results,
                "version_details": {
                    "source": {
                        "version": str(versions["source"]),
                        "major": versions["source"].major,
                        "minor": versions["source"].minor,
                        "patch": versions["source"].patch,
                        "server_version_num": versions["source"].server_version_num,
                        "full_version": versions["source"].full_version,
                        "is_supported": self.version_manager.is_version_supported(versions["source"]),
                        "features": self.version_manager.get_feature_support(versions["source"]),
                        "recommendations": self.version_manager.get_version_recommendations(versions["source"])
                    },
                    "target": {
                        "version": str(versions["target"]),
                        "major": versions["target"].major,
                        "minor": versions["target"].minor,
                        "patch": versions["target"].patch,
                        "server_version_num": versions["target"].server_version_num,
                        "full_version": versions["target"].full_version,
                        "is_supported": self.version_manager.is_version_supported(versions["target"]),
                        "features": self.version_manager.get_feature_support(versions["target"]),
                        "recommendations": self.version_manager.get_version_recommendations(versions["target"])
                    }
                },
                "compatibility": compatibility,
                "connection_info": {
                    "source": connection_info["source"].to_dict() if connection_info["source"] else None,
                    "target": connection_info["target"].to_dict() if connection_info["target"] else None
                },
                "supported_version_range": self.version_manager.get_supported_version_range(),
                "pgsd_requirements": {
                    "min_version": DatabaseConstants.MIN_SUPPORTED_VERSION,
                    "recommended_version": DatabaseConstants.RECOMMENDED_VERSION
                }
            }
            
            # Add version changelog if versions are different
            if versions["source"] != versions["target"]:
                if versions["source"] < versions["target"]:
                    report["version_changelog"] = self.version_manager.get_version_changelog(
                        versions["source"], versions["target"]
                    )
                else:
                    report["version_changelog"] = self.version_manager.get_version_changelog(
                        versions["target"], versions["source"]
                    )
            
            self.logger.info("Version report generated", extra={
                "source_version": str(versions["source"]),
                "target_version": str(versions["target"]),
                "compatibility_status": compatibility["is_compatible"]
            })
            
            return report
            
        except Exception as e:
            self.logger.error("Version report generation failed", extra={
                "error": str(e)
            })
            raise DatabaseVersionError(
                f"Version report generation failed: {str(e)}",
                original_error=e
            )
    
    async def validate_operation_support(self, operation: str) -> Dict[str, bool]:
        """Validate if both databases support a specific operation.
        
        Args:
            operation: Operation name to validate
            
        Returns:
            Dictionary with support status for each database
        """
        versions = await self.detect_versions()
        
        return {
            "source_supports": self.version_manager.validate_version_for_operation(
                versions["source"], operation
            ),
            "target_supports": self.version_manager.validate_version_for_operation(
                versions["target"], operation
            )
        }
    
    def get_cached_versions(self) -> Optional[Dict[str, PostgreSQLVersion]]:
        """Get cached version information if available.
        
        Returns:
            Cached version information or None if not available
        """
        if self._source_version and self._target_version:
            return {
                "source": self._source_version,
                "target": self._target_version
            }
        return None
    
    def clear_cache(self):
        """Clear cached version information."""
        self._source_version = None
        self._target_version = None
        self._last_detection_time = None
        self._detection_results = {}
        
        self.logger.info("Version cache cleared")
    
    def get_detection_statistics(self) -> Dict[str, Any]:
        """Get version detection statistics.
        
        Returns:
            Dictionary with detection statistics
        """
        return {
            "has_cached_versions": bool(self._source_version and self._target_version),
            "last_detection_time": self._last_detection_time.isoformat() if self._last_detection_time else None,
            "cache_age_seconds": (datetime.utcnow() - self._last_detection_time).total_seconds() if self._last_detection_time else None,
            "detection_results": self._detection_results.copy()
        }
