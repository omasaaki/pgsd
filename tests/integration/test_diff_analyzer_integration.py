"""Integration tests for diff analyzer with real schema data."""

import pytest
from datetime import datetime

from src.pgsd.core.analyzer import DiffAnalyzer
from src.pgsd.models.schema import (
    SchemaInfo,
    TableInfo,
    ColumnInfo,
    ConstraintInfo,
)


class TestDiffAnalyzerIntegration:
    """Integration tests for DiffAnalyzer using realistic schema scenarios."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return DiffAnalyzer()

    @pytest.fixture
    def sample_schema_v1(self):
        """Create a realistic schema representing version 1."""
        # Users table
        users_columns = [
            ColumnInfo(
                column_name="id",
                data_type="integer",
                is_nullable=False,
                column_default="nextval('users_id_seq'::regclass)",
                character_maximum_length=None,
                numeric_precision=32,
                numeric_scale=0,
                ordinal_position=1,
                udt_name="int4",
                column_comment="Primary key",
            ),
            ColumnInfo(
                column_name="username",
                data_type="character varying",
                is_nullable=False,
                column_default=None,
                character_maximum_length=50,
                numeric_precision=None,
                numeric_scale=None,
                ordinal_position=2,
                udt_name="varchar",
                column_comment="Username",
            ),
            ColumnInfo(
                column_name="email",
                data_type="character varying",
                is_nullable=False,
                column_default=None,
                character_maximum_length=100,
                numeric_precision=None,
                numeric_scale=None,
                ordinal_position=3,
                udt_name="varchar",
                column_comment="Email address",
            ),
            ColumnInfo(
                column_name="created_at",
                data_type="timestamp without time zone",
                is_nullable=False,
                column_default="CURRENT_TIMESTAMP",
                character_maximum_length=None,
                numeric_precision=None,
                numeric_scale=None,
                ordinal_position=4,
                udt_name="timestamp",
                column_comment="Creation timestamp",
            ),
        ]

        users_constraints = [
            ConstraintInfo(
                constraint_name="users_pkey",
                constraint_type="PRIMARY KEY",
                table_name="users",
                column_name="id",
            ),
            ConstraintInfo(
                constraint_name="users_username_unique",
                constraint_type="UNIQUE",
                table_name="users",
                column_name="username",
            ),
        ]

        users_table = TableInfo(
            table_name="users",
            table_schema="public",
            table_type="BASE TABLE",
            columns=users_columns,
            constraints=users_constraints,
            table_comment="User accounts",
            estimated_rows=1000,
            table_size="48 kB",
        )

        return SchemaInfo(
            schema_name="public",
            database_type="source",
            collection_time=datetime(2025, 7, 14, 10, 0, 0),
            tables=[users_table],
        )

    @pytest.fixture
    def sample_schema_v2(self):
        """Create a realistic schema representing version 2 with modifications."""
        # Modified Users table - enhanced with new fields
        users_columns = [
            ColumnInfo(
                column_name="id",
                data_type="integer",
                is_nullable=False,
                column_default="nextval('users_id_seq'::regclass)",
                character_maximum_length=None,
                numeric_precision=32,
                numeric_scale=0,
                ordinal_position=1,
                udt_name="int4",
                column_comment="Primary key",
            ),
            ColumnInfo(
                column_name="username",
                data_type="character varying",
                is_nullable=False,
                column_default=None,
                character_maximum_length=60,  # Increased from 50
                numeric_precision=None,
                numeric_scale=None,
                ordinal_position=2,
                udt_name="varchar",
                column_comment="Username",
            ),
            ColumnInfo(
                column_name="email",
                data_type="character varying",
                is_nullable=False,
                column_default=None,
                character_maximum_length=100,
                numeric_precision=None,
                numeric_scale=None,
                ordinal_position=3,
                udt_name="varchar",
                column_comment="Email address",
            ),
            ColumnInfo(
                column_name="full_name",  # NEW COLUMN
                data_type="character varying",
                is_nullable=True,
                column_default=None,
                character_maximum_length=200,
                numeric_precision=None,
                numeric_scale=None,
                ordinal_position=4,
                udt_name="varchar",
                column_comment="Full name",
            ),
            ColumnInfo(
                column_name="created_at",
                data_type="timestamp without time zone",
                is_nullable=False,
                column_default="CURRENT_TIMESTAMP",
                character_maximum_length=None,
                numeric_precision=None,
                numeric_scale=None,
                ordinal_position=5,  # Position changed due to new column
                udt_name="timestamp",
                column_comment="Creation timestamp",
            ),
            ColumnInfo(
                column_name="updated_at",  # NEW COLUMN
                data_type="timestamp without time zone",
                is_nullable=True,
                column_default=None,
                character_maximum_length=None,
                numeric_precision=None,
                numeric_scale=None,
                ordinal_position=6,
                udt_name="timestamp",
                column_comment="Last update timestamp",
            ),
        ]

        users_constraints = [
            ConstraintInfo(
                constraint_name="users_pkey",
                constraint_type="PRIMARY KEY",
                table_name="users",
                column_name="id",
            ),
            ConstraintInfo(
                constraint_name="users_username_unique",
                constraint_type="UNIQUE",
                table_name="users",
                column_name="username",
            ),
            ConstraintInfo(
                constraint_name="users_email_unique",  # NEW CONSTRAINT
                constraint_type="UNIQUE",
                table_name="users",
                column_name="email",
            ),
        ]

        users_table = TableInfo(
            table_name="users",
            table_schema="public",
            table_type="BASE TABLE",
            columns=users_columns,
            constraints=users_constraints,
            table_comment="User accounts",
            estimated_rows=1500,  # Increased
            table_size="72 kB",  # Increased
        )

        # NEW Comments table
        comments_columns = [
            ColumnInfo(
                column_name="id",
                data_type="integer",
                is_nullable=False,
                column_default="nextval('comments_id_seq'::regclass)",
                character_maximum_length=None,
                numeric_precision=32,
                numeric_scale=0,
                ordinal_position=1,
                udt_name="int4",
                column_comment="Primary key",
            ),
            ColumnInfo(
                column_name="user_id",
                data_type="integer",
                is_nullable=False,
                column_default=None,
                character_maximum_length=None,
                numeric_precision=32,
                numeric_scale=0,
                ordinal_position=2,
                udt_name="int4",
                column_comment="User reference",
            ),
            ColumnInfo(
                column_name="content",
                data_type="text",
                is_nullable=False,
                column_default=None,
                character_maximum_length=None,
                numeric_precision=None,
                numeric_scale=None,
                ordinal_position=3,
                udt_name="text",
                column_comment="Comment content",
            ),
        ]

        comments_constraints = [
            ConstraintInfo(
                constraint_name="comments_pkey",
                constraint_type="PRIMARY KEY",
                table_name="comments",
                column_name="id",
            ),
            ConstraintInfo(
                constraint_name="comments_user_id_fkey",
                constraint_type="FOREIGN KEY",
                table_name="comments",
                column_name="user_id",
                foreign_table_name="users",
                foreign_column_name="id",
            ),
        ]

        comments_table = TableInfo(
            table_name="comments",
            table_schema="public",
            table_type="BASE TABLE",
            columns=comments_columns,
            constraints=comments_constraints,
            table_comment="Post comments",
            estimated_rows=500,
            table_size="32 kB",
        )

        return SchemaInfo(
            schema_name="public",
            database_type="target",
            collection_time=datetime(2025, 7, 14, 10, 30, 0),
            tables=[users_table, comments_table],
        )

    def test_realistic_schema_evolution(
        self, analyzer, sample_schema_v1, sample_schema_v2
    ):
        """Test realistic schema evolution scenario."""
        result = analyzer.analyze(sample_schema_v1, sample_schema_v2)

        # Verify basic structure
        assert len(result.tables["added"]) == 1  # comments table
        assert len(result.tables["removed"]) == 0
        assert len(result.tables["modified"]) == 1  # users table

        # Verify added table
        added_table = result.tables["added"][0]
        assert added_table.table_name == "comments"

        # Verify modified table
        modified_table = result.tables["modified"][0]
        assert modified_table.name == "users"

        # Verify column changes
        assert len(result.columns["added"]) > 0  # New columns added
        assert len(result.columns["modified"]) > 0  # Columns modified

        # Verify constraint changes
        assert len(result.constraints["added"]) > 0  # New constraints

        # Verify summary
        result.update_summary()
        assert result.summary["total_changes"] > 0

    def test_performance_medium_schema(self, analyzer):
        """Test performance with medium-sized schemas."""
        import time

        # Create medium schemas (10 tables, 5 columns each)
        tables = []
        for i in range(10):
            columns = []
            for j in range(5):
                columns.append(
                    ColumnInfo(
                        column_name=f"col_{j}",
                        data_type="integer",
                        is_nullable=False,
                        ordinal_position=j + 1,
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

        schema_a = SchemaInfo(
            schema_name="public",
            database_type="source",
            collection_time=datetime(2025, 7, 14, 10, 0, 0),
            tables=tables,
        )

        schema_b = SchemaInfo(
            schema_name="public",
            database_type="target",
            collection_time=datetime(2025, 7, 14, 10, 0, 0),
            tables=tables,  # Identical
        )

        start_time = time.time()
        result = analyzer.analyze(schema_a, schema_b)
        end_time = time.time()

        execution_time = end_time - start_time

        # Should complete reasonably quickly
        assert execution_time < 1.0

        # Verify analysis was completed
        assert result.summary["total_changes"] == 0

    def test_edge_case_empty_schemas(self, analyzer):
        """Test edge case with empty schemas."""
        empty_schema_a = SchemaInfo(
            schema_name="public",
            database_type="source",
            collection_time=datetime(2025, 7, 14, 10, 0, 0),
            tables=[],
        )

        empty_schema_b = SchemaInfo(
            schema_name="public",
            database_type="target",
            collection_time=datetime(2025, 7, 14, 10, 0, 0),
            tables=[],
        )

        result = analyzer.analyze(empty_schema_a, empty_schema_b)

        assert len(result.tables["added"]) == 0
        assert len(result.tables["removed"]) == 0
        assert len(result.tables["modified"]) == 0
        assert result.summary["total_changes"] == 0
