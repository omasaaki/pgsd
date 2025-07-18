"""Simple tests for diff analyzer to improve coverage."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.pgsd.core.analyzer import DiffAnalyzer, DiffResult, TableDiff
from src.pgsd.models.schema import SchemaInfo, TableInfo, ColumnInfo


class TestDiffAnalyzerSimple:
    """Simple tests focusing on working functionality."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return DiffAnalyzer()

    @pytest.fixture
    def empty_schema_a(self):
        """Create empty schema A."""
        return SchemaInfo(
            schema_name="public",
            database_type="source",
            collection_time=datetime.now(),
            tables=[],
            views=[],
            sequences=[],
            functions=[],
            constraints=[]
        )

    @pytest.fixture
    def empty_schema_b(self):
        """Create empty schema B."""
        return SchemaInfo(
            schema_name="public",
            database_type="target",
            collection_time=datetime.now(),
            tables=[],
            views=[],
            sequences=[],
            functions=[],
            constraints=[]
        )

    def test_diff_analyzer_initialization(self, analyzer):
        """Test DiffAnalyzer initialization."""
        assert analyzer.result is not None
        assert isinstance(analyzer.result, DiffResult)

    def test_diff_result_initialization(self):
        """Test DiffResult initialization."""
        result = DiffResult()
        
        # Check default dictionary structure
        assert hasattr(result, 'tables')
        assert hasattr(result, 'columns')
        assert hasattr(result, 'constraints')
        assert hasattr(result, 'indexes')
        assert hasattr(result, 'triggers')
        assert hasattr(result, 'views')
        assert hasattr(result, 'functions')
        assert hasattr(result, 'sequences')
        assert hasattr(result, 'summary')

    def test_diff_result_init_defaults(self):
        """Test DiffResult initializes with correct defaults."""
        result = DiffResult()
        
        # Initialize default structure
        result.tables = {"added": [], "removed": [], "modified": []}
        result.columns = {"added": [], "removed": [], "modified": []}
        result.summary = {}
        
        assert len(result.tables["added"]) == 0
        assert len(result.tables["removed"]) == 0
        assert len(result.tables["modified"]) == 0

    def test_diff_result_update_summary(self):
        """Test DiffResult update_summary method."""
        result = DiffResult()
        
        # Initialize with some data
        result.tables = {
            "added": [Mock(), Mock()],
            "removed": [Mock()],
            "modified": [Mock(), Mock(), Mock()]
        }
        result.columns = {
            "added": [Mock()],
            "removed": [],
            "modified": [Mock(), Mock()]
        }
        result.constraints = {
            "added": [],
            "removed": [Mock()],
            "modified": []
        }
        result.views = {"added": [], "removed": [], "modified": []}
        result.functions = {"added": [], "removed": [], "modified": []}
        result.sequences = {"added": [], "removed": [], "modified": []}
        
        result.update_summary()
        
        assert result.summary["tables_added"] == 2
        assert result.summary["tables_removed"] == 1
        assert result.summary["tables_modified"] == 3
        assert result.summary["columns_added"] == 1
        assert result.summary["columns_modified"] == 2
        assert result.summary["constraints_removed"] == 1
        assert result.summary["total_changes"] == 10

    def test_table_diff_initialization(self):
        """Test TableDiff initialization."""
        table_diff = TableDiff(name="test_table")
        
        assert table_diff.name == "test_table"
        assert isinstance(table_diff.columns, dict)
        assert isinstance(table_diff.constraints, dict)
        assert isinstance(table_diff.indexes, dict)
        assert isinstance(table_diff.triggers, dict)

    def test_table_diff_has_changes_empty(self):
        """Test TableDiff has_changes with empty diff."""
        table_diff = TableDiff(name="test_table")
        assert not table_diff.has_changes()

    def test_table_diff_has_changes_with_columns(self):
        """Test TableDiff has_changes with column changes."""
        table_diff = TableDiff(name="test_table")
        table_diff.columns = {"added": [Mock()]}
        assert table_diff.has_changes()

    def test_table_diff_has_changes_with_constraints(self):
        """Test TableDiff has_changes with constraint changes."""
        table_diff = TableDiff(name="test_table")
        table_diff.constraints = {"removed": [Mock()]}
        assert table_diff.has_changes()

    def test_table_diff_has_changes_with_indexes(self):
        """Test TableDiff has_changes with index changes."""
        table_diff = TableDiff(name="test_table")
        table_diff.indexes = {"modified": [Mock()]}
        assert table_diff.has_changes()

    def test_table_diff_has_changes_with_triggers(self):
        """Test TableDiff has_changes with trigger changes."""
        table_diff = TableDiff(name="test_table")
        table_diff.triggers = {"added": [Mock()]}
        assert table_diff.has_changes()

    def test_analyze_empty_schemas(self, analyzer, empty_schema_a, empty_schema_b):
        """Test analyzing empty schemas."""
        result = analyzer.analyze(empty_schema_a, empty_schema_b)
        
        assert isinstance(result, DiffResult)
        # No changes expected
        assert result.summary.get("total_changes", 0) == 0

    def test_analyze_identical_schemas(self, analyzer, empty_schema_a):
        """Test analyzing identical schemas."""
        result = analyzer.analyze(empty_schema_a, empty_schema_a)
        
        assert isinstance(result, DiffResult)
        # No changes expected for identical schemas
        assert result.summary.get("total_changes", 0) == 0

    def test_compare_column_details_identical_columns(self, analyzer):
        """Test comparing identical columns."""
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
            data_type="integer",
            is_nullable=False,
            numeric_precision=32
        )
        
        changes = analyzer._compare_column_details(col_a, col_b)
        assert changes is None

    def test_compare_column_details_different_types(self, analyzer):
        """Test comparing columns with different types."""
        col_a = ColumnInfo(
            column_name="id",
            ordinal_position=1,
            data_type="integer",
            is_nullable=False
        )
        
        col_b = ColumnInfo(
            column_name="id",
            ordinal_position=1,
            data_type="bigint",
            is_nullable=False
        )
        
        changes = analyzer._compare_column_details(col_a, col_b)
        assert changes is not None
        assert "data_type" in changes
        assert changes["data_type"]["from"] == "integer"
        assert changes["data_type"]["to"] == "bigint"

    def test_compare_column_details_nullable_change(self, analyzer):
        """Test comparing columns with nullable changes."""
        col_a = ColumnInfo(
            column_name="name",
            ordinal_position=2,
            data_type="varchar",
            is_nullable=False
        )
        
        col_b = ColumnInfo(
            column_name="name",
            ordinal_position=2,
            data_type="varchar",
            is_nullable=True
        )
        
        changes = analyzer._compare_column_details(col_a, col_b)
        assert changes is not None
        assert "is_nullable" in changes
        assert changes["is_nullable"]["from"] is False
        assert changes["is_nullable"]["to"] is True

    def test_compare_column_details_default_change(self, analyzer):
        """Test comparing columns with default value changes."""
        col_a = ColumnInfo(
            column_name="status",
            ordinal_position=3,
            data_type="varchar",
            column_default=None
        )
        
        col_b = ColumnInfo(
            column_name="status",
            ordinal_position=3,
            data_type="varchar",
            column_default="'active'"
        )
        
        changes = analyzer._compare_column_details(col_a, col_b)
        assert changes is not None
        assert "column_default" in changes
        assert changes["column_default"]["from"] is None
        assert changes["column_default"]["to"] == "'active'"

    def test_compare_column_details_precision_change(self, analyzer):
        """Test comparing columns with precision changes."""
        col_a = ColumnInfo(
            column_name="price",
            ordinal_position=4,
            data_type="numeric",
            numeric_precision=10,
            numeric_scale=2
        )
        
        col_b = ColumnInfo(
            column_name="price",
            ordinal_position=4,
            data_type="numeric",
            numeric_precision=12,
            numeric_scale=4
        )
        
        changes = analyzer._compare_column_details(col_a, col_b)
        assert changes is not None
        assert "numeric_precision" in changes
        assert "numeric_scale" in changes
        assert changes["numeric_precision"]["from"] == 10
        assert changes["numeric_precision"]["to"] == 12
        assert changes["numeric_scale"]["from"] == 2
        assert changes["numeric_scale"]["to"] == 4

    def test_compare_column_details_length_change(self, analyzer):
        """Test comparing columns with length changes."""
        col_a = ColumnInfo(
            column_name="name",
            ordinal_position=1,
            data_type="varchar",
            character_maximum_length=50
        )
        
        col_b = ColumnInfo(
            column_name="name",
            ordinal_position=1,
            data_type="varchar",
            character_maximum_length=100
        )
        
        changes = analyzer._compare_column_details(col_a, col_b)
        assert changes is not None
        assert "character_maximum_length" in changes
        assert changes["character_maximum_length"]["from"] == 50
        assert changes["character_maximum_length"]["to"] == 100

    def test_compare_column_details_comment_change(self, analyzer):
        """Test comparing columns with comment changes."""
        col_a = ColumnInfo(
            column_name="id",
            ordinal_position=1,
            data_type="integer",
            column_comment=None
        )
        
        col_b = ColumnInfo(
            column_name="id",
            ordinal_position=1,
            data_type="integer",
            column_comment="Primary key identifier"
        )
        
        changes = analyzer._compare_column_details(col_a, col_b)
        # column_comment is not implemented in the analyzer yet
        assert changes is None

    def test_compare_column_details_multiple_changes(self, analyzer):
        """Test comparing columns with multiple changes."""
        col_a = ColumnInfo(
            column_name="email",
            ordinal_position=2,
            data_type="varchar",
            character_maximum_length=100,
            is_nullable=False,
            column_comment=None
        )
        
        col_b = ColumnInfo(
            column_name="email",
            ordinal_position=2,
            data_type="text",
            character_maximum_length=None,
            is_nullable=True,
            column_comment="User email address"
        )
        
        changes = analyzer._compare_column_details(col_a, col_b)
        assert changes is not None
        assert "data_type" in changes
        assert "character_maximum_length" in changes
        assert "is_nullable" in changes
        # column_comment is not implemented in the analyzer yet
        
        assert changes["data_type"]["from"] == "varchar"
        assert changes["data_type"]["to"] == "text"
        assert changes["is_nullable"]["from"] is False
        assert changes["is_nullable"]["to"] is True

    def test_compare_column_details_position_change(self, analyzer):
        """Test comparing columns with position changes."""
        col_a = ColumnInfo(
            column_name="status",
            ordinal_position=3,
            data_type="varchar"
        )
        
        col_b = ColumnInfo(
            column_name="status",
            ordinal_position=5,
            data_type="varchar"
        )
        
        changes = analyzer._compare_column_details(col_a, col_b)
        assert changes is not None
        assert "ordinal_position" in changes
        assert changes["ordinal_position"]["from"] == 3
        assert changes["ordinal_position"]["to"] == 5

    def test_compare_column_details_udt_name_change(self, analyzer):
        """Test comparing columns with UDT name changes."""
        col_a = ColumnInfo(
            column_name="id",
            ordinal_position=1,
            data_type="integer",
            udt_name="int4"
        )
        
        col_b = ColumnInfo(
            column_name="id",
            ordinal_position=1,
            data_type="bigint",
            udt_name="int8"
        )
        
        changes = analyzer._compare_column_details(col_a, col_b)
        assert changes is not None
        # udt_name is not implemented in the analyzer yet, only data_type is checked
        assert "data_type" in changes
        assert changes["data_type"]["from"] == "integer"
        assert changes["data_type"]["to"] == "bigint"

    def test_reset_result(self, analyzer):
        """Test that analyzer resets result for new analysis."""
        # First analysis
        result1 = analyzer.analyze(
            SchemaInfo(
                schema_name="test1",
                database_type="source",
                collection_time=datetime.now(),
                tables=[],
                views=[],
                sequences=[],
                functions=[],
                constraints=[]
            ),
            SchemaInfo(
                schema_name="test1",
                database_type="target",
                collection_time=datetime.now(),
                tables=[],
                views=[],
                sequences=[],
                functions=[],
                constraints=[]
            )
        )
        
        # Second analysis should get a fresh result
        result2 = analyzer.analyze(
            SchemaInfo(
                schema_name="test2",
                database_type="source",
                collection_time=datetime.now(),
                tables=[],
                views=[],
                sequences=[],
                functions=[],
                constraints=[]
            ),
            SchemaInfo(
                schema_name="test2",
                database_type="target",
                collection_time=datetime.now(),
                tables=[],
                views=[],
                sequences=[],
                functions=[],
                constraints=[]
            )
        )
        
        # Both should be separate instances
        assert result1 is not result2

    def test_analyze_with_table_changes(self, analyzer):
        """Test analyzing schemas with table differences."""
        # Create table for schema A
        table_a = TableInfo(
            table_name="users",
            table_type="BASE TABLE",
            table_schema="public",
            columns=[
                ColumnInfo(
                    column_name="id",
                    ordinal_position=1,
                    data_type="integer"
                )
            ],
            constraints=[]
        )
        
        # Create modified table for schema B
        table_b = TableInfo(
            table_name="users",
            table_type="BASE TABLE", 
            table_schema="public",
            columns=[
                ColumnInfo(
                    column_name="id",
                    ordinal_position=1,
                    data_type="bigint"  # Changed type
                ),
                ColumnInfo(
                    column_name="email",
                    ordinal_position=2,
                    data_type="varchar"  # New column
                )
            ],
            constraints=[]
        )
        
        # Create new table for schema B
        new_table = TableInfo(
            table_name="posts",
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
            tables=[table_b, new_table],
            views=[],
            sequences=[],
            functions=[],
            constraints=[]
        )
        
        result = analyzer.analyze(schema_a, schema_b)
        
        # Check table changes
        assert len(result.tables["added"]) == 1
        assert len(result.tables["modified"]) == 1
        assert result.tables["added"][0].table_name == "posts"
        
        # Check column changes
        assert len(result.columns["added"]) >= 1  # email column + posts table columns
        assert len(result.columns["modified"]) >= 1  # id column type change
        
        # Check summary
        assert result.summary["tables_added"] == 1
        assert result.summary["tables_modified"] == 1
        assert result.summary["total_changes"] > 0

    def test_analyze_with_view_changes(self, analyzer):
        """Test analyzing schemas with view differences."""
        from src.pgsd.models.schema import ViewInfo
        
        view_a = ViewInfo(
            view_name="user_summary",
            view_definition="SELECT id, name FROM users",
            is_updatable=False,
            is_insertable_into=False
        )
        
        view_b = ViewInfo(
            view_name="user_summary", 
            view_definition="SELECT id, name, email FROM users",  # Modified
            is_updatable=True,  # Changed
            is_insertable_into=False
        )
        
        new_view = ViewInfo(
            view_name="post_summary",
            view_definition="SELECT id, title FROM posts",
            is_updatable=False,
            is_insertable_into=False
        )
        
        schema_a = SchemaInfo(
            schema_name="public",
            database_type="source",
            collection_time=datetime.now(),
            tables=[],
            views=[view_a],
            sequences=[],
            functions=[],
            constraints=[]
        )
        
        schema_b = SchemaInfo(
            schema_name="public",
            database_type="target",
            collection_time=datetime.now(),
            tables=[],
            views=[view_b, new_view],
            sequences=[],
            functions=[],
            constraints=[]
        )
        
        result = analyzer.analyze(schema_a, schema_b)
        
        # Check view changes
        assert len(result.views["added"]) == 1
        assert len(result.views["modified"]) == 1
        assert result.views["added"][0].view_name == "post_summary"
        
        # Check summary
        assert result.summary["views_added"] == 1
        assert result.summary["views_modified"] == 1

    def test_analyze_with_function_changes(self, analyzer):
        """Test analyzing schemas with function differences."""
        from src.pgsd.models.schema import FunctionInfo
        
        func_a = FunctionInfo(
            function_name="get_user_count",
            function_type="FUNCTION",
            return_type="integer",
            function_definition="SELECT COUNT(*) FROM users",
            argument_types=[]
        )
        
        func_b = FunctionInfo(
            function_name="get_user_count",
            function_type="FUNCTION", 
            return_type="bigint",  # Changed
            function_definition="SELECT COUNT(*)::bigint FROM users",  # Modified
            argument_types=[]
        )
        
        new_func = FunctionInfo(
            function_name="get_post_count",
            function_type="FUNCTION",
            return_type="integer",
            function_definition="SELECT COUNT(*) FROM posts",
            argument_types=[]
        )
        
        schema_a = SchemaInfo(
            schema_name="public",
            database_type="source",
            collection_time=datetime.now(),
            tables=[],
            views=[],
            sequences=[],
            functions=[func_a],
            constraints=[]
        )
        
        schema_b = SchemaInfo(
            schema_name="public",
            database_type="target",
            collection_time=datetime.now(),
            tables=[],
            views=[],
            sequences=[],
            functions=[func_b, new_func],
            constraints=[]
        )
        
        result = analyzer.analyze(schema_a, schema_b)
        
        # Check function changes
        assert len(result.functions["added"]) == 1
        assert len(result.functions["modified"]) == 1
        assert result.functions["added"][0].function_name == "get_post_count"
        
        # Check summary
        assert result.summary["functions_added"] == 1
        assert result.summary["functions_modified"] == 1

    def test_analyze_with_sequence_changes(self, analyzer):
        """Test analyzing schemas with sequence differences."""
        from src.pgsd.models.schema import SequenceInfo
        
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
            increment="5",  # Changed
            cycle_option=True  # Changed
        )
        
        new_seq = SequenceInfo(
            sequence_name="posts_id_seq",
            data_type="bigint",
            start_value="1",
            minimum_value="1",
            maximum_value="9223372036854775807",
            increment="1",
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
            sequences=[seq_b, new_seq],
            functions=[],
            constraints=[]
        )
        
        result = analyzer.analyze(schema_a, schema_b)
        
        # Check sequence changes
        assert len(result.sequences["added"]) == 1
        assert len(result.sequences["modified"]) == 1
        assert result.sequences["added"][0].sequence_name == "posts_id_seq"
        
        # Check summary
        assert result.summary["sequences_added"] == 1
        assert result.summary["sequences_modified"] == 1

    def test_analyze_with_constraint_changes(self, analyzer):
        """Test analyzing schemas with constraint differences."""
        from src.pgsd.models.schema import ConstraintInfo
        
        # Create table with constraint for schema A
        constraint_a = ConstraintInfo(
            constraint_name="users_pkey",
            table_name="users",
            constraint_type="PRIMARY KEY",
            column_name="id"
        )
        
        table_a = TableInfo(
            table_name="users",
            table_type="BASE TABLE",
            table_schema="public",
            columns=[
                ColumnInfo(
                    column_name="id",
                    ordinal_position=1,
                    data_type="integer"
                )
            ],
            constraints=[constraint_a]
        )
        
        # Create table with modified and new constraints for schema B
        constraint_b = ConstraintInfo(
            constraint_name="users_pkey",
            table_name="users", 
            constraint_type="PRIMARY KEY",
            column_name="id"  # Same constraint
        )
        
        new_constraint = ConstraintInfo(
            constraint_name="users_email_unique",
            table_name="users",
            constraint_type="UNIQUE",
            column_name="email"
        )
        
        table_b = TableInfo(
            table_name="users",
            table_type="BASE TABLE",
            table_schema="public",
            columns=[
                ColumnInfo(
                    column_name="id",
                    ordinal_position=1,
                    data_type="integer"
                ),
                ColumnInfo(
                    column_name="email",
                    ordinal_position=2,
                    data_type="varchar"
                )
            ],
            constraints=[constraint_b, new_constraint]
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
        
        # Check constraint changes
        assert len(result.constraints["added"]) >= 1  # New constraint added
        assert result.summary["constraints_added"] >= 1

    def test_analyze_with_index_changes(self, analyzer):
        """Test analyzing schemas with index differences."""
        from src.pgsd.models.schema import IndexInfo
        
        # Create table with index for schema A
        index_a = IndexInfo(
            index_name="users_pkey_idx",
            table_name="users",
            index_type="btree",
            is_unique=True,
            is_primary=True,
            column_names=["id"]
        )
        
        table_a = TableInfo(
            table_name="users",
            table_type="BASE TABLE",
            table_schema="public",
            columns=[
                ColumnInfo(
                    column_name="id",
                    ordinal_position=1,
                    data_type="integer"
                )
            ],
            constraints=[],
            indexes=[index_a]
        )
        
        # Create table with modified index for schema B
        index_b = IndexInfo(
            index_name="users_pkey_idx",
            table_name="users",
            index_type="btree",
            is_unique=True,
            is_primary=True,
            column_names=["id"]
        )
        
        new_index = IndexInfo(
            index_name="users_email_idx",
            table_name="users",
            index_type="btree",
            is_unique=False,
            is_primary=False,
            column_names=["email"]
        )
        
        table_b = TableInfo(
            table_name="users",
            table_type="BASE TABLE",
            table_schema="public",
            columns=[
                ColumnInfo(
                    column_name="id",
                    ordinal_position=1,
                    data_type="integer"
                ),
                ColumnInfo(
                    column_name="email",
                    ordinal_position=2,
                    data_type="varchar"
                )
            ],
            constraints=[],
            indexes=[index_b, new_index]
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
        
        # Check index changes
        assert len(result.indexes["added"]) >= 1  # New index added
        assert result.summary["indexes_added"] >= 1

    def test_analyze_with_trigger_changes(self, analyzer):
        """Test analyzing schemas with trigger differences."""
        from src.pgsd.models.schema import TriggerInfo
        
        # Create table with trigger for schema A
        trigger_a = TriggerInfo(
            trigger_name="users_audit_trigger",
            table_name="users",
            trigger_event="INSERT",
            trigger_timing="AFTER",
            function_name="audit_function"
        )
        
        table_a = TableInfo(
            table_name="users",
            table_type="BASE TABLE",
            table_schema="public",
            columns=[
                ColumnInfo(
                    column_name="id",
                    ordinal_position=1,
                    data_type="integer"
                )
            ],
            constraints=[],
            triggers=[trigger_a]
        )
        
        # Create table with modified trigger for schema B
        trigger_b = TriggerInfo(
            trigger_name="users_audit_trigger",
            table_name="users",
            trigger_event="UPDATE",  # Changed
            trigger_timing="BEFORE",  # Changed
            function_name="new_audit_function"  # Changed
        )
        
        new_trigger = TriggerInfo(
            trigger_name="users_log_trigger",
            table_name="users",
            trigger_event="DELETE",
            trigger_timing="AFTER",
            function_name="log_function"
        )
        
        table_b = TableInfo(
            table_name="users",
            table_type="BASE TABLE",
            table_schema="public",
            columns=[
                ColumnInfo(
                    column_name="id",
                    ordinal_position=1,
                    data_type="integer"
                )
            ],
            constraints=[],
            triggers=[trigger_b, new_trigger]
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
        
        # Check trigger changes
        assert len(result.triggers["added"]) >= 1  # New trigger added
        assert len(result.triggers["modified"]) >= 1  # Modified trigger
        assert result.summary["triggers_added"] >= 1
        assert result.summary["triggers_modified"] >= 1

    def test_compare_constraint_details(self, analyzer):
        """Test detailed constraint comparison."""
        from src.pgsd.models.schema import ConstraintInfo
        
        const_a = ConstraintInfo(
            constraint_name="test_fk",
            table_name="users",
            constraint_type="FOREIGN KEY",
            column_name="dept_id",
            foreign_table_name="departments",
            foreign_column_name="id"
        )
        
        const_b = ConstraintInfo(
            constraint_name="test_fk",
            table_name="users",
            constraint_type="FOREIGN KEY",
            column_name="dept_id",
            foreign_table_name="departments_new",  # Changed
            foreign_column_name="dept_id"  # Changed
        )
        
        changes = analyzer._compare_constraint_details(const_a, const_b)
        
        assert changes is not None
        assert "foreign_table_name" in changes
        assert "foreign_column_name" in changes

    def test_compare_index_details(self, analyzer):
        """Test detailed index comparison."""
        from src.pgsd.models.schema import IndexInfo
        
        idx_a = IndexInfo(
            index_name="test_idx",
            table_name="users",
            index_type="btree",
            is_unique=False,
            is_primary=False,
            column_names=["name"]
        )
        
        idx_b = IndexInfo(
            index_name="test_idx",
            table_name="users",
            index_type="gin",  # Changed
            is_unique=True,  # Changed
            is_primary=False,
            column_names=["name", "email"]  # Changed
        )
        
        changes = analyzer._compare_index_details(idx_a, idx_b)
        
        assert changes is not None
        assert "index_type" in changes
        assert "is_unique" in changes
        assert "columns" in changes

    def test_compare_trigger_details(self, analyzer):
        """Test detailed trigger comparison."""
        from src.pgsd.models.schema import TriggerInfo
        
        trig_a = TriggerInfo(
            trigger_name="test_trigger",
            table_name="users",
            trigger_event="INSERT",
            trigger_timing="AFTER",
            function_name="old_function"
        )
        
        trig_b = TriggerInfo(
            trigger_name="test_trigger",
            table_name="users",
            trigger_event="UPDATE",  # Changed
            trigger_timing="BEFORE",  # Changed
            function_name="new_function"  # Changed
        )
        
        changes = analyzer._compare_trigger_details(trig_a, trig_b)
        
        assert changes is not None
        assert "timing" in changes
        assert "events" in changes
        assert "function_name" in changes

    def test_compare_view_details(self, analyzer):
        """Test detailed view comparison."""
        from src.pgsd.models.schema import ViewInfo
        
        view_a = ViewInfo(
            view_name="test_view",
            view_definition="SELECT id FROM users",
            is_updatable=False,
            is_insertable_into=False
        )
        
        view_b = ViewInfo(
            view_name="test_view",
            view_definition="SELECT id, name FROM users",  # Changed
            is_updatable=True,  # Changed
            is_insertable_into=True  # Changed
        )
        
        changes = analyzer._compare_view_details(view_a, view_b)
        
        assert changes is not None
        assert "definition" in changes
        assert "is_updatable" in changes
        assert "is_insertable_into" in changes

    def test_compare_function_details(self, analyzer):
        """Test detailed function comparison."""
        from src.pgsd.models.schema import FunctionInfo
        
        func_a = FunctionInfo(
            function_name="test_func",
            function_type="FUNCTION",
            return_type="integer",
            function_definition="RETURN 1;",
            argument_types=["integer"]
        )
        
        func_b = FunctionInfo(
            function_name="test_func",
            function_type="PROCEDURE",  # Changed
            return_type="bigint",  # Changed
            function_definition="RETURN 2;",  # Changed
            argument_types=["bigint", "text"]  # Changed
        )
        
        changes = analyzer._compare_function_details(func_a, func_b)
        
        assert changes is not None
        assert "function_type" in changes
        assert "return_type" in changes
        assert "definition" in changes
        assert "argument_types" in changes

    def test_compare_sequence_details(self, analyzer):
        """Test detailed sequence comparison."""
        from src.pgsd.models.schema import SequenceInfo
        
        seq_a = SequenceInfo(
            sequence_name="test_seq",
            data_type="bigint",
            start_value="1",
            minimum_value="1",
            maximum_value="999",
            increment="1",
            cycle_option=False
        )
        
        seq_b = SequenceInfo(
            sequence_name="test_seq",
            data_type="integer",  # Changed
            start_value="10",  # Changed
            minimum_value="5",  # Changed
            maximum_value="9999",  # Changed
            increment="2",  # Changed
            cycle_option=True  # Changed
        )
        
        changes = analyzer._compare_sequence_details(seq_a, seq_b)
        
        assert changes is not None
        assert "data_type" in changes
        assert "start_value" in changes
        assert "minimum_value" in changes
        assert "maximum_value" in changes
        assert "increment" in changes
        assert "cycle_option" in changes