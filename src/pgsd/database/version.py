"""PostgreSQL version management for PGSD application."""

import logging
from typing import Optional, List, Dict, Any

from ..constants.database import DatabaseConstants
from ..exceptions.database import DatabaseVersionError
from ..models.database import PostgreSQLVersion


class VersionManager:
    """PostgreSQL version management and compatibility checking."""
    
    def __init__(self):
        """Initialize version manager."""
        self.logger = logging.getLogger(__name__)
        
        # Supported versions
        self.min_supported_version = PostgreSQLVersion.parse(DatabaseConstants.MIN_SUPPORTED_VERSION)
        self.recommended_version = PostgreSQLVersion.parse(DatabaseConstants.RECOMMENDED_VERSION)
        
        # Version-specific feature support
        self._feature_support = {
            "13.0": {
                "partitioned_tables": True,
                "generated_columns": True,
                "b_tree_deduplication": True,
                "incremental_sorting": False,
                "multirange_types": False
            },
            "14.0": {
                "partitioned_tables": True,
                "generated_columns": True,
                "b_tree_deduplication": True,
                "incremental_sorting": True,
                "multirange_types": True
            },
            "15.0": {
                "partitioned_tables": True,
                "generated_columns": True,
                "b_tree_deduplication": True,
                "incremental_sorting": True,
                "multirange_types": True,
                "merge_command": True
            }
        }
    
    def check_version_compatibility(self, version: PostgreSQLVersion) -> Dict[str, Any]:
        """Check version compatibility with PGSD requirements.
        
        Args:
            version: PostgreSQL version to check
            
        Returns:
            Dictionary with compatibility information
        """
        compatibility = {
            "is_supported": False,
            "is_recommended": False,
            "warnings": [],
            "features": {},
            "upgrade_recommendation": None
        }
        
        # Check minimum version support
        if version >= self.min_supported_version:
            compatibility["is_supported"] = True
        else:
            compatibility["warnings"].append(
                f"Version {version} is below minimum supported version {self.min_supported_version}"
            )
        
        # Check recommended version
        if version >= self.recommended_version:
            compatibility["is_recommended"] = True
        else:
            compatibility["warnings"].append(
                f"Version {version} is below recommended version {self.recommended_version}"
            )
            compatibility["upgrade_recommendation"] = f"Consider upgrading to PostgreSQL {self.recommended_version} or later"
        
        # Get feature support
        compatibility["features"] = self.get_feature_support(version)
        
        # Version-specific warnings
        if version.major < 14:
            compatibility["warnings"].append(
                "This PostgreSQL version may have limited schema comparison features"
            )
        
        self.logger.debug("Version compatibility check completed", extra={
            "version": str(version),
            "is_supported": compatibility["is_supported"],
            "is_recommended": compatibility["is_recommended"],
            "warnings_count": len(compatibility["warnings"])
        })
        
        return compatibility
    
    def get_feature_support(self, version: PostgreSQLVersion) -> Dict[str, bool]:
        """Get feature support for specific version.
        
        Args:
            version: PostgreSQL version
            
        Returns:
            Dictionary of feature support
        """
        # Find closest supported version
        version_key = f"{version.major}.{version.minor}"
        
        # Try exact match first
        if version_key in self._feature_support:
            return self._feature_support[version_key].copy()
        
        # Try major version match
        major_key = f"{version.major}.0"
        if major_key in self._feature_support:
            return self._feature_support[major_key].copy()
        
        # Fall back to closest lower version
        available_versions = sorted(
            [PostgreSQLVersion.parse(v) for v in self._feature_support.keys()],
            reverse=True
        )
        
        for available_version in available_versions:
            if version >= available_version:
                version_key = f"{available_version.major}.{available_version.minor}"
                return self._feature_support[version_key].copy()
        
        # Default minimal feature set
        return {
            "partitioned_tables": False,
            "generated_columns": False,
            "b_tree_deduplication": False,
            "incremental_sorting": False,
            "multirange_types": False
        }
    
    def compare_versions(self, version1: PostgreSQLVersion, version2: PostgreSQLVersion) -> Dict[str, Any]:
        """Compare two PostgreSQL versions.
        
        Args:
            version1: First version
            version2: Second version
            
        Returns:
            Dictionary with comparison results
        """
        comparison = {
            "version1": str(version1),
            "version2": str(version2),
            "are_equal": version1 == version2,
            "version1_newer": version1 > version2,
            "version2_newer": version2 > version1,
            "major_version_diff": version1.major != version2.major,
            "minor_version_diff": version1.minor != version2.minor,
            "patch_version_diff": version1.patch != version2.patch,
            "compatibility_concerns": []
        }
        
        # Check for compatibility concerns
        if comparison["major_version_diff"]:
            comparison["compatibility_concerns"].append(
                "Major version difference may cause schema comparison issues"
            )
        
        if abs(version1.major - version2.major) > 2:
            comparison["compatibility_concerns"].append(
                "Large version gap may cause significant compatibility issues"
            )
        
        # Feature support comparison
        features1 = self.get_feature_support(version1)
        features2 = self.get_feature_support(version2)
        
        feature_diff = []
        for feature in features1:
            if features1[feature] != features2.get(feature, False):
                feature_diff.append(feature)
        
        comparison["feature_differences"] = feature_diff
        
        return comparison
    
    def get_version_recommendations(self, version: PostgreSQLVersion) -> List[str]:
        """Get recommendations for specific version.
        
        Args:
            version: PostgreSQL version
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Basic version recommendations
        if version < self.min_supported_version:
            recommendations.append(
                f"Upgrade to PostgreSQL {self.min_supported_version} or later for full PGSD support"
            )
        elif version < self.recommended_version:
            recommendations.append(
                f"Consider upgrading to PostgreSQL {self.recommended_version} for optimal performance"
            )
        
        # Feature-specific recommendations
        features = self.get_feature_support(version)
        
        if not features.get("incremental_sorting", False):
            recommendations.append(
                "Upgrade to PostgreSQL 14+ for improved query performance with incremental sorting"
            )
        
        if not features.get("multirange_types", False):
            recommendations.append(
                "Upgrade to PostgreSQL 14+ for multirange type support"
            )
        
        # Security recommendations
        if version.major < 14:
            recommendations.append(
                "Consider upgrading for latest security patches and improvements"
            )
        
        return recommendations
    
    def validate_version_for_operation(self, version: PostgreSQLVersion, operation: str) -> bool:
        """Validate version for specific operation.
        
        Args:
            version: PostgreSQL version
            operation: Operation name
            
        Returns:
            True if version supports the operation
        """
        # Basic operations supported by all versions
        basic_operations = [
            "schema_info",
            "table_info",
            "column_info",
            "constraint_info",
            "index_info"
        ]
        
        if operation in basic_operations:
            return version >= self.min_supported_version
        
        # Advanced operations with version requirements
        advanced_operations = {
            "partitioned_table_info": "13.0",
            "generated_column_info": "13.0",
            "multirange_type_info": "14.0",
            "merge_command_info": "15.0"
        }
        
        if operation in advanced_operations:
            required_version = PostgreSQLVersion.parse(advanced_operations[operation])
            return version >= required_version
        
        # Unknown operation - require minimum version
        return version >= self.min_supported_version
    
    def get_version_changelog(self, from_version: PostgreSQLVersion, to_version: PostgreSQLVersion) -> List[str]:
        """Get changelog between versions.
        
        Args:
            from_version: Starting version
            to_version: Target version
            
        Returns:
            List of changes between versions
        """
        if from_version >= to_version:
            return []
        
        changelog = []
        
        # Major version changes
        if from_version.major < 14 and to_version.major >= 14:
            changelog.extend([
                "Added incremental sorting support",
                "Added multirange types",
                "Improved performance for partitioned tables",
                "Enhanced JSON functionality"
            ])
        
        if from_version.major < 15 and to_version.major >= 15:
            changelog.extend([
                "Added MERGE command support",
                "Improved logical replication",
                "Enhanced security features",
                "Better query performance"
            ])
        
        # Minor version changes (example)
        if from_version.minor < to_version.minor:
            changelog.append("Bug fixes and performance improvements")
        
        return changelog
    
    @staticmethod
    def parse_version_string(version_string: str) -> PostgreSQLVersion:
        """Parse version string to PostgreSQLVersion object.
        
        Args:
            version_string: Version string to parse
            
        Returns:
            PostgreSQLVersion object
            
        Raises:
            DatabaseVersionError: If version string is invalid
        """
        try:
            return PostgreSQLVersion.parse(version_string)
        except Exception as e:
            raise DatabaseVersionError(
                f"Invalid version string '{version_string}': {str(e)}",
                original_error=e
            )
    
    def is_version_supported(self, version: PostgreSQLVersion) -> bool:
        """Check if version is supported by PGSD.
        
        Args:
            version: PostgreSQL version
            
        Returns:
            True if version is supported
        """
        return version >= self.min_supported_version
    
    def get_supported_version_range(self) -> Dict[str, PostgreSQLVersion]:
        """Get supported version range.
        
        Returns:
            Dictionary with min and max supported versions
        """
        return {
            "min_version": self.min_supported_version,
            "recommended_version": self.recommended_version
        }
