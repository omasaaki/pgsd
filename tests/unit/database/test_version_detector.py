"""Tests for PostgreSQL version detection functionality."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from src.pgsd.database.version_detector import VersionDetector
from src.pgsd.database.manager import DatabaseManager
from src.pgsd.database.connector import DatabaseConnector
from src.pgsd.models.database import PostgreSQLVersion
from src.pgsd.exceptions.database import DatabaseVersionError


class TestVersionDetector:
    """Test cases for VersionDetector class."""

    @pytest.fixture
    def mock_database_manager(self):
        """Create mock database manager."""
        manager = Mock(spec=DatabaseManager)
        manager.config = Mock()
        manager.config.database.source.database = "source_db"
        manager.config.database.target.database = "target_db"
        return manager

    @pytest.fixture
    def mock_source_connector(self):
        """Create mock source connector."""
        connector = Mock(spec=DatabaseConnector)
        connector.get_version = AsyncMock(return_value=PostgreSQLVersion.parse("14.5"))
        return connector

    @pytest.fixture
    def mock_target_connector(self):
        """Create mock target connector."""
        connector = Mock(spec=DatabaseConnector)
        connector.get_version = AsyncMock(return_value=PostgreSQLVersion.parse("13.8"))
        return connector

    @pytest.fixture
    def version_detector(self, mock_database_manager):
        """Create version detector instance."""
        return VersionDetector(mock_database_manager)

    @pytest.mark.asyncio
    async def test_detect_versions_success(
        self,
        version_detector,
        mock_database_manager,
        mock_source_connector,
        mock_target_connector,
    ):
        """Test successful version detection."""
        # Setup mocks
        mock_database_manager.get_source_connection = AsyncMock(
            return_value=mock_source_connector
        )
        mock_database_manager.get_target_connection = AsyncMock(
            return_value=mock_target_connector
        )
        mock_database_manager.return_source_connection = Mock()
        mock_database_manager.return_target_connection = Mock()

        # Test version detection
        versions = await version_detector.detect_versions()

        # Verify results
        assert "source" in versions
        assert "target" in versions
        assert str(versions["source"]) == "14.5.0"
        assert str(versions["target"]) == "13.8.0"

        # Verify connections were returned
        mock_database_manager.return_source_connection.assert_called_once()
        mock_database_manager.return_target_connection.assert_called_once()

    @pytest.mark.asyncio
    async def test_detect_versions_cached(
        self,
        version_detector,
        mock_database_manager,
        mock_source_connector,
        mock_target_connector,
    ):
        """Test version detection with caching."""
        # Setup mocks
        mock_database_manager.get_source_connection = AsyncMock(
            return_value=mock_source_connector
        )
        mock_database_manager.get_target_connection = AsyncMock(
            return_value=mock_target_connector
        )
        mock_database_manager.return_source_connection = Mock()
        mock_database_manager.return_target_connection = Mock()

        # First detection
        versions1 = await version_detector.detect_versions()

        # Second detection (should use cache)
        versions2 = await version_detector.detect_versions()

        # Verify cache was used
        assert versions1 == versions2
        assert mock_database_manager.get_source_connection.call_count == 1
        assert mock_database_manager.get_target_connection.call_count == 1

    @pytest.mark.asyncio
    async def test_detect_versions_force_refresh(
        self,
        version_detector,
        mock_database_manager,
        mock_source_connector,
        mock_target_connector,
    ):
        """Test version detection with forced cache refresh."""
        # Setup mocks
        mock_database_manager.get_source_connection = AsyncMock(
            return_value=mock_source_connector
        )
        mock_database_manager.get_target_connection = AsyncMock(
            return_value=mock_target_connector
        )
        mock_database_manager.return_source_connection = Mock()
        mock_database_manager.return_target_connection = Mock()

        # First detection
        await version_detector.detect_versions()

        # Force refresh
        await version_detector.detect_versions(force_refresh=True)

        # Verify both detections were performed
        assert mock_database_manager.get_source_connection.call_count == 2
        assert mock_database_manager.get_target_connection.call_count == 2

    @pytest.mark.asyncio
    async def test_detect_versions_source_failure(
        self, version_detector, mock_database_manager
    ):
        """Test version detection failure for source database."""
        # Setup mock to fail for source
        mock_database_manager.get_source_connection = AsyncMock(
            side_effect=Exception("Source connection failed")
        )

        # Test version detection failure
        with pytest.raises(
            DatabaseVersionError, match="Source database version detection failed"
        ):
            await version_detector.detect_versions()

    @pytest.mark.asyncio
    async def test_detect_versions_target_failure(
        self, version_detector, mock_database_manager, mock_source_connector
    ):
        """Test version detection failure for target database."""
        # Setup mocks
        mock_database_manager.get_source_connection = AsyncMock(
            return_value=mock_source_connector
        )
        mock_database_manager.get_target_connection = AsyncMock(
            side_effect=Exception("Target connection failed")
        )
        mock_database_manager.return_source_connection = Mock()

        # Test version detection failure
        with pytest.raises(
            DatabaseVersionError, match="Target database version detection failed"
        ):
            await version_detector.detect_versions()

    @pytest.mark.asyncio
    async def test_check_compatibility_supported_versions(self, version_detector):
        """Test compatibility check with supported versions."""
        source_version = PostgreSQLVersion.parse("14.5")
        target_version = PostgreSQLVersion.parse("13.8")

        compatibility = await version_detector.check_compatibility(
            source_version, target_version
        )

        # Verify compatibility result
        assert compatibility["is_compatible"] is True
        assert compatibility["source_version"] == "14.5.0"
        assert compatibility["target_version"] == "13.8.0"
        assert "version_comparison" in compatibility
        assert "feature_differences" in compatibility

    @pytest.mark.asyncio
    async def test_check_compatibility_unsupported_version(self, version_detector):
        """Test compatibility check with unsupported version."""
        source_version = PostgreSQLVersion.parse("12.5")  # Below minimum
        target_version = PostgreSQLVersion.parse("14.0")

        compatibility = await version_detector.check_compatibility(
            source_version, target_version
        )

        # Verify compatibility result
        assert compatibility["is_compatible"] is False
        assert len(compatibility["errors"]) > 0
        assert "not supported" in compatibility["errors"][0]

    @pytest.mark.asyncio
    async def test_check_compatibility_feature_differences(self, version_detector):
        """Test compatibility check with feature differences."""
        source_version = PostgreSQLVersion.parse("13.0")  # No incremental sorting
        target_version = PostgreSQLVersion.parse("14.0")  # Has incremental sorting

        compatibility = await version_detector.check_compatibility(
            source_version, target_version
        )

        # Verify feature differences are detected
        assert len(compatibility["feature_differences"]) > 0
        feature_names = [fd["feature"] for fd in compatibility["feature_differences"]]
        assert (
            "incremental_sorting" in feature_names
            or "multirange_types" in feature_names
        )

    @pytest.mark.asyncio
    async def test_get_version_report(
        self,
        version_detector,
        mock_database_manager,
        mock_source_connector,
        mock_target_connector,
    ):
        """Test version report generation."""
        # Setup mocks
        mock_database_manager.get_source_connection = AsyncMock(
            return_value=mock_source_connector
        )
        mock_database_manager.get_target_connection = AsyncMock(
            return_value=mock_target_connector
        )
        mock_database_manager.return_source_connection = Mock()
        mock_database_manager.return_target_connection = Mock()
        mock_database_manager.get_connection_info = AsyncMock(
            return_value={
                "source": Mock(to_dict=Mock(return_value={})),
                "target": Mock(to_dict=Mock(return_value={})),
            }
        )

        # Generate report
        report = await version_detector.get_version_report()

        # Verify report structure
        assert "report_timestamp" in report
        assert "detection_results" in report
        assert "version_details" in report
        assert "compatibility" in report
        assert "connection_info" in report
        assert "supported_version_range" in report
        assert "pgsd_requirements" in report

        # Verify version details
        assert "source" in report["version_details"]
        assert "target" in report["version_details"]
        assert "version" in report["version_details"]["source"]
        assert "features" in report["version_details"]["source"]

    @pytest.mark.asyncio
    async def test_validate_operation_support(
        self,
        version_detector,
        mock_database_manager,
        mock_source_connector,
        mock_target_connector,
    ):
        """Test operation support validation."""
        # Setup mocks
        mock_database_manager.get_source_connection = AsyncMock(
            return_value=mock_source_connector
        )
        mock_database_manager.get_target_connection = AsyncMock(
            return_value=mock_target_connector
        )
        mock_database_manager.return_source_connection = Mock()
        mock_database_manager.return_target_connection = Mock()

        # Test basic operation support
        support = await version_detector.validate_operation_support("schema_info")

        # Verify support result
        assert "source_supports" in support
        assert "target_supports" in support
        assert support["source_supports"] is True
        assert support["target_supports"] is True

    def test_get_cached_versions_empty(self, version_detector):
        """Test getting cached versions when cache is empty."""
        cached = version_detector.get_cached_versions()
        assert cached is None

    @pytest.mark.asyncio
    async def test_get_cached_versions_populated(
        self,
        version_detector,
        mock_database_manager,
        mock_source_connector,
        mock_target_connector,
    ):
        """Test getting cached versions when cache is populated."""
        # Setup mocks
        mock_database_manager.get_source_connection = AsyncMock(
            return_value=mock_source_connector
        )
        mock_database_manager.get_target_connection = AsyncMock(
            return_value=mock_target_connector
        )
        mock_database_manager.return_source_connection = Mock()
        mock_database_manager.return_target_connection = Mock()

        # Populate cache
        await version_detector.detect_versions()

        # Get cached versions
        cached = version_detector.get_cached_versions()

        assert cached is not None
        assert "source" in cached
        assert "target" in cached
        assert str(cached["source"]) == "14.5.0"
        assert str(cached["target"]) == "13.8.0"

    def test_clear_cache(self, version_detector):
        """Test cache clearing."""
        # Manually set cache
        version_detector._source_version = PostgreSQLVersion.parse("14.0")
        version_detector._target_version = PostgreSQLVersion.parse("13.0")
        version_detector._last_detection_time = datetime.utcnow()

        # Clear cache
        version_detector.clear_cache()

        # Verify cache is cleared
        assert version_detector._source_version is None
        assert version_detector._target_version is None
        assert version_detector._last_detection_time is None
        assert version_detector._detection_results == {}

    def test_get_detection_statistics_empty(self, version_detector):
        """Test getting detection statistics when cache is empty."""
        stats = version_detector.get_detection_statistics()

        assert stats["has_cached_versions"] is False
        assert stats["last_detection_time"] is None
        assert stats["cache_age_seconds"] is None
        assert stats["detection_results"] == {}

    @pytest.mark.asyncio
    async def test_get_detection_statistics_populated(
        self,
        version_detector,
        mock_database_manager,
        mock_source_connector,
        mock_target_connector,
    ):
        """Test getting detection statistics when cache is populated."""
        # Setup mocks
        mock_database_manager.get_source_connection = AsyncMock(
            return_value=mock_source_connector
        )
        mock_database_manager.get_target_connection = AsyncMock(
            return_value=mock_target_connector
        )
        mock_database_manager.return_source_connection = Mock()
        mock_database_manager.return_target_connection = Mock()

        # Populate cache
        await version_detector.detect_versions()

        # Get statistics
        stats = version_detector.get_detection_statistics()

        assert stats["has_cached_versions"] is True
        assert stats["last_detection_time"] is not None
        assert stats["cache_age_seconds"] is not None
        assert stats["cache_age_seconds"] >= 0
        assert len(stats["detection_results"]) > 0


class TestVersionDetectorIntegration:
    """Integration tests for VersionDetector."""

    @pytest.mark.asyncio
    async def test_version_detection_integration(self):
        """Test version detection integration with mock database."""
        # This would be an integration test with actual database connections
        # For now, we'll skip this as it requires actual PostgreSQL instances
        pytest.skip("Integration test requires actual PostgreSQL instances")

    @pytest.mark.asyncio
    async def test_compatibility_check_integration(self):
        """Test compatibility check integration."""
        # This would be an integration test with actual database connections
        pytest.skip("Integration test requires actual PostgreSQL instances")


class TestVersionDetectorEdgeCases:
    """Edge case tests for VersionDetector."""

    @pytest.fixture
    def mock_database_manager(self):
        """Create mock database manager."""
        manager = Mock(spec=DatabaseManager)
        manager.config = Mock()
        manager.config.database.source.database = "source_db"
        manager.config.database.target.database = "target_db"
        return manager

    @pytest.fixture
    def version_detector(self, mock_database_manager):
        """Create version detector instance."""
        return VersionDetector(mock_database_manager)

    @pytest.fixture
    def mock_source_connector(self):
        """Create mock source connector."""
        connector = Mock(spec=DatabaseConnector)
        connector.get_version = AsyncMock(return_value=PostgreSQLVersion.parse("14.5"))
        connector.execute_query = AsyncMock(return_value=[{"version": "PostgreSQL 14.5"}])
        return connector

    @pytest.fixture
    def mock_target_connector(self):
        """Create mock target connector."""
        connector = Mock(spec=DatabaseConnector)
        connector.get_version = AsyncMock(return_value=PostgreSQLVersion.parse("13.8"))
        connector.execute_query = AsyncMock(return_value=[{"version": "PostgreSQL 13.8"}])
        return connector

    @pytest.mark.asyncio
    async def test_concurrent_version_detection(
        self,
        version_detector,
        mock_database_manager,
        mock_source_connector,
        mock_target_connector,
    ):
        """Test concurrent version detection calls."""
        # Setup mocks
        mock_database_manager.get_source_connection = AsyncMock(
            return_value=mock_source_connector
        )
        mock_database_manager.get_target_connection = AsyncMock(
            return_value=mock_target_connector
        )
        mock_database_manager.return_source_connection = Mock()
        mock_database_manager.return_target_connection = Mock()

        # Run concurrent detections
        tasks = [version_detector.detect_versions() for _ in range(3)]
        results = await asyncio.gather(*tasks)

        # Verify all results are the same
        for result in results:
            assert str(result["source"]) == "14.5.0"
            assert str(result["target"]) == "13.8.0"

    @pytest.mark.asyncio
    async def test_version_detection_with_connection_timeout(
        self, version_detector, mock_database_manager
    ):
        """Test version detection with connection timeout."""
        # Setup mock to timeout
        mock_database_manager.get_source_connection = AsyncMock(
            side_effect=asyncio.TimeoutError("Connection timeout")
        )

        # Test timeout handling
        with pytest.raises(DatabaseVersionError):
            await version_detector.detect_versions()

    @pytest.mark.asyncio
    async def test_malformed_version_string(
        self, version_detector, mock_database_manager
    ):
        """Test handling of malformed version strings."""
        # Setup mock connector with malformed version
        mock_connector = Mock(spec=DatabaseConnector)
        mock_connector.get_version = AsyncMock(
            side_effect=Exception("Invalid version format")
        )

        mock_database_manager.get_source_connection = AsyncMock(
            return_value=mock_connector
        )

        # Test error handling
        with pytest.raises(DatabaseVersionError):
            await version_detector.detect_versions()
