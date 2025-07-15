"""Integration tests for the core schema comparison engine."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.pgsd.core.engine import SchemaComparisonEngine
from src.pgsd.config.manager import ConfigurationManager
from src.pgsd.models.schema import SchemaInfo, TableInfo, ColumnInfo
from src.pgsd.exceptions.processing import ProcessingError
from src.pgsd.exceptions.database import DatabaseConnectionError


class TestSchemaComparisonEngineIntegration:
    """Integration tests for SchemaComparisonEngine."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration manager."""
        config = Mock(spec=ConfigurationManager)
        config.database = {
            "source": {
                "host": "localhost",
                "port": 5432,
                "database": "test_source",
                "username": "test_user",
                "password": "test_pass",
            },
            "target": {
                "host": "localhost",
                "port": 5432,
                "database": "test_target",
                "username": "test_user",
                "password": "test_pass",
            },
        }
        return config

    @pytest.fixture
    def engine(self, mock_config):
        """Create a schema comparison engine instance."""
        return SchemaComparisonEngine(mock_config)

    @pytest.fixture
    def sample_schema_info_source(self):
        """Create sample source schema information."""
        columns = [
            ColumnInfo(
                column_name="id",
                ordinal_position=1,
                data_type="integer",
                is_nullable=False,
            ),
            ColumnInfo(
                column_name="name",
                ordinal_position=2,
                data_type="character varying",
                is_nullable=True,
                character_maximum_length=100,
            ),
        ]

        table = TableInfo(
            table_name="users",
            table_schema="public",
            table_type="BASE TABLE",
            columns=columns,
        )

        return SchemaInfo(
            schema_name="public",
            database_type="source",
            collection_time=datetime(2025, 7, 14, 10, 0, 0),
            tables=[table],
        )

    @pytest.fixture
    def sample_schema_info_target(self):
        """Create sample target schema information."""
        columns = [
            ColumnInfo(
                column_name="id",
                ordinal_position=1,
                data_type="integer",
                is_nullable=False,
            ),
            ColumnInfo(
                column_name="name",
                ordinal_position=2,
                data_type="character varying",
                is_nullable=True,
                character_maximum_length=150,  # Changed length
            ),
            ColumnInfo(
                column_name="email",  # New column
                ordinal_position=3,
                data_type="character varying",
                is_nullable=True,
                character_maximum_length=255,
            ),
        ]

        table = TableInfo(
            table_name="users",
            table_schema="public",
            table_type="BASE TABLE",
            columns=columns,
        )

        return SchemaInfo(
            schema_name="public",
            database_type="target",
            collection_time=datetime(2025, 7, 14, 10, 30, 0),
            tables=[table],
        )

    def test_engine_initialization(self, engine, mock_config):
        """Test engine initialization."""
        assert engine.config == mock_config
        assert engine.database_manager is None
        assert engine.schema_collector is None
        assert engine.diff_analyzer is not None
        assert not engine._initialized

    def test_engine_repr(self, engine):
        """Test engine string representation."""
        assert "not initialized" in repr(engine)

    @pytest.mark.asyncio
    async def test_initialize_success(self, engine):
        """Test successful engine initialization."""
        with patch(
            "src.pgsd.core.engine.DatabaseManager"
        ) as mock_db_manager_class, patch(
            "src.pgsd.core.engine.SchemaInformationCollector"
        ) as mock_collector_class:

            # Setup mocks
            mock_db_manager = AsyncMock()
            mock_db_manager.initialize = AsyncMock()
            mock_db_manager_class.return_value = mock_db_manager

            mock_collector = Mock()
            mock_collector_class.return_value = mock_collector

            # Initialize
            await engine.initialize()

            # Verify initialization
            assert engine._initialized
            assert engine.database_manager == mock_db_manager
            assert engine.schema_collector == mock_collector
            mock_db_manager.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_failure(self, engine):
        """Test engine initialization failure."""
        with patch("src.pgsd.core.engine.DatabaseManager") as mock_db_manager_class:
            mock_db_manager_class.side_effect = Exception("Database error")

            with pytest.raises(ProcessingError, match="Engine initialization failed"):
                await engine.initialize()

            assert not engine._initialized

    @pytest.mark.asyncio
    async def test_compare_schemas_not_initialized(self, engine):
        """Test schema comparison when engine not initialized."""
        with pytest.raises(ProcessingError, match="Engine not initialized"):
            await engine.compare_schemas("public", "public")

    @pytest.mark.asyncio
    async def test_compare_schemas_success(
        self, engine, sample_schema_info_source, sample_schema_info_target
    ):
        """Test successful schema comparison."""
        # Mock initialization
        engine._initialized = True
        engine.schema_collector = AsyncMock()
        engine.schema_collector.collect_schema_info.side_effect = [
            sample_schema_info_source,
            sample_schema_info_target,
        ]

        # Perform comparison
        result = await engine.compare_schemas("public", "public")

        # Verify results
        assert result is not None
        assert hasattr(result, "summary")
        assert hasattr(result, "metadata")
        assert result.metadata["source_schema"] == "public"
        assert result.metadata["target_schema"] == "public"
        assert "analysis_time_seconds" in result.metadata
        assert "comparison_timestamp" in result.metadata

    @pytest.mark.asyncio
    async def test_compare_schemas_collection_failure(self, engine):
        """Test schema comparison with collection failure."""
        engine._initialized = True
        engine.schema_collector = AsyncMock()
        engine.schema_collector.collect_schema_info.side_effect = (
            DatabaseConnectionError(
                host="localhost", port=5432, database="test_db", user="test_user"
            )
        )

        with pytest.raises(DatabaseConnectionError):
            await engine.compare_schemas("public", "public")

    @pytest.mark.asyncio
    async def test_get_available_schemas_not_initialized(self, engine):
        """Test getting available schemas when engine not initialized."""
        with pytest.raises(ProcessingError, match="Engine not initialized"):
            await engine.get_available_schemas()

    @pytest.mark.asyncio
    async def test_get_available_schemas_success(self, engine):
        """Test successful retrieval of available schemas."""
        engine._initialized = True
        engine.schema_collector = AsyncMock()
        engine.schema_collector.get_available_schemas.return_value = [
            "public",
            "information_schema",
            "pg_catalog",
        ]

        schemas = await engine.get_available_schemas("source")

        assert len(schemas) == 3
        assert "public" in schemas
        assert "information_schema" in schemas
        assert "pg_catalog" in schemas

    @pytest.mark.asyncio
    async def test_validate_schema_exists_true(self, engine):
        """Test schema validation when schema exists."""
        engine._initialized = True
        engine.schema_collector = AsyncMock()
        engine.schema_collector.get_available_schemas.return_value = [
            "public",
            "test_schema",
        ]

        exists = await engine.validate_schema_exists("public", "source")
        assert exists is True

    @pytest.mark.asyncio
    async def test_validate_schema_exists_false(self, engine):
        """Test schema validation when schema doesn't exist."""
        engine._initialized = True
        engine.schema_collector = AsyncMock()
        engine.schema_collector.get_available_schemas.return_value = [
            "public",
            "test_schema",
        ]

        exists = await engine.validate_schema_exists("nonexistent", "source")
        assert exists is False

    @pytest.mark.asyncio
    async def test_get_schema_summary_success(self, engine, sample_schema_info_source):
        """Test successful schema summary generation."""
        engine._initialized = True
        engine.schema_collector = AsyncMock()
        engine.schema_collector.get_available_schemas.return_value = ["public"]
        engine.schema_collector.collect_schema_info.return_value = (
            sample_schema_info_source
        )

        summary = await engine.get_schema_summary("public", "source")

        assert summary["schema_name"] == "public"
        assert summary["database_type"] == "source"
        assert "collection_time" in summary
        assert "object_counts" in summary
        assert len(summary["tables"]) == 1
        assert summary["tables"][0]["name"] == "users"
        assert summary["tables"][0]["columns"] == 2

    @pytest.mark.asyncio
    async def test_get_schema_summary_schema_not_found(self, engine):
        """Test schema summary when schema doesn't exist."""
        engine._initialized = True
        engine.schema_collector = AsyncMock()
        engine.schema_collector.get_available_schemas.return_value = ["public"]

        with pytest.raises(ProcessingError, match="Schema 'nonexistent' not found"):
            await engine.get_schema_summary("nonexistent", "source")

    @pytest.mark.asyncio
    async def test_cleanup_success(self, engine):
        """Test successful cleanup."""
        # Setup initialized engine
        engine._initialized = True
        engine.database_manager = AsyncMock()
        engine.database_manager.close_all = AsyncMock()

        await engine.cleanup()

        engine.database_manager.close_all.assert_called_once()
        assert not engine._initialized

    @pytest.mark.asyncio
    async def test_cleanup_with_error(self, engine):
        """Test cleanup with error (should not raise)."""
        engine._initialized = True
        engine.database_manager = AsyncMock()
        engine.database_manager.close_all.side_effect = Exception("Cleanup error")

        # Should not raise exception
        await engine.cleanup()
        assert not engine._initialized

    @pytest.mark.asyncio
    async def test_context_manager(self, engine):
        """Test engine as async context manager."""
        with patch.object(engine, "initialize") as mock_init, patch.object(
            engine, "cleanup"
        ) as mock_cleanup:

            mock_init.return_value = None
            mock_cleanup.return_value = None

            async with engine as eng:
                assert eng == engine
                mock_init.assert_called_once()

            mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_end_to_end_comparison(
        self, engine, sample_schema_info_source, sample_schema_info_target
    ):
        """Test end-to-end schema comparison workflow."""
        with patch(
            "src.pgsd.core.engine.DatabaseManager"
        ) as mock_db_manager_class, patch(
            "src.pgsd.core.engine.SchemaInformationCollector"
        ) as mock_collector_class:

            # Setup mocks
            mock_db_manager = AsyncMock()
            mock_db_manager.initialize = AsyncMock()
            mock_db_manager_class.return_value = mock_db_manager

            mock_collector = AsyncMock()
            mock_collector.collect_schema_info.side_effect = [
                sample_schema_info_source,
                sample_schema_info_target,
            ]
            mock_collector_class.return_value = mock_collector

            # Initialize and run comparison
            await engine.initialize()
            result = await engine.compare_schemas("public", "public")

            # Verify the comparison detected changes
            assert result.summary["total_changes"] > 0
            assert len(result.columns["added"]) == 1  # email column added
            assert len(result.columns["modified"]) == 1  # name column length changed

            # Verify metadata
            assert result.metadata["source_schema"] == "public"
            assert result.metadata["target_schema"] == "public"

            # Cleanup
            await engine.cleanup()

    @pytest.mark.asyncio
    async def test_performance_with_large_schemas(self, engine):
        """Test engine performance with larger schemas."""
        # Create larger schema data
        tables = []
        for i in range(20):  # 20 tables
            columns = []
            for j in range(10):  # 10 columns each
                columns.append(
                    ColumnInfo(
                        column_name=f"col_{j}",
                        ordinal_position=j + 1,
                        data_type="character varying",
                        is_nullable=True,
                    )
                )

            tables.append(
                TableInfo(
                    table_name=f"table_{i}",
                    table_schema="public",
                    table_type="BASE TABLE",
                    columns=columns,
                )
            )

        large_schema_source = SchemaInfo(
            schema_name="public",
            database_type="source",
            collection_time=datetime.now(),
            tables=tables,
        )

        large_schema_target = SchemaInfo(
            schema_name="public",
            database_type="target",
            collection_time=datetime.now(),
            tables=tables,  # Identical for performance test
        )

        # Mock setup
        engine._initialized = True
        engine.schema_collector = AsyncMock()
        engine.schema_collector.collect_schema_info.side_effect = [
            large_schema_source,
            large_schema_target,
        ]

        # Measure performance
        import time

        start_time = time.time()
        result = await engine.compare_schemas("public", "public")
        execution_time = time.time() - start_time

        # Verify reasonable performance (should complete quickly)
        assert execution_time < 1.0  # Less than 1 second
        assert result.summary["total_changes"] == 0  # Identical schemas
