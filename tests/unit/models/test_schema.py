"""Tests for schema data models."""

import pytest
from datetime import datetime
from dataclasses import FrozenInstanceError

from src.pgsd.models.schema import (
    ObjectType,
    ConstraintType,
    IndexType,
    ColumnInfo,
    ConstraintInfo,
    IndexInfo,
    TableInfo,
    ViewInfo,
    SequenceInfo,
    FunctionInfo,
    SchemaInfo,
    SchemaComparison,
)


class TestColumnInfo:
    """Test cases for ColumnInfo class."""

    def test_column_info_creation(self):
        """Test column info creation."""
        column = ColumnInfo(
            column_name="id",
            ordinal_position=1,
            column_default="nextval('users_id_seq'::regclass)",
            is_nullable=False,
            data_type="integer",
            numeric_precision=32,
            numeric_scale=0,
            udt_name="int4",
            column_comment="Primary key",
        )

        assert column.column_name == "id"
        assert column.ordinal_position == 1
        assert column.is_nullable is False
        assert column.data_type == "integer"
        assert column.column_comment == "Primary key"

    def test_column_info_immutability(self):
        """Test column info immutability."""
        column = ColumnInfo(column_name="id", ordinal_position=1)

        with pytest.raises(FrozenInstanceError):
            column.column_name = "new_name"

    def test_column_info_to_dict(self):
        """Test column info to dictionary conversion."""
        column = ColumnInfo(
            column_name="username",
            ordinal_position=2,
            is_nullable=False,
            data_type="varchar",
            character_maximum_length=50,
        )

        result = column.to_dict()

        assert result["column_name"] == "username"
        assert result["ordinal_position"] == 2
        assert result["character_maximum_length"] == 50

    def test_column_info_from_dict(self):
        """Test column info from dictionary creation."""
        data = {
            "column_name": "email",
            "ordinal_position": 3,
            "is_nullable": True,
            "data_type": "varchar",
            "character_maximum_length": 255,
        }

        column = ColumnInfo.from_dict(data)

        assert column.column_name == "email"
        assert column.ordinal_position == 3
        assert column.is_nullable is True
        assert column.character_maximum_length == 255


class TestConstraintInfo:
    """Test cases for ConstraintInfo class."""

    def test_constraint_info_creation(self):
        """Test constraint info creation."""
        constraint = ConstraintInfo(
            constraint_name="users_pkey",
            table_name="users",
            constraint_type="PRIMARY KEY",
            column_name="id",
        )

        assert constraint.constraint_name == "users_pkey"
        assert constraint.table_name == "users"
        assert constraint.constraint_type == "PRIMARY KEY"
        assert constraint.column_name == "id"

    def test_foreign_key_constraint(self):
        """Test foreign key constraint creation."""
        constraint = ConstraintInfo(
            constraint_name="fk_user_id",
            table_name="posts",
            constraint_type="FOREIGN KEY",
            column_name="user_id",
            foreign_table_name="users",
            foreign_column_name="id",
        )

        assert constraint.foreign_table_name == "users"
        assert constraint.foreign_column_name == "id"


class TestIndexInfo:
    """Test cases for IndexInfo class."""

    def test_index_info_creation(self):
        """Test index info creation."""
        index = IndexInfo(
            index_name="idx_username",
            table_name="users",
            index_type="btree",
            is_unique=True,
            is_primary=False,
            column_names=["username"],
            index_definition="CREATE UNIQUE INDEX idx_username ON users (username)",
        )

        assert index.index_name == "idx_username"
        assert index.is_unique is True
        assert index.is_primary is False
        assert index.column_names == ["username"]


