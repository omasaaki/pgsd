"""Simplified tests for diff analyzer."""

import pytest
from datetime import datetime
from unittest.mock import Mock

from src.pgsd.core.analyzer import DiffAnalyzer, DiffResult, TableDiff
from src.pgsd.models.schema import (
    SchemaInfo,
    TableInfo,
    ColumnInfo,
    ConstraintInfo,
)


class TestDiffResultBasic:
    """Basic test cases for DiffResult class."""

    def test_initialization(self):
        """Test DiffResult initialization."""
        result = DiffResult()
        
        # Check default structure
        assert "added" in result.tables
        assert "removed" in result.tables
        assert "modified" in result.tables
        
        assert "added" in result.columns
        assert "removed" in result.columns
        assert "modified" in result.columns
        
        assert isinstance(result.summary, dict)

    def test_update_summary(self):
        """Test summary update calculation."""
        result = DiffResult()
        
        # Add some test data
        result.tables["added"] = [Mock(), Mock()]
        result.tables["removed"] = [Mock()]
        result.columns["modified"] = [Mock(), Mock(), Mock()]
        
        result.update_summary()
        
        assert result.summary["tables_added"] == 2
        assert result.summary["tables_removed"] == 1
        assert result.summary["columns_modified"] == 3
        assert result.summary["total_changes"] == 6


class TestTableDiffBasic:
    """Basic test cases for TableDiff class."""

    def test_has_changes_empty(self):
        """Test has_changes with empty diff."""
        table_diff = TableDiff(name="test_table")
        assert not table_diff.has_changes()

    def test_has_changes_with_columns(self):
        """Test has_changes with column changes."""
        table_diff = TableDiff(name="test_table")
        table_diff.columns = {"added": [Mock()]}
        assert table_diff.has_changes()


