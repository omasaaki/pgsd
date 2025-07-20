"""Tests for schema information collector."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta, timezone

from src.pgsd.schema.collector import SchemaInformationCollector
from src.pgsd.database.manager import DatabaseManager
from src.pgsd.database.connector import DatabaseConnector
from src.pgsd.exceptions.database import (
    SchemaCollectionError,
    DatabaseQueryError,
)


class TestSchemaInformationCollector:
    """Test cases for SchemaInformationCollector class."""

    @pytest.fixture
    def mock_database_manager(self):
        """Create mock database manager."""
        manager = Mock(spec=DatabaseManager)
        manager.config = Mock()
        return manager

    @pytest.fixture
    def mock_connector(self):
        """Create mock database connector."""
        connector = Mock(spec=DatabaseConnector)
        connector.verify_schema_access = AsyncMock(return_value=True)
        connector.execute_query = AsyncMock()
        return connector

    @pytest.fixture
    def schema_collector(self, mock_database_manager):
        """Create schema collector instance."""
        return SchemaInformationCollector(mock_database_manager)

    @pytest.fixture
    def sample_table_data(self):
        """Sample table data for testing."""
        return [
            {
                "table_name": "users",
                "table_type": "BASE TABLE",
                "table_schema": "public",
                "table_comment": "User information table",
                "estimated_rows": 1000,
                "table_size": "48 kB",
            },
            {
                "table_name": "posts",
                "table_type": "BASE TABLE",
                "table_schema": "public",
                "table_comment": None,
                "estimated_rows": 5000,
                "table_size": "120 kB",
            },
        ]

    @pytest.fixture
    def sample_column_data(self):
        """Sample column data for testing."""
        return [
            {
                "column_name": "id",
                "ordinal_position": 1,
                "column_default": "nextval('users_id_seq'::regclass)",
                "is_nullable": "NO",
                "data_type": "integer",
                "character_maximum_length": None,
                "numeric_precision": 32,
                "numeric_scale": 0,
                "udt_name": "int4",
                "column_comment": "Primary key",
            },
            {
                "column_name": "username",
                "ordinal_position": 2,
                "column_default": None,
                "is_nullable": "NO",
                "data_type": "character varying",
                "character_maximum_length": 50,
                "numeric_precision": None,
                "numeric_scale": None,
                "udt_name": "varchar",
                "column_comment": "Username",
            },
        ]

    @pytest.mark.asyncio
    async def test_collect_schema_info_success(
        self,
        schema_collector,
        mock_database_manager,
        mock_connector,
        sample_table_data,
        sample_column_data,
    ):
        """Test successful schema information collection."""
        # Setup mocks
        mock_database_manager.get_source_connection = AsyncMock(
            return_value=mock_connector
        )
        mock_database_manager.return_source_connection = Mock()

        # Setup query responses
        query_responses = {
            # Tables query
            0: sample_table_data,
            # Columns query (called twice for two tables)
            1: sample_column_data,
            2: sample_column_data,
            # Views query
            3: [],
            # Sequences query
            4: [],
            # Functions query
            5: [],
            # Indexes query
            6: [],
            # Triggers query
            7: [],
            # Constraints query
            8: [],
        }

        call_count = 0

        async def mock_execute_query(*args, **kwargs):
            nonlocal call_count
            result = query_responses.get(call_count, [])
            call_count += 1
            return result

        mock_connector.execute_query = mock_execute_query

        # Test schema collection
        schema_info = await schema_collector.collect_schema_info("public", "source")

        # Verify results
        assert schema_info.schema_name == "public"
        assert schema_info.database_type == "source"
        assert schema_info.collection_time is not None
        assert len(schema_info.tables) == 2
        assert schema_info.tables[0].table_name == "users"
        assert schema_info.tables[1].table_name == "posts"

        # Verify tables have columns
        assert hasattr(schema_info.tables[0], "columns")
        assert hasattr(schema_info.tables[1], "columns")

        # Verify connection was returned
        mock_database_manager.return_source_connection.assert_called_once()

    @pytest.mark.asyncio
    async def test_collect_schema_info_cached(
        self,
        schema_collector,
        mock_database_manager,
        mock_connector,
        sample_table_data,
        sample_column_data,
    ):
        """Test schema information collection with caching."""
        # Setup mocks
        mock_database_manager.get_source_connection = AsyncMock(
            return_value=mock_connector
        )
        mock_database_manager.return_source_connection = Mock()

        # Setup basic query response
        mock_connector.execute_query = AsyncMock(return_value=[])

        # First collection
        schema_info1 = await schema_collector.collect_schema_info("public", "source")

        # Second collection (should use cache)
        schema_info2 = await schema_collector.collect_schema_info("public", "source")

        # Verify cache was used
        assert schema_info1 == schema_info2
        assert mock_database_manager.get_source_connection.call_count == 1
        assert mock_database_manager.return_source_connection.call_count == 1

    @pytest.mark.asyncio
    async def test_collect_schema_info_permission_error(
        self, schema_collector, mock_database_manager, mock_connector
    ):
        """Test schema collection with permission error."""
        # Setup mocks
        mock_database_manager.get_source_connection = AsyncMock(
            return_value=mock_connector
        )
        mock_database_manager.return_source_connection = Mock()
        mock_connector.verify_schema_access = AsyncMock(return_value=False)

        # Test permission error
        with pytest.raises(SchemaCollectionError, match="Schema collection failed"):
            await schema_collector.collect_schema_info("private", "source")

        # Verify connection was returned
        mock_database_manager.return_source_connection.assert_called_once()

    @pytest.mark.asyncio
    async def test_collect_schema_info_query_error(
        self, schema_collector, mock_database_manager, mock_connector
    ):
        """Test schema collection with query error."""
        # Setup mocks
        mock_database_manager.get_source_connection = AsyncMock(
            return_value=mock_connector
        )
        mock_database_manager.return_source_connection = Mock()
        mock_connector.execute_query = AsyncMock(
            side_effect=DatabaseQueryError("Query failed")
        )

        # Test query error
        with pytest.raises(SchemaCollectionError, match="Schema collection failed"):
            await schema_collector.collect_schema_info("public", "source")

        # Verify connection was returned
        mock_database_manager.return_source_connection.assert_called_once()

    @pytest.mark.asyncio
    async def test_collect_tables(
        self,
        schema_collector,
        mock_database_manager,
        mock_connector,
        sample_table_data,
        sample_column_data,
    ):
        """Test table collection."""
        # Setup mocks
        query_responses = [sample_table_data, sample_column_data, sample_column_data]
        call_count = 0

        async def mock_execute_query(*args, **kwargs):
            nonlocal call_count
            result = query_responses[call_count]
            call_count += 1
            return result

        mock_connector.execute_query = mock_execute_query

        # Test table collection
        tables = await schema_collector._collect_tables(mock_connector, "public")

        # Verify results
        assert len(tables) == 2
        assert tables[0]["table_name"] == "users"
        assert tables[1]["table_name"] == "posts"
        assert "columns" in tables[0]
        assert "columns" in tables[1]

    @pytest.mark.asyncio
    async def test_collect_columns(
        self, schema_collector, mock_connector, sample_column_data
    ):
        """Test column collection."""
        # Setup mock
        mock_connector.execute_query = AsyncMock(return_value=sample_column_data)

        # Test column collection
        columns = await schema_collector._collect_columns(
            mock_connector, "public", "users"
        )

        # Verify results
        assert len(columns) == 2
        assert columns[0]["column_name"] == "id"
        assert columns[1]["column_name"] == "username"
        assert columns[0]["data_type"] == "integer"
        assert columns[1]["data_type"] == "character varying"

    @pytest.mark.asyncio
    async def test_collect_views(self, schema_collector, mock_connector):
        """Test view collection."""
        # Sample view data
        view_data = [
            {
                "view_name": "user_summary",
                "view_definition": "SELECT id, username FROM users",
                "is_updatable": "NO",
                "is_insertable_into": "NO",
                "view_comment": "User summary view",
            }
        ]

        # Setup mocks
        query_responses = [view_data, []]  # View data, then empty columns
        call_count = 0

        async def mock_execute_query(*args, **kwargs):
            nonlocal call_count
            result = query_responses[call_count]
            call_count += 1
            return result

        mock_connector.execute_query = mock_execute_query

        # Test view collection
        views = await schema_collector._collect_views(mock_connector, "public")

        # Verify results
        assert len(views) == 1
        assert views[0]["view_name"] == "user_summary"
        assert views[0]["is_updatable"] == "NO"
        assert "columns" in views[0]

    @pytest.mark.asyncio
    async def test_collect_sequences(self, schema_collector, mock_connector):
        """Test sequence collection."""
        # Sample sequence data
        sequence_data = [
            {
                "sequence_name": "users_id_seq",
                "data_type": "bigint",
                "start_value": "1",
                "minimum_value": "1",
                "maximum_value": "9223372036854775807",
                "increment": "1",
                "cycle_option": "NO",
                "sequence_comment": "Primary key sequence",
            }
        ]

        # Setup mock
        mock_connector.execute_query = AsyncMock(return_value=sequence_data)

        # Test sequence collection
        sequences = await schema_collector._collect_sequences(mock_connector, "public")

        # Verify results
        assert len(sequences) == 1
        assert sequences[0]["sequence_name"] == "users_id_seq"
        assert sequences[0]["increment"] == "1"

    @pytest.mark.asyncio
    async def test_collect_constraints(self, schema_collector, mock_connector):
        """Test constraint collection."""
        # Sample constraint data
        constraint_data = [
            {
                "constraint_name": "users_pkey",
                "table_name": "users",
                "constraint_type": "PRIMARY KEY",
                "column_name": "id",
                "foreign_table_name": None,
                "foreign_column_name": None,
                "check_clause": None,
                "constraint_comment": None,
            }
        ]

        # Setup mock
        mock_connector.execute_query = AsyncMock(return_value=constraint_data)

        # Test constraint collection
        constraints = await schema_collector._collect_constraints(
            mock_connector, "public"
        )

        # Verify results
        assert len(constraints) == 1
        assert constraints[0]["constraint_name"] == "users_pkey"
        assert constraints[0]["constraint_type"] == "PRIMARY KEY"

    def test_cache_functionality(self, schema_collector):
        """Test cache functionality."""
        # Test cache miss
        assert not schema_collector._is_cached("source:public")

        # Add to cache
        schema_collector._schema_cache["source:public"] = {"test": "data"}
        schema_collector._cache_timestamps["source:public"] = datetime.now(timezone.utc)

        # Test cache hit
        assert schema_collector._is_cached("source:public")

        # Test cache expiration
        schema_collector._cache_timestamps["source:public"] = (
            datetime.now(timezone.utc) - timedelta(seconds=400)
        )
        assert not schema_collector._is_cached("source:public")

    def test_clear_cache(self, schema_collector):
        """Test cache clearing."""
        # Add test data to cache
        schema_collector._schema_cache["source:public"] = {"test": "data1"}
        schema_collector._schema_cache["target:public"] = {"test": "data2"}
        schema_collector._cache_timestamps["source:public"] = datetime.now(timezone.utc)
        schema_collector._cache_timestamps["target:public"] = datetime.now(timezone.utc)

        # Clear specific schema
        schema_collector.clear_cache("public")

        # Verify cache is cleared
        assert len(schema_collector._schema_cache) == 0
        assert len(schema_collector._cache_timestamps) == 0

    def test_get_cache_statistics(self, schema_collector):
        """Test cache statistics."""
        # Add test data to cache
        schema_collector._schema_cache["source:public"] = {"test": "data1"}
        schema_collector._schema_cache["target:public"] = {"test": "data2"}
        schema_collector._cache_timestamps["source:public"] = datetime.now(timezone.utc)
        schema_collector._cache_timestamps["target:public"] = datetime.now(timezone.utc)

        # Get statistics
        stats = schema_collector.get_cache_statistics()

        # Verify statistics
        assert stats["cached_schemas"] == 2
        assert len(stats["cache_keys"]) == 2
        assert stats["cache_ttl_seconds"] == 300
        assert stats["oldest_cache_age"] is not None

    @pytest.mark.asyncio
    async def test_get_available_schemas(
        self, schema_collector, mock_database_manager, mock_connector
    ):
        """Test getting available schemas."""
        # Setup mock
        mock_database_manager.get_source_connection = AsyncMock(
            return_value=mock_connector
        )
        mock_database_manager.return_source_connection = Mock()
        mock_connector.execute_query = AsyncMock(
            return_value=[
                {"schema_name": "public"},
                {"schema_name": "private"},
                {"schema_name": "test"},
            ]
        )

        # Test getting available schemas
        schemas = await schema_collector.get_available_schemas("source")

        # Verify results
        assert schemas == ["public", "private", "test"]
        mock_database_manager.return_source_connection.assert_called_once()

    @pytest.mark.asyncio
    async def test_target_database_collection(
        self, schema_collector, mock_database_manager, mock_connector
    ):
        """Test schema collection for target database."""
        # Setup mocks
        mock_database_manager.get_target_connection = AsyncMock(
            return_value=mock_connector
        )
        mock_database_manager.return_target_connection = Mock()
        mock_connector.execute_query = AsyncMock(return_value=[])

        # Test target database collection
        schema_info = await schema_collector.collect_schema_info("public", "target")

        # Verify target database was used
        assert schema_info.database_type == "target"
        mock_database_manager.get_target_connection.assert_called_once()
        mock_database_manager.return_target_connection.assert_called_once()


class TestSchemaCollectorEdgeCases:
    """Edge case tests for SchemaInformationCollector."""

    @pytest.fixture
    def mock_database_manager(self):
        """Create mock database manager."""
        manager = Mock(spec=DatabaseManager)
        manager.config = Mock()
        return manager

    @pytest.mark.asyncio
    async def test_concurrent_schema_collection(self, mock_database_manager):
        """Test concurrent schema collection calls."""
        # Setup mocks
        mock_connector = Mock(spec=DatabaseConnector)
        mock_connector.verify_schema_access = AsyncMock(return_value=True)
        mock_connector.execute_query = AsyncMock(return_value=[])

        mock_database_manager.get_source_connection = AsyncMock(
            return_value=mock_connector
        )
        mock_database_manager.return_source_connection = Mock()

        collector = SchemaInformationCollector(mock_database_manager)

        # Run concurrent collections
        tasks = [collector.collect_schema_info("public", "source") for _ in range(3)]
        results = await asyncio.gather(*tasks)

        # Verify all results are consistent
        for result in results:
            assert result.schema_name == "public"
            assert result.database_type == "source"

    @pytest.mark.asyncio
    async def test_empty_schema_collection(self, mock_database_manager):
        """Test collection of empty schema."""
        # Setup mocks
        mock_connector = Mock(spec=DatabaseConnector)
        mock_connector.verify_schema_access = AsyncMock(return_value=True)
        mock_connector.execute_query = AsyncMock(return_value=[])

        mock_database_manager.get_source_connection = AsyncMock(
            return_value=mock_connector
        )
        mock_database_manager.return_source_connection = Mock()

        collector = SchemaInformationCollector(mock_database_manager)

        # Test empty schema collection
        schema_info = await collector.collect_schema_info("empty", "source")

        # Verify empty results
        assert len(schema_info.tables) == 0
        assert len(schema_info.views) == 0
        assert len(schema_info.sequences) == 0
        assert len(schema_info.functions) == 0