class TestTableInfo:
    """Test cases for TableInfo class."""

    def test_table_info_creation(self):
        """Test table info creation."""
        columns = [
            ColumnInfo(column_name="id", ordinal_position=1, data_type="integer"),
            ColumnInfo(column_name="name", ordinal_position=2, data_type="varchar"),
        ]

        table = TableInfo(
            table_name="users",
            table_type="BASE TABLE",
            table_schema="public",
            table_comment="User information",
            estimated_rows=1000,
            columns=columns,
        )

        assert table.table_name == "users"
        assert table.table_type == "BASE TABLE"
        assert len(table.columns) == 2
        assert table.estimated_rows == 1000

    def test_get_column(self):
        """Test getting column by name."""
        columns = [
            ColumnInfo(column_name="id", ordinal_position=1, data_type="integer"),
            ColumnInfo(column_name="name", ordinal_position=2, data_type="varchar"),
        ]

        table = TableInfo(
            table_name="users",
            table_type="BASE TABLE",
            table_schema="public",
            columns=columns,
        )

        column = table.get_column("name")
        assert column is not None
        assert column.column_name == "name"
        assert column.data_type == "varchar"

        # Test non-existent column
        assert table.get_column("nonexistent") is None

    def test_get_primary_key_columns(self):
        """Test getting primary key columns."""
        constraints = [
            ConstraintInfo(
                constraint_name="users_pkey",
                table_name="users",
                constraint_type="PRIMARY KEY",
                column_name="id",
            )
        ]

        table = TableInfo(
            table_name="users",
            table_type="BASE TABLE",
            table_schema="public",
            constraints=constraints,
        )

        pk_columns = table.get_primary_key_columns()
        assert pk_columns == ["id"]

    def test_table_info_to_dict(self):
        """Test table info to dictionary conversion."""
        columns = [
            ColumnInfo(column_name="id", ordinal_position=1, data_type="integer")
        ]

        table = TableInfo(
            table_name="users",
            table_type="BASE TABLE",
            table_schema="public",
            columns=columns,
        )

        result = table.to_dict()

        assert result["table_name"] == "users"
        assert result["table_type"] == "BASE TABLE"
        assert len(result["columns"]) == 1
        assert result["columns"][0]["column_name"] == "id"

    def test_table_info_from_dict(self):
        """Test table info from dictionary creation."""
        data = {
            "table_name": "posts",
            "table_type": "BASE TABLE",
            "table_schema": "public",
            "table_comment": "Blog posts",
            "estimated_rows": 500,
            "table_size": "64 kB",
            "columns": [
                {
                    "column_name": "id",
                    "ordinal_position": 1,
                    "data_type": "integer",
                    "is_nullable": False,
                }
            ],
            "constraints": [],
            "indexes": [],
            "triggers": [],
        }

        table = TableInfo.from_dict(data)

        assert table.table_name == "posts"
        assert table.table_comment == "Blog posts"
        assert table.estimated_rows == 500
        assert len(table.columns) == 1
        assert table.columns[0].column_name == "id"


class TestViewInfo:
    """Test cases for ViewInfo class."""

    def test_view_info_creation(self):
        """Test view info creation."""
        view = ViewInfo(
            view_name="user_summary",
            view_definition="SELECT id, username FROM users",
            is_updatable=False,
            is_insertable_into=False,
            view_comment="User summary view",
        )

        assert view.view_name == "user_summary"
        assert view.is_updatable is False
        assert view.is_insertable_into is False
        assert view.view_comment == "User summary view"


class TestSequenceInfo:
    """Test cases for SequenceInfo class."""

    def test_sequence_info_creation(self):
        """Test sequence info creation."""
        sequence = SequenceInfo(
            sequence_name="users_id_seq",
            data_type="bigint",
            start_value="1",
            minimum_value="1",
            maximum_value="9223372036854775807",
            increment="1",
            cycle_option=False,
        )

        assert sequence.sequence_name == "users_id_seq"
        assert sequence.data_type == "bigint"
        assert sequence.increment == "1"
        assert sequence.cycle_option is False


class TestFunctionInfo:
    """Test cases for FunctionInfo class."""

    def test_function_info_creation(self):
        """Test function info creation."""
        function = FunctionInfo(
            function_name="get_user_count",
            function_type="FUNCTION",
            return_type="integer",
            function_definition="BEGIN RETURN (SELECT COUNT(*) FROM users); END;",
            argument_types=["integer"],
            argument_names=["min_id"],
        )

        assert function.function_name == "get_user_count"
        assert function.return_type == "integer"
        assert function.argument_types == ["integer"]
        assert function.argument_names == ["min_id"]


