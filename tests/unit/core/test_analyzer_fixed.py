"""Tests for diff analyzer - fixed version."""

import pytest
from unittest.mock import Mock
from datetime import datetime

from src.pgsd.core.analyzer import DiffAnalyzer, DiffResult, TableDiff
from src.pgsd.models.schema import (
    SchemaInfo,
    TableInfo,
    ColumnInfo,
    ConstraintInfo,
    ViewInfo,
    FunctionInfo,
    SequenceInfo,
)


class TestDiffAnalyzerCore:
    """Core tests for DiffAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return DiffAnalyzer()

    @pytest.fixture
    def sample_column(self):
        """Create a sample column."""
        return ColumnInfo(
            column_name="id",
            ordinal_position=1,
            data_type="integer",
            is_nullable=False,
            column_default="nextval('users_id_seq'::regclass)",
            numeric_precision=32,
            numeric_scale=0,
            udt_name="int4",
            column_comment="Primary key"
        )

    @pytest.fixture
    def sample_table(self, sample_column):
        """Create a sample table."""
        return TableInfo(
            table_name="users",
            table_type="BASE TABLE",
            table_schema="public",
            table_comment="User table",
            estimated_rows=1000,
            table_size="64 kB",
            columns=[sample_column],
            constraints=[]
        )

    @pytest.fixture
    def sample_schema(self, sample_table):
        """Create a sample schema."""
        return SchemaInfo(
            schema_name="public",
            database_type="source",
            collection_time=datetime.now(),
            tables=[sample_table],
            views=[],
            sequences=[],
            functions=[],
            constraints=[]
        )

    def test_initialization(self, analyzer):
        """Test analyzer initialization."""
        assert analyzer.logger is not None

    def test_analyze_identical_schemas(self, analyzer, sample_schema):
        """Test analyzing identical schemas."""
        result = analyzer.analyze(sample_schema, sample_schema)
        
        assert isinstance(result, DiffResult)
        assert len(result.tables["added"]) == 0
        assert len(result.tables["removed"]) == 0
        assert len(result.tables["modified"]) == 0
        assert result.summary["total_changes"] == 0

    def test_analyze_table_added(self, analyzer, sample_schema, sample_table):
        """Test detection of added table."""
        # Create schema with additional table
        new_table = TableInfo(
            table_name="posts",
            table_type="BASE TABLE",
            table_schema="public",
            table_comment="Posts table",
            estimated_rows=500,
            table_size="32 kB",
            columns=[],
            constraints=[]
        )
        
        schema_b = SchemaInfo(
            schema_name="public",
            database_type="target",
            collection_time=datetime.now(),
            tables=[sample_table, new_table],
            views=[],
            sequences=[],
            functions=[],
            constraints=[]
        )
        
        result = analyzer.analyze(sample_schema, schema_b)
        
        assert len(result.tables["added"]) == 1
        assert result.tables["added"][0].table_name == "posts"
        assert result.summary["tables_added"] == 1

    def test_analyze_table_removed(self, analyzer, sample_schema, sample_table):
        """Test detection of removed table."""
        # Create schema with missing table
        schema_b = SchemaInfo(
            schema_name="public",
            database_type="target",
            collection_time=datetime.now(),
            tables=[],  # No tables
            views=[],
            sequences=[],
            functions=[],
            constraints=[]
        )
        
        result = analyzer.analyze(sample_schema, schema_b)
        
        assert len(result.tables["removed"]) == 1
        assert result.tables["removed"][0].table_name == "users"
        assert result.summary["tables_removed"] == 1

    def test_compare_column_details_identical(self, analyzer, sample_column):
        """Test comparing identical columns."""
        changes = analyzer._compare_column_details(sample_column, sample_column)
        assert changes is None

    def test_compare_column_details_changed(self, analyzer):
        """Test comparing columns with changes."""
        col_a = ColumnInfo(
            column_name="id",
            ordinal_position=1,
            data_type="integer",
            is_nullable=False,
            numeric_precision=32
        )
        
        col_b = ColumnInfo(
            column_name="id",
            ordinal_position=1,
            data_type="bigint",  # Changed
            is_nullable=False,
            numeric_precision=64  # Changed
        )
        
        changes = analyzer._compare_column_details(col_a, col_b)
        
        assert changes is not None
        assert "data_type" in changes
        assert changes["data_type"]["from"] == "integer"
        assert changes["data_type"]["to"] == "bigint"
        assert "numeric_precision" in changes
        assert changes["numeric_precision"]["from"] == 32
        assert changes["numeric_precision"]["to"] == 64

    def test_compare_column_details_nullable_change(self, analyzer):
        """Test comparing columns with nullable change."""
        col_a = ColumnInfo(
            column_name="email",
            ordinal_position=2,
            data_type="varchar",
            is_nullable=False
        )
        
        col_b = ColumnInfo(
            column_name="email",
            ordinal_position=2,
            data_type="varchar",
            is_nullable=True  # Changed
        )
        
        changes = analyzer._compare_column_details(col_a, col_b)
        
        assert changes is not None
        assert "is_nullable" in changes
        assert changes["is_nullable"]["from"] is False
        assert changes["is_nullable"]["to"] is True

    def test_compare_table_details_columns_added(self, analyzer, sample_table):
        """Test comparing tables with added columns."""
        # Create table with additional column
        new_column = ColumnInfo(
            column_name="email",
            ordinal_position=2,
            data_type="varchar",
            character_maximum_length=255
        )
        
        table_b = TableInfo(
            table_name="users",
            table_type="BASE TABLE",
            table_schema="public",
            columns=sample_table.columns + [new_column],
            constraints=[]
        )
        
        diff = analyzer._compare_table_details(sample_table, table_b)
        
        assert isinstance(diff, TableDiff)
        assert diff.name == "users"
        assert len(diff.columns["added"]) == 1
        assert diff.columns["added"][0].column_name == "email"

    def test_compare_table_details_columns_removed(self, analyzer, sample_table):
        """Test comparing tables with removed columns."""
        # Create table with no columns
        table_b = TableInfo(
            table_name="users",
            table_type="BASE TABLE",
            table_schema="public",
            columns=[],
            constraints=[]
        )
        
        diff = analyzer._compare_table_details(sample_table, table_b)
        
        assert isinstance(diff, TableDiff)
        assert len(diff.columns["removed"]) == 1
        assert diff.columns["removed"][0].column_name == "id"

    def test_compare_table_details_metadata_changes(self, analyzer, sample_table):
        """Test comparing tables with metadata changes."""
        table_b = TableInfo(
            table_name="users",
            table_type="BASE TABLE",
            table_schema="public",
            table_comment="Updated user table",  # Changed
            estimated_rows=2000,  # Changed
            table_size="128 kB",  # Changed
            columns=sample_table.columns,
            constraints=[]
        )
        
        diff = analyzer._compare_table_details(sample_table, table_b)
        
        assert diff.metadata_changes is not None
        assert "table_comment" in diff.metadata_changes
        assert "estimated_rows" in diff.metadata_changes
        assert "table_size" in diff.metadata_changes

    def test_compare_constraints_added(self, analyzer):
        """Test comparing constraints with additions."""
        constraint = ConstraintInfo(
            constraint_name="users_pkey",
            table_name="users",
            constraint_type="PRIMARY KEY",
            column_name="id"
        )
        
        table_a = TableInfo(
            table_name="users",
            table_type="BASE TABLE",
            table_schema="public",
            columns=[],
            constraints=[]
        )
        
        table_b = TableInfo(
            table_name="users",
            table_type="BASE TABLE",
            table_schema="public",
            columns=[],
            constraints=[constraint]
        )
        
        diff = analyzer._compare_table_details(table_a, table_b)
        
        assert len(diff.constraints["added"]) == 1
        assert diff.constraints["added"][0].constraint_name == "users_pkey"

    def test_analyze_views_added(self, analyzer):
        """Test detection of added views."""
        view = ViewInfo(
            view_name="user_summary",
            view_definition="SELECT * FROM users",
            is_updatable=True,
            is_insertable_into=False,
            columns=[]
        )
        
        schema_a = SchemaInfo(
            schema_name="public",
            database_type="source",
            collection_time=datetime.now(),
            tables=[],
            views=[],
            sequences=[],
            functions=[],
            constraints=[]
        )
        
        schema_b = SchemaInfo(
            schema_name="public",
            database_type="target",
            collection_time=datetime.now(),
            tables=[],
            views=[view],
            sequences=[],
            functions=[],
            constraints=[]
        )
        
        result = analyzer.analyze(schema_a, schema_b)
        
        assert len(result.views["added"]) == 1
        assert result.views["added"][0].view_name == "user_summary"

    def test_analyze_sequences_modified(self, analyzer):
        """Test detection of modified sequences."""
        seq_a = SequenceInfo(
            sequence_name="users_id_seq",
            data_type="bigint",
            start_value="1",
            minimum_value="1",
            maximum_value="9223372036854775807",
            increment="1",
            cycle_option=False
        )
        
        seq_b = SequenceInfo(
            sequence_name="users_id_seq",
            data_type="bigint",
            start_value="100",  # Changed
            minimum_value="1",
            maximum_value="9223372036854775807",
            increment="10",  # Changed
            cycle_option=False
        )
        
        schema_a = SchemaInfo(
            schema_name="public",
            database_type="source",
            collection_time=datetime.now(),
            tables=[],
            views=[],
            sequences=[seq_a],
            functions=[],
            constraints=[]
        )
        
        schema_b = SchemaInfo(
            schema_name="public",
            database_type="target",
            collection_time=datetime.now(),
            tables=[],
            views=[],
            sequences=[seq_b],
            functions=[],
            constraints=[]
        )
        
        result = analyzer.analyze(schema_a, schema_b)
        
        assert len(result.sequences["modified"]) == 1
        changes = result.sequences["modified"][0]["changes"]
        assert "start_value" in changes
        assert "increment" in changes

    def test_analyze_functions_removed(self, analyzer):
        """Test detection of removed functions."""
        func = FunctionInfo(
            function_name="get_user_count",
            function_type="FUNCTION",
            return_type="integer",
            function_definition="SELECT COUNT(*) FROM users"
        )
        
        schema_a = SchemaInfo(
            schema_name="public",
            database_type="source",
            collection_time=datetime.now(),
            tables=[],
            views=[],
            sequences=[],
            functions=[func],
            constraints=[]
        )
        
        schema_b = SchemaInfo(
            schema_name="public",
            database_type="target",
            collection_time=datetime.now(),
            tables=[],
            views=[],
            sequences=[],
            functions=[],
            constraints=[]
        )
        
        result = analyzer.analyze(schema_a, schema_b)
        
        assert len(result.functions["removed"]) == 1
        assert result.functions["removed"][0].function_name == "get_user_count"

    def test_empty_schemas_comparison(self, analyzer):
        """Test comparing empty schemas."""
        schema_a = SchemaInfo(
            schema_name="public",
            database_type="source",
            collection_time=datetime.now(),
            tables=[],
            views=[],
            sequences=[],
            functions=[],
            constraints=[]
        )
        
        schema_b = SchemaInfo(
            schema_name="public",
            database_type="target",
            collection_time=datetime.now(),
            tables=[],
            views=[],
            sequences=[],
            functions=[],
            constraints=[]
        )
        
        result = analyzer.analyze(schema_a, schema_b)
        
        assert result.summary["total_changes"] == 0

    def test_complex_table_modifications(self, analyzer):
        """Test complex table modifications with multiple changes."""
        # Source table
        col_a1 = ColumnInfo(column_name="id", ordinal_position=1, data_type="integer")
        col_a2 = ColumnInfo(column_name="name", ordinal_position=2, data_type="varchar")
        col_a3 = ColumnInfo(column_name="deleted_at", ordinal_position=3, data_type="timestamp")
        
        table_a = TableInfo(
            table_name="users",
            table_type="BASE TABLE",
            table_schema="public",
            columns=[col_a1, col_a2, col_a3],
            constraints=[]
        )
        
        # Target table
        col_b1 = ColumnInfo(column_name="id", ordinal_position=1, data_type="bigint")  # Type changed
        col_b2 = ColumnInfo(column_name="name", ordinal_position=2, data_type="varchar")
        col_b3 = ColumnInfo(column_name="email", ordinal_position=3, data_type="varchar")  # New column
        col_b4 = ColumnInfo(column_name="created_at", ordinal_position=4, data_type="timestamp")  # New column
        # deleted_at is removed
        
        table_b = TableInfo(
            table_name="users",
            table_type="BASE TABLE",
            table_schema="public",
            columns=[col_b1, col_b2, col_b3, col_b4],
            constraints=[]
        )
        
        diff = analyzer._compare_table_details(table_a, table_b)
        
        assert len(diff.columns["added"]) == 2  # email, created_at
        assert len(diff.columns["removed"]) == 1  # deleted_at
        assert len(diff.columns["modified"]) == 1  # id (type changed)
        assert diff.has_changes()

    def test_case_sensitive_comparison(self, analyzer):
        """Test case-sensitive table name comparison."""
        table_a = TableInfo(
            table_name="Users",  # Uppercase
            table_type="BASE TABLE",
            table_schema="public",
            columns=[],
            constraints=[]
        )
        
        table_b = TableInfo(
            table_name="users",  # Lowercase
            table_type="BASE TABLE",
            table_schema="public",
            columns=[],
            constraints=[]
        )
        
        schema_a = SchemaInfo(
            schema_name="public",
            database_type="source",
            collection_time=datetime.now(),
            tables=[table_a],
            views=[],
            sequences=[],
            functions=[],
            constraints=[]
        )
        
        schema_b = SchemaInfo(
            schema_name="public",
            database_type="target",
            collection_time=datetime.now(),
            tables=[table_b],
            views=[],
            sequences=[],
            functions=[],
            constraints=[]
        )
        
        result = analyzer.analyze(schema_a, schema_b)
        
        # Different case should be treated as different tables
        assert len(result.tables["added"]) == 1
        assert len(result.tables["removed"]) == 1

    def test_performance_with_many_tables(self, analyzer):
        """Test performance with many tables."""
        # Create schemas with 100 tables each
        tables = []
        for i in range(100):
            table = TableInfo(
                table_name=f"table_{i}",
                table_type="BASE TABLE",
                table_schema="public",
                columns=[
                    ColumnInfo(
                        column_name=f"col_{j}",
                        ordinal_position=j+1,
                        data_type="integer"
                    ) for j in range(5)
                ],
                constraints=[]
            )
            tables.append(table)
        
        schema_a = SchemaInfo(
            schema_name="public",
            database_type="source",
            collection_time=datetime.now(),
            tables=tables,
            views=[],
            sequences=[],
            functions=[],
            constraints=[]
        )
        
        # Schema B has same tables (no changes expected)
        schema_b = SchemaInfo(
            schema_name="public",
            database_type="target",
            collection_time=datetime.now(),
            tables=tables,
            views=[],
            sequences=[],
            functions=[],
            constraints=[]
        )
        
        result = analyzer.analyze(schema_a, schema_b)
        
        assert result.summary["total_changes"] == 0
        assert len(result.tables["modified"]) == 0