class TestDiffAnalyzerBasic:
    """Basic test cases for DiffAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return DiffAnalyzer()

    def test_analyzer_initialization(self, analyzer):
        """Test analyzer initialization."""
        assert isinstance(analyzer, DiffAnalyzer)
        assert isinstance(analyzer.result, DiffResult)

    def test_empty_schemas_comparison(self, analyzer):
        """Test comparison of empty schemas."""
        schema_a = SchemaInfo(
            schema_name="public",
            database_type="source",
            collection_time=datetime(2025, 7, 14, 10, 0, 0),
            tables=[],
            views=[],
            functions=[],
            sequences=[]
        )
        
        schema_b = SchemaInfo(
            schema_name="public",
            database_type="target",
            collection_time=datetime(2025, 7, 14, 10, 0, 0),
            tables=[],
            views=[],
            functions=[],
            sequences=[]
        )
        
        result = analyzer.analyze(schema_a, schema_b)
        
        assert len(result.tables["added"]) == 0
        assert len(result.tables["removed"]) == 0
        assert len(result.tables["modified"]) == 0
        assert result.summary["total_changes"] == 0

    def test_identical_schemas_comparison(self, analyzer):
        """Test comparison of identical schemas."""
        column = ColumnInfo(
            column_name="id",
            ordinal_position=1,
            data_type="integer",
            is_nullable=False
        )
        
        table = TableInfo(
            table_name="users",
            table_schema="public",
            table_type="BASE TABLE",
            columns=[column]
        )
        
        schema = SchemaInfo(
            schema_name="public",
            database_type="source",
            collection_time=datetime(2025, 7, 14, 10, 0, 0),
            tables=[table],
            views=[],
            functions=[],
            sequences=[]
        )
        
        result = analyzer.analyze(schema, schema)
        
        assert len(result.tables["added"]) == 0
        assert len(result.tables["removed"]) == 0
        assert len(result.tables["modified"]) == 0
        assert result.summary["total_changes"] == 0

    def test_table_added(self, analyzer):
        """Test detection of added table."""
        # Schema A: empty
        schema_a = SchemaInfo(
            schema_name="public",
            database_type="source",
            collection_time=datetime(2025, 7, 14, 10, 0, 0),
            tables=[],
            views=[],
            functions=[],
            sequences=[]
        )
        
        # Schema B: has one table
        column = ColumnInfo(
            column_name="id",
            ordinal_position=1,
            data_type="integer",
            is_nullable=False
        )
        
        table = TableInfo(
            table_name="users",
            table_schema="public",
            table_type="BASE TABLE",
            columns=[column]
        )
        
        schema_b = SchemaInfo(
            schema_name="public",
            database_type="target",
            collection_time=datetime(2025, 7, 14, 10, 0, 0),
            tables=[table],
            views=[],
            functions=[],
            sequences=[]
        )
        
        result = analyzer.analyze(schema_a, schema_b)
        
        assert len(result.tables["added"]) == 1
        assert len(result.tables["removed"]) == 0
        assert len(result.tables["modified"]) == 0
        
        # Check that the added table is correct
        added_table = result.tables["added"][0]
        assert added_table.table_name == "users"
        
        # Check that column was also added
        assert len(result.columns["added"]) == 1
        added_column = result.columns["added"][0]
        assert added_column["table"] == "users"
        assert added_column["column"].column_name == "id"

    def test_table_removed(self, analyzer):
        """Test detection of removed table."""
        # Schema A: has one table
        column = ColumnInfo(
            column_name="id",
            ordinal_position=1,
            data_type="integer",
            is_nullable=False
        )
        
        table = TableInfo(
            table_name="old_table",
            table_schema="public",
            table_type="BASE TABLE",
            columns=[column]
        )
        
        schema_a = SchemaInfo(
            schema_name="public",
            database_type="source",
            collection_time=datetime(2025, 7, 14, 10, 0, 0),
            tables=[table],
            views=[],
            functions=[],
            sequences=[]
        )
        
        # Schema B: empty
        schema_b = SchemaInfo(
            schema_name="public",
            database_type="target",
            collection_time=datetime(2025, 7, 14, 10, 0, 0),
            tables=[],
            views=[],
            functions=[],
            sequences=[]
        )
        
        result = analyzer.analyze(schema_a, schema_b)
        
        assert len(result.tables["added"]) == 0
        assert len(result.tables["removed"]) == 1
        assert len(result.tables["modified"]) == 0
        
        # Check that the removed table is correct
        removed_table = result.tables["removed"][0]
        assert removed_table.table_name == "old_table"
        
        # Check that column was also removed
        assert len(result.columns["removed"]) == 1
        removed_column = result.columns["removed"][0]
        assert removed_column["table"] == "old_table"
        assert removed_column["column"].column_name == "id"

    def test_column_modified(self, analyzer):
        """Test detection of modified column."""
        # Schema A: table with integer column
        column_a = ColumnInfo(
            column_name="amount",
            ordinal_position=1,
            data_type="integer",
            is_nullable=False,
            numeric_precision=32
        )
        
        table_a = TableInfo(
            table_name="orders",
            table_schema="public",
            table_type="BASE TABLE",
            columns=[column_a]
        )
        
        schema_a = SchemaInfo(
            schema_name="public",
            database_type="source",
            collection_time=datetime(2025, 7, 14, 10, 0, 0),
            tables=[table_a],
            views=[],
            functions=[],
            sequences=[]
        )
        
        # Schema B: same table but column is now bigint
        column_b = ColumnInfo(
            column_name="amount",
            ordinal_position=1,
            data_type="bigint",  # Changed
            is_nullable=False,
            numeric_precision=64  # Changed
        )
        
        table_b = TableInfo(
            table_name="orders",
            table_schema="public",
            table_type="BASE TABLE",
            columns=[column_b]
        )
        
        schema_b = SchemaInfo(
            schema_name="public",
            database_type="target",
            collection_time=datetime(2025, 7, 14, 10, 0, 0),
            tables=[table_b],
            views=[],
            functions=[],
            sequences=[]
        )
        
        result = analyzer.analyze(schema_a, schema_b)
        
        assert len(result.tables["added"]) == 0
        assert len(result.tables["removed"]) == 0
        assert len(result.tables["modified"]) == 1
        
        # Check table modification
        modified_table = result.tables["modified"][0]
        assert modified_table.name == "orders"
        assert modified_table.has_changes()
        
        # Check column modification
        assert len(result.columns["modified"]) == 1
        modified_column = result.columns["modified"][0]
        assert modified_column["table"] == "orders"
        assert modified_column["column"].column_name == "amount"
        
        # Check specific changes
        changes = modified_column["changes"]
        assert "data_type" in changes
        assert changes["data_type"]["from"] == "integer"
        assert changes["data_type"]["to"] == "bigint"
        assert "numeric_precision" in changes
        assert changes["numeric_precision"]["from"] == 32
        assert changes["numeric_precision"]["to"] == 64

    def test_column_added_to_existing_table(self, analyzer):
        """Test detection of column added to existing table."""
        # Schema A: table with one column
        column_a = ColumnInfo(
            column_name="id",
            ordinal_position=1,
            data_type="integer",
            is_nullable=False
        )
        
        table_a = TableInfo(
            table_name="users",
            table_schema="public",
            table_type="BASE TABLE",
            columns=[column_a]
        )
        
        schema_a = SchemaInfo(
            schema_name="public",
            database_type="source",
            collection_time=datetime(2025, 7, 14, 10, 0, 0),
            tables=[table_a],
            views=[],
            functions=[],
            sequences=[]
        )
        
        # Schema B: same table with additional column
        column_b1 = ColumnInfo(
            column_name="id",
            ordinal_position=1,
            data_type="integer",
            is_nullable=False
        )
        
        column_b2 = ColumnInfo(
            column_name="email",  # New column
            ordinal_position=2,
            data_type="varchar",
            is_nullable=True,
            character_maximum_length=255
        )
        
        table_b = TableInfo(
            table_name="users",
            table_schema="public",
            table_type="BASE TABLE",
            columns=[column_b1, column_b2]
        )
        
        schema_b = SchemaInfo(
            schema_name="public",
            database_type="target",
            collection_time=datetime(2025, 7, 14, 10, 0, 0),
            tables=[table_b],
            views=[],
            functions=[],
            sequences=[]
        )
        
        result = analyzer.analyze(schema_a, schema_b)
        
        assert len(result.tables["added"]) == 0
        assert len(result.tables["removed"]) == 0
        assert len(result.tables["modified"]) == 1
        
        # Check table modification
        modified_table = result.tables["modified"][0]
        assert modified_table.name == "users"
        assert modified_table.has_changes()
        
        # Check column addition
        assert len(result.columns["added"]) == 1
        added_column = result.columns["added"][0]
        assert added_column["table"] == "users"
        assert added_column["column"].column_name == "email"

    def test_constraint_added(self, analyzer):
        """Test detection of added constraint."""
        # Schema A: table without constraints
        column = ColumnInfo(
            column_name="id",
            ordinal_position=1,
            data_type="integer",
            is_nullable=False
        )
        
        table_a = TableInfo(
            table_name="users",
            table_schema="public",
            table_type="BASE TABLE",
            columns=[column],
            constraints=[]
        )
        
        schema_a = SchemaInfo(
            schema_name="public",
            database_type="source",
            collection_time=datetime(2025, 7, 14, 10, 0, 0),
            tables=[table_a],
            views=[],
            functions=[],
            sequences=[]
        )
        
        # Schema B: same table with primary key constraint
        constraint = ConstraintInfo(
            constraint_name="users_pkey",
            table_name="users",
            constraint_type="PRIMARY KEY",
            column_name="id"
        )
        
        table_b = TableInfo(
            table_name="users",
            table_schema="public",
            table_type="BASE TABLE",
            columns=[column],
            constraints=[constraint]
        )
        
        schema_b = SchemaInfo(
            schema_name="public",
            database_type="target",
            collection_time=datetime(2025, 7, 14, 10, 0, 0),
            tables=[table_b],
            views=[],
            functions=[],
            sequences=[]
        )
        
        result = analyzer.analyze(schema_a, schema_b)
        
        assert len(result.tables["modified"]) == 1
        
        # Check constraint addition
        assert len(result.constraints["added"]) == 1
        added_constraint = result.constraints["added"][0]
        assert added_constraint["table"] == "users"
        assert added_constraint["constraint"].constraint_name == "users_pkey"
        assert added_constraint["constraint"].constraint_type == "PRIMARY KEY"

    def test_performance_basic(self, analyzer):
        """Test basic performance with small schemas."""
        import time
        
        # Create small schemas
        columns = [
            ColumnInfo(column_name=f"col_{i}", ordinal_position=i+1, data_type="integer")
            for i in range(5)
        ]
        
        table = TableInfo(
            table_name="test_table",
            table_schema="public",
            table_type="BASE TABLE",
            columns=columns
        )
        
        schema_a = SchemaInfo(
            schema_name="public",
            database_type="source",
            collection_time=datetime(2025, 7, 14, 10, 0, 0),
            tables=[table],
            views=[],
            functions=[],
            sequences=[]
        )
        
        schema_b = SchemaInfo(
            schema_name="public",
            database_type="target",
            collection_time=datetime(2025, 7, 14, 10, 0, 0),
            tables=[table],  # Identical
            views=[],
            functions=[],
            sequences=[]
        )
        
        start_time = time.time()
        result = analyzer.analyze(schema_a, schema_b)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Should complete very quickly for small schemas
        assert execution_time < 0.1
        assert result.summary["total_changes"] == 0