class TestSchemaInfo:
    """Test cases for SchemaInfo class."""

    def test_schema_info_creation(self):
        """Test schema info creation."""
        collection_time = datetime.now()

        schema = SchemaInfo(
            schema_name="public",
            database_type="source",
            collection_time=collection_time,
        )

        assert schema.schema_name == "public"
        assert schema.database_type == "source"
        assert schema.collection_time == collection_time
        assert len(schema.tables) == 0
        assert len(schema.views) == 0

    def test_schema_info_with_tables(self):
        """Test schema info with tables."""
        tables = [
            TableInfo(
                table_name="users", table_type="BASE TABLE", table_schema="public"
            ),
            TableInfo(
                table_name="posts", table_type="BASE TABLE", table_schema="public"
            ),
        ]

        schema = SchemaInfo(
            schema_name="public",
            database_type="source",
            collection_time=datetime.now(),
            tables=tables,
        )

        assert len(schema.tables) == 2
        assert schema.tables[0].table_name == "users"
        assert schema.tables[1].table_name == "posts"

    def test_get_table(self):
        """Test getting table by name."""
        tables = [
            TableInfo(
                table_name="users", table_type="BASE TABLE", table_schema="public"
            )
        ]

        schema = SchemaInfo(
            schema_name="public",
            database_type="source",
            collection_time=datetime.now(),
            tables=tables,
        )

        table = schema.get_table("users")
        assert table is not None
        assert table.table_name == "users"

        # Test non-existent table
        assert schema.get_table("nonexistent") is None

    def test_get_object_count(self):
        """Test getting object count statistics."""
        tables = [
            TableInfo(
                table_name="users", table_type="BASE TABLE", table_schema="public"
            )
        ]

        views = [
            ViewInfo(
                view_name="user_summary",
                view_definition="SELECT * FROM users",
                is_updatable=False,
                is_insertable_into=False,
            )
        ]

        schema = SchemaInfo(
            schema_name="public",
            database_type="source",
            collection_time=datetime.now(),
            tables=tables,
            views=views,
        )

        counts = schema.get_object_count()

        assert counts["tables"] == 1
        assert counts["views"] == 1
        assert counts["sequences"] == 0
        assert counts["functions"] == 0

    def test_schema_info_to_dict(self):
        """Test schema info to dictionary conversion."""
        collection_time = datetime.now()

        schema = SchemaInfo(
            schema_name="test", database_type="source", collection_time=collection_time
        )

        result = schema.to_dict()

        assert result["schema_name"] == "test"
        assert result["database_type"] == "source"
        assert result["collection_time"] == collection_time.isoformat()
        assert "tables" in result
        assert "views" in result

    def test_schema_info_from_dict(self):
        """Test schema info from dictionary creation."""
        collection_time = datetime.now()

        data = {
            "schema_name": "test",
            "database_type": "target",
            "collection_time": collection_time.isoformat(),
            "tables": [],
            "views": [],
            "sequences": [],
            "functions": [],
            "constraints": [],
            "indexes": [],
            "triggers": [],
        }

        schema = SchemaInfo.from_dict(data)

        assert schema.schema_name == "test"
        assert schema.database_type == "target"
        assert schema.collection_time == collection_time

    def test_schema_info_json_serialization(self):
        """Test schema info JSON serialization."""
        collection_time = datetime.now()

        schema = SchemaInfo(
            schema_name="test", database_type="source", collection_time=collection_time
        )

        # Test to_json
        json_str = schema.to_json()
        assert isinstance(json_str, str)

        # Test from_json
        schema_from_json = SchemaInfo.from_json(json_str)
        assert schema_from_json.schema_name == "test"
        assert schema_from_json.database_type == "source"
        assert schema_from_json.collection_time == collection_time


