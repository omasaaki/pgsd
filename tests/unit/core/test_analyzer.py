"""Tests for diff analyzer."""

import pytest
from unittest.mock import Mock

from src.pgsd.core.analyzer import DiffAnalyzer, DiffResult, TableDiff
from src.pgsd.models.schema import (
    SchemaInfo,
    TableInfo,
    ColumnInfo,
    ConstraintInfo,
    IndexInfo,
    ViewInfo,
    FunctionInfo,
    SequenceInfo,
    TriggerInfo,
)


class TestDiffResult:
    """Test cases for DiffResult class."""

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


class TestTableDiff:
    """Test cases for TableDiff class."""

    def test_has_changes_empty(self):
        """Test has_changes with empty diff."""
        table_diff = TableDiff(name="test_table")
        assert not table_diff.has_changes()

    def test_has_changes_with_columns(self):
        """Test has_changes with column changes."""
        table_diff = TableDiff(name="test_table")
        table_diff.columns = {"added": [Mock()]}
        assert table_diff.has_changes()

    def test_has_changes_with_constraints(self):
        """Test has_changes with constraint changes."""
        table_diff = TableDiff(name="test_table")
        table_diff.constraints = {"removed": [Mock()]}
        assert table_diff.has_changes()


class TestDiffAnalyzer:
    """Test cases for DiffAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return DiffAnalyzer()

    @pytest.fixture
    def sample_column_a(self):
        """Create sample column A."""
        return ColumnInfo(
            column_name="id",
            data_type="integer",
            is_nullable=False,
            column_default="nextval('seq'::regclass)",
            character_maximum_length=None,
            numeric_precision=32,
            numeric_scale=0,
            ordinal_position=1,
            udt_name="int4",
            column_comment="Primary key"
        )

    @pytest.fixture
    def sample_column_b(self):
        """Create sample column B with modifications."""
        return ColumnInfo(
            column_name="id",
            data_type="bigint",  # Changed from integer
            is_nullable=False,
            column_default="nextval('seq'::regclass)",
            character_maximum_length=None,
            numeric_precision=64,  # Changed from 32
            numeric_scale=0,
            ordinal_position=1,
            udt_name="int8",  # Changed from int4
            column_comment="Primary key"
        )

    @pytest.fixture
    def sample_table_a(self, sample_column_a):
        """Create sample table A."""
        return TableInfo(
            table_name="users",
            table_schema="public",
            table_type="BASE TABLE",
            columns=[sample_column_a],
            constraints=[],
            indexes=[],
            triggers=[],
            table_comment="User table",
            estimated_rows=1000,
            table_size="64 kB"
        )

    @pytest.fixture
    def sample_table_b(self, sample_column_b):
        """Create sample table B with modifications."""
        # Add a new column
        new_column = ColumnInfo(
            column_name="email",
            data_type="character varying",
            is_nullable=True,
            column_default=None,
            character_maximum_length=255,
            numeric_precision=None,
            numeric_scale=None,
            ordinal_position=2,
            udt_name="varchar",
            column_comment="Email address"
        )
        
        return TableInfo(
            table_name="users",
            table_schema="public",
            table_type="BASE TABLE",
            columns=[sample_column_b, new_column],
            constraints=[],
            indexes=[],
            triggers=[],
            table_comment="User table",
            estimated_rows=1500,  # Changed
            table_size="96 kB"    # Changed
        )

    @pytest.fixture
    def schema_a(self, sample_table_a):
        """Create sample schema A."""
        from datetime import datetime
        return SchemaInfo(
            schema_name="public",
            database_type="source",
            collection_time=datetime(2025, 7, 14, 10, 0, 0),
            tables=[sample_table_a],
            views=[],
            functions=[],
            sequences=[]
        )

    @pytest.fixture
    def schema_b(self, sample_table_b):
        """Create sample schema B."""
        from datetime import datetime
        # Add a new table
        new_table = TableInfo(
            table_name="posts",
            table_schema="public",
            table_type="BASE TABLE",
            columns=[
                ColumnInfo(
                    column_name="id",
                    data_type="integer",
                    is_nullable=False,
                    column_default="nextval('posts_id_seq'::regclass)",
                    character_maximum_length=None,
                    numeric_precision=32,
                    numeric_scale=0,
                    ordinal_position=1,
                    udt_name="int4",
                    column_comment="Post ID"
                )
            ],
            constraints=[],
            indexes=[],
            triggers=[],
            table_comment="Posts table",
            estimated_rows=500,
            table_size="32 kB"
        )
        
        return SchemaInfo(
            schema_name="public",
            database_type="target",
            collection_time=datetime(2025, 7, 14, 10, 5, 0),
            tables=[sample_table_b, new_table],
            views=[],
            functions=[],
            sequences=[]
        )

    def test_analyze_basic(self, analyzer, schema_a, schema_b):
        """Test basic schema analysis."""
        result = analyzer.analyze(schema_a, schema_b)
        
        assert isinstance(result, DiffResult)
        assert len(result.tables["added"]) == 1  # posts table added
        assert len(result.tables["removed"]) == 0
        assert len(result.tables["modified"]) == 1  # users table modified
        
        # Check summary is updated
        assert result.summary["tables_added"] == 1
        assert result.summary["tables_modified"] == 1
        assert result.summary["total_changes"] > 0

    def test_compare_column_details(self, analyzer, sample_column_a, sample_column_b):
        """Test column detail comparison."""
        changes = analyzer._compare_column_details(sample_column_a, sample_column_b)
        
        assert changes is not None
        assert "data_type" in changes
        assert changes["data_type"]["from"] == "integer"
        assert changes["data_type"]["to"] == "bigint"
        
        assert "numeric_precision" in changes
        assert changes["numeric_precision"]["from"] == 32
        assert changes["numeric_precision"]["to"] == 64

    def test_compare_column_details_no_changes(self, analyzer, sample_column_a):
        """Test column comparison with no changes."""
        changes = analyzer._compare_column_details(sample_column_a, sample_column_a)
        assert changes is None

    def test_compare_tables_added(self, analyzer):
        """Test detection of added tables."""
        from datetime import datetime
        # Create schemas
        table_a = TableInfo(
            table_name="users", table_schema="public", table_type="BASE TABLE",
            columns=[], constraints=[], indexes=[], triggers=[],
            table_comment=None, estimated_rows=0, table_size="0"
        )
        
        table_b1 = TableInfo(
            table_name="users", table_schema="public", table_type="BASE TABLE",
            columns=[], constraints=[], indexes=[], triggers=[],
            table_comment=None, estimated_rows=0, table_size="0"
        )
        
        table_b2 = TableInfo(
            table_name="posts", table_schema="public", table_type="BASE TABLE",
            columns=[], constraints=[], indexes=[], triggers=[],
            table_comment=None, estimated_rows=0, table_size="0"
        )
        
        schema_a = SchemaInfo(
            schema_name="public", database_type="source",
            collection_time=datetime(2025, 7, 14, 10, 0, 0),
            tables=[table_a], views=[], functions=[], sequences=[]
        )
        
        schema_b = SchemaInfo(
            schema_name="public", database_type="target",
            collection_time=datetime(2025, 7, 14, 10, 0, 0),
            tables=[table_b1, table_b2], views=[], functions=[], sequences=[]
        )
        
        result = analyzer.analyze(schema_a, schema_b)
        
        assert len(result.tables["added"]) == 1
        assert result.tables["added"][0].table_name == "posts"

    def test_compare_tables_removed(self, analyzer):
        """Test detection of removed tables."""
        table_a1 = TableInfo(
            name="users", schema="public", table_type="BASE TABLE",
            columns=[], constraints=[], indexes=[], triggers=[],
            table_comment=None, estimated_rows=0, table_size="0"
        )
        
        table_a2 = TableInfo(
            name="old_table", schema="public", table_type="BASE TABLE",
            columns=[], constraints=[], indexes=[], triggers=[],
            table_comment=None, estimated_rows=0, table_size="0"
        )
        
        table_b = TableInfo(
            name="users", schema="public", table_type="BASE TABLE",
            columns=[], constraints=[], indexes=[], triggers=[],
            table_comment=None, estimated_rows=0, table_size="0"
        )
        
        schema_a = SchemaInfo(
            schema_name="public", database_name="db_a", database_type="source",
            postgresql_version="14.5", collection_time="2025-07-14T10:00:00",
            tables=[table_a1, table_a2], views=[], functions=[], sequences=[],
            statistics={}
        )
        
        schema_b = SchemaInfo(
            schema_name="public", database_name="db_b", database_type="target",
            postgresql_version="14.5", collection_time="2025-07-14T10:00:00",
            tables=[table_b], views=[], functions=[], sequences=[],
            statistics={}
        )
        
        result = analyzer.analyze(schema_a, schema_b)
        
        assert len(result.tables["removed"]) == 1
        assert result.tables["removed"][0].name == "old_table"

    def test_compare_empty_schemas(self, analyzer):
        """Test comparison of empty schemas."""
        schema_a = SchemaInfo(
            schema_name="public", database_name="db_a", database_type="source",
            postgresql_version="14.5", collection_time="2025-07-14T10:00:00",
            tables=[], views=[], functions=[], sequences=[],
            statistics={}
        )
        
        schema_b = SchemaInfo(
            schema_name="public", database_name="db_b", database_type="target",
            postgresql_version="14.5", collection_time="2025-07-14T10:00:00",
            tables=[], views=[], functions=[], sequences=[],
            statistics={}
        )
        
        result = analyzer.analyze(schema_a, schema_b)
        
        assert len(result.tables["added"]) == 0
        assert len(result.tables["removed"]) == 0
        assert len(result.tables["modified"]) == 0
        assert result.summary["total_changes"] == 0

    def test_compare_identical_schemas(self, analyzer, schema_a):
        """Test comparison of identical schemas."""
        result = analyzer.analyze(schema_a, schema_a)
        
        assert len(result.tables["added"]) == 0
        assert len(result.tables["removed"]) == 0
        assert len(result.tables["modified"]) == 0
        assert result.summary["total_changes"] == 0

    def test_compare_constraints(self, analyzer):
        """Test constraint comparison."""
        # Create constraint objects
        constraint_a = ConstraintInfo(
            name="users_pkey",
            constraint_type="PRIMARY KEY",
            table_name="users",
            columns=["id"],
            is_deferrable=False,
            initially_deferred=False
        )
        
        constraint_b = ConstraintInfo(
            name="users_email_unique",
            constraint_type="UNIQUE",
            table_name="users",
            columns=["email"],
            is_deferrable=False,
            initially_deferred=False
        )
        
        table_a = TableInfo(
            name="users", schema="public", table_type="BASE TABLE",
            columns=[], constraints=[constraint_a], indexes=[], triggers=[],
            table_comment=None, estimated_rows=0, table_size="0"
        )
        
        table_b = TableInfo(
            name="users", schema="public", table_type="BASE TABLE",
            columns=[], constraints=[constraint_a, constraint_b], indexes=[], triggers=[],
            table_comment=None, estimated_rows=0, table_size="0"
        )
        
        table_diff = analyzer._compare_table_details(table_a, table_b)
        
        assert "added" in table_diff.constraints
        assert len(table_diff.constraints["added"]) == 1
        assert table_diff.constraints["added"][0].name == "users_email_unique"

    def test_compare_views(self, analyzer):
        """Test view comparison."""
        view_a = ViewInfo(
            name="user_summary",
            schema="public",
            definition="SELECT id, name FROM users",
            is_materialized=False,
            columns=[]
        )
        
        view_b = ViewInfo(
            name="user_summary",
            schema="public",
            definition="SELECT id, name, email FROM users",  # Modified
            is_materialized=False,
            columns=[]
        )
        
        schema_a = SchemaInfo(
            schema_name="public", database_name="db_a", database_type="source",
            postgresql_version="14.5", collection_time="2025-07-14T10:00:00",
            tables=[], views=[view_a], functions=[], sequences=[],
            statistics={}
        )
        
        schema_b = SchemaInfo(
            schema_name="public", database_name="db_b", database_type="target",
            postgresql_version="14.5", collection_time="2025-07-14T10:00:00",
            tables=[], views=[view_b], functions=[], sequences=[],
            statistics={}
        )
        
        result = analyzer.analyze(schema_a, schema_b)
        
        assert len(result.views["modified"]) == 1
        assert "definition" in result.views["modified"][0]["changes"]

    def test_compare_functions(self, analyzer):
        """Test function comparison."""
        func_a = FunctionInfo(
            name="get_user_count",
            schema="public",
            signature="get_user_count()",
            return_type="integer",
            language="sql",
            definition="SELECT COUNT(*) FROM users",
            volatility="STABLE",
            arguments=[]
        )
        
        func_b = FunctionInfo(
            name="get_user_count",
            schema="public", 
            signature="get_user_count()",
            return_type="bigint",  # Changed
            language="sql",
            definition="SELECT COUNT(*) FROM users",
            volatility="STABLE",
            arguments=[]
        )
        
        schema_a = SchemaInfo(
            schema_name="public", database_name="db_a", database_type="source",
            postgresql_version="14.5", collection_time="2025-07-14T10:00:00",
            tables=[], views=[], functions=[func_a], sequences=[],
            statistics={}
        )
        
        schema_b = SchemaInfo(
            schema_name="public", database_name="db_b", database_type="target",
            postgresql_version="14.5", collection_time="2025-07-14T10:00:00",
            tables=[], views=[], functions=[func_b], sequences=[],
            statistics={}
        )
        
        result = analyzer.analyze(schema_a, schema_b)
        
        assert len(result.functions["modified"]) == 1
        assert "return_type" in result.functions["modified"][0]["changes"]

    def test_compare_sequences(self, analyzer):
        """Test sequence comparison."""
        seq_a = SequenceInfo(
            name="users_id_seq",
            schema="public",
            data_type="bigint",
            start_value=1,
            increment=1,
            min_value=1,
            max_value=9223372036854775807,
            is_cycled=False,
            owner_table="users",
            owner_column="id"
        )
        
        seq_b = SequenceInfo(
            name="users_id_seq",
            schema="public",
            data_type="bigint",
            start_value=100,  # Changed
            increment=1,
            min_value=1,
            max_value=9223372036854775807,
            is_cycled=False,
            owner_table="users",
            owner_column="id"
        )
        
        schema_a = SchemaInfo(
            schema_name="public", database_name="db_a", database_type="source",
            postgresql_version="14.5", collection_time="2025-07-14T10:00:00",
            tables=[], views=[], functions=[], sequences=[seq_a],
            statistics={}
        )
        
        schema_b = SchemaInfo(
            schema_name="public", database_name="db_b", database_type="target",
            postgresql_version="14.5", collection_time="2025-07-14T10:00:00",
            tables=[], views=[], functions=[], sequences=[seq_b],
            statistics={}
        )
        
        result = analyzer.analyze(schema_a, schema_b)
        
        assert len(result.sequences["modified"]) == 1
        assert "start_value" in result.sequences["modified"][0]["changes"]


class TestDiffAnalyzerEdgeCases:
    """Test edge cases for DiffAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return DiffAnalyzer()

    def test_case_sensitivity(self, analyzer):
        """Test case sensitivity in names."""
        table_a = TableInfo(
            name="Users", schema="public", table_type="BASE TABLE",
            columns=[], constraints=[], indexes=[], triggers=[],
            table_comment=None, estimated_rows=0, table_size="0"
        )
        
        table_b = TableInfo(
            name="users", schema="public", table_type="BASE TABLE",
            columns=[], constraints=[], indexes=[], triggers=[],
            table_comment=None, estimated_rows=0, table_size="0"
        )
        
        schema_a = SchemaInfo(
            schema_name="public", database_name="db_a", database_type="source",
            postgresql_version="14.5", collection_time="2025-07-14T10:00:00",
            tables=[table_a], views=[], functions=[], sequences=[],
            statistics={}
        )
        
        schema_b = SchemaInfo(
            schema_name="public", database_name="db_b", database_type="target",
            postgresql_version="14.5", collection_time="2025-07-14T10:00:00",
            tables=[table_b], views=[], functions=[], sequences=[],
            statistics={}
        )
        
        result = analyzer.analyze(schema_a, schema_b)
        
        # Different case should be treated as different tables
        assert len(result.tables["added"]) == 1
        assert len(result.tables["removed"]) == 1

    def test_null_values_handling(self, analyzer):
        """Test handling of NULL values in comparisons."""
        col_a = ColumnInfo(
            name="description",
            data_type="text",
            is_nullable=True,
            column_default=None,
            character_maximum_length=None,
            numeric_precision=None,
            numeric_scale=None,
            ordinal_position=1,
            udt_name="text",
            column_comment=None
        )
        
        col_b = ColumnInfo(
            name="description",
            data_type="text",
            is_nullable=True,
            column_default="'default value'",  # Changed from None
            character_maximum_length=None,
            numeric_precision=None,
            numeric_scale=None,
            ordinal_position=1,
            udt_name="text",
            column_comment="Added comment"  # Changed from None
        )
        
        changes = analyzer._compare_column_details(col_a, col_b)
        
        assert changes is not None
        assert "column_default" in changes
        assert changes["column_default"]["from"] is None
        assert changes["column_default"]["to"] == "'default value'"

    def test_large_schema_simulation(self, analyzer):
        """Test with large number of tables and columns."""
        # Create schema A with 50 tables, each with 10 columns
        tables_a = []
        for i in range(50):
            columns = []
            for j in range(10):
                columns.append(ColumnInfo(
                    name=f"col_{j}",
                    data_type="integer",
                    is_nullable=False,
                    column_default=None,
                    character_maximum_length=None,
                    numeric_precision=32,
                    numeric_scale=0,
                    ordinal_position=j + 1,
                    udt_name="int4",
                    column_comment=None
                ))
            
            tables_a.append(TableInfo(
                name=f"table_{i}",
                schema="public",
                table_type="BASE TABLE",
                columns=columns,
                constraints=[],
                indexes=[],
                triggers=[],
                table_comment=None,
                estimated_rows=1000,
                table_size="64 kB"
            ))
        
        # Create schema B identical to A (should result in no changes)
        schema_a = SchemaInfo(
            schema_name="public", database_name="db_a", database_type="source",
            postgresql_version="14.5", collection_time="2025-07-14T10:00:00",
            tables=tables_a, views=[], functions=[], sequences=[],
            statistics={}
        )
        
        schema_b = SchemaInfo(
            schema_name="public", database_name="db_b", database_type="target",
            postgresql_version="14.5", collection_time="2025-07-14T10:00:00",
            tables=tables_a, views=[], functions=[], sequences=[],
            statistics={}
        )
        
        result = analyzer.analyze(schema_a, schema_b)
        
        assert result.summary["total_changes"] == 0
        assert len(result.tables["added"]) == 0
        assert len(result.tables["removed"]) == 0
        assert len(result.tables["modified"]) == 0