class TestSchemaComparison:
    """Test cases for SchemaComparison class."""

    def test_schema_comparison_creation(self):
        """Test schema comparison creation."""
        collection_time = datetime.now()
        comparison_time = datetime.now()

        source_schema = SchemaInfo(
            schema_name="public",
            database_type="source",
            collection_time=collection_time,
        )

        target_schema = SchemaInfo(
            schema_name="public",
            database_type="target",
            collection_time=collection_time,
        )

        comparison = SchemaComparison(
            source_schema=source_schema,
            target_schema=target_schema,
            comparison_time=comparison_time,
            differences=[{"type": "table_added", "name": "new_table"}],
        )

        assert comparison.source_schema.database_type == "source"
        assert comparison.target_schema.database_type == "target"
        assert comparison.comparison_time == comparison_time
        assert len(comparison.differences) == 1

    def test_schema_comparison_json_serialization(self):
        """Test schema comparison JSON serialization."""
        collection_time = datetime.now()
        comparison_time = datetime.now()

        source_schema = SchemaInfo(
            schema_name="public",
            database_type="source",
            collection_time=collection_time,
        )

        target_schema = SchemaInfo(
            schema_name="public",
            database_type="target",
            collection_time=collection_time,
        )

        comparison = SchemaComparison(
            source_schema=source_schema,
            target_schema=target_schema,
            comparison_time=comparison_time,
        )

        # Test to_json
        json_str = comparison.to_json()
        assert isinstance(json_str, str)

        # Test from_json
        comparison_from_json = SchemaComparison.from_json(json_str)
        assert comparison_from_json.source_schema.database_type == "source"
        assert comparison_from_json.target_schema.database_type == "target"


class TestEnums:
    """Test cases for enum classes."""

    def test_object_type_enum(self):
        """Test ObjectType enum."""
        assert ObjectType.TABLE.value == "table"
        assert ObjectType.VIEW.value == "view"
        assert ObjectType.SEQUENCE.value == "sequence"
        assert ObjectType.FUNCTION.value == "function"

    def test_constraint_type_enum(self):
        """Test ConstraintType enum."""
        assert ConstraintType.PRIMARY_KEY.value == "PRIMARY KEY"
        assert ConstraintType.FOREIGN_KEY.value == "FOREIGN KEY"
        assert ConstraintType.UNIQUE.value == "UNIQUE"
        assert ConstraintType.CHECK.value == "CHECK"

    def test_index_type_enum(self):
        """Test IndexType enum."""
        assert IndexType.BTREE.value == "btree"
        assert IndexType.HASH.value == "hash"
        assert IndexType.GIN.value == "gin"
        assert IndexType.GIST.value == "gist"


class TestDataModelIntegration:
    """Integration tests for data models."""

    def test_complete_schema_structure(self):
        """Test complete schema structure creation."""
        # Create columns
        columns = [
            ColumnInfo(
                column_name="id",
                ordinal_position=1,
                data_type="integer",
                is_nullable=False,
            ),
            ColumnInfo(
                column_name="username",
                ordinal_position=2,
                data_type="varchar",
                character_maximum_length=50,
                is_nullable=False,
            ),
        ]

        # Create constraints
        constraints = [
            ConstraintInfo(
                constraint_name="users_pkey",
                table_name="users",
                constraint_type="PRIMARY KEY",
                column_name="id",
            ),
            ConstraintInfo(
                constraint_name="users_username_unique",
                table_name="users",
                constraint_type="UNIQUE",
                column_name="username",
            ),
        ]

        # Create indexes
        indexes = [
            IndexInfo(
                index_name="users_pkey",
                table_name="users",
                index_type="btree",
                is_unique=True,
                is_primary=True,
                column_names=["id"],
            )
        ]

        # Create table
        table = TableInfo(
            table_name="users",
            table_type="BASE TABLE",
            table_schema="public",
            table_comment="User information table",
            estimated_rows=1000,
            columns=columns,
            constraints=constraints,
            indexes=indexes,
        )

        # Create schema
        schema = SchemaInfo(
            schema_name="public",
            database_type="source",
            collection_time=datetime.now(),
            tables=[table],
        )

        # Verify complete structure
        assert len(schema.tables) == 1
        assert len(schema.tables[0].columns) == 2
        assert len(schema.tables[0].constraints) == 2
        assert len(schema.tables[0].indexes) == 1

        # Test JSON serialization of complete structure
        json_str = schema.to_json()
        schema_from_json = SchemaInfo.from_json(json_str)

        assert schema_from_json.tables[0].table_name == "users"
        assert len(schema_from_json.tables[0].columns) == 2
        assert schema_from_json.tables[0].columns[0].column_name == "id"
        assert schema_from_json.tables[0].columns[1].column_name == "username"
