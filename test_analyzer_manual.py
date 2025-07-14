#!/usr/bin/env python3
"""Manual test for diff analyzer functionality."""

from datetime import datetime
from src.pgsd.core.analyzer import DiffAnalyzer
from src.pgsd.models.schema import (
    SchemaInfo,
    TableInfo,
    ColumnInfo,
    ConstraintInfo,
)


def create_schema_v1():
    """Create a sample schema version 1."""
    # Users table
    users_columns = [
        ColumnInfo(
            column_name="id",
            ordinal_position=1,
            data_type="integer",
            is_nullable=False,
            column_default="nextval('users_id_seq'::regclass)",
            numeric_precision=32,
            numeric_scale=0,
            udt_name="int4",
            column_comment="Primary key"
        ),
        ColumnInfo(
            column_name="username",
            ordinal_position=2,
            data_type="character varying",
            is_nullable=False,
            character_maximum_length=50,
            udt_name="varchar",
            column_comment="Username"
        ),
        ColumnInfo(
            column_name="email",
            ordinal_position=3,
            data_type="character varying",
            is_nullable=False,
            character_maximum_length=100,
            udt_name="varchar", 
            column_comment="Email address"
        ),
        ColumnInfo(
            column_name="created_at",
            ordinal_position=4,
            data_type="timestamp without time zone",
            is_nullable=False,
            column_default="CURRENT_TIMESTAMP",
            udt_name="timestamp",
            column_comment="Creation timestamp"
        )
    ]

    users_constraints = [
        ConstraintInfo(
            constraint_name="users_pkey",
            table_name="users",
            constraint_type="PRIMARY KEY",
            column_name="id"
        ),
        ConstraintInfo(
            constraint_name="users_username_unique",
            table_name="users",
            constraint_type="UNIQUE",
            column_name="username"
        )
    ]

    users_table = TableInfo(
        table_name="users",
        table_schema="public",
        table_type="BASE TABLE",
        columns=users_columns,
        constraints=users_constraints,
        table_comment="User accounts",
        estimated_rows=1000,
        table_size="48 kB"
    )

    # Posts table
    posts_columns = [
        ColumnInfo(
            column_name="id",
            ordinal_position=1,
            data_type="integer",
            is_nullable=False,
            column_default="nextval('posts_id_seq'::regclass)",
            numeric_precision=32,
            numeric_scale=0,
            udt_name="int4",
            column_comment="Primary key"
        ),
        ColumnInfo(
            column_name="user_id",
            ordinal_position=2,
            data_type="integer",
            is_nullable=False,
            numeric_precision=32,
            numeric_scale=0,
            udt_name="int4",
            column_comment="User reference"
        ),
        ColumnInfo(
            column_name="title",
            ordinal_position=3,
            data_type="character varying",
            is_nullable=False,
            character_maximum_length=255,
            udt_name="varchar",
            column_comment="Post title"
        ),
        ColumnInfo(
            column_name="content",
            ordinal_position=4,
            data_type="text",
            is_nullable=True,
            udt_name="text",
            column_comment="Post content"
        ),
        ColumnInfo(
            column_name="published",
            ordinal_position=5,
            data_type="boolean",
            is_nullable=False,
            column_default="false",
            udt_name="bool",
            column_comment="Publication status"
        ),
        ColumnInfo(
            column_name="created_at",
            ordinal_position=6,
            data_type="timestamp without time zone",
            is_nullable=False,
            column_default="CURRENT_TIMESTAMP",
            udt_name="timestamp",
            column_comment="Creation timestamp"
        )
    ]

    posts_constraints = [
        ConstraintInfo(
            constraint_name="posts_pkey",
            table_name="posts",
            constraint_type="PRIMARY KEY",
            column_name="id"
        ),
        ConstraintInfo(
            constraint_name="posts_user_id_fkey",
            table_name="posts",
            constraint_type="FOREIGN KEY",
            column_name="user_id",
            foreign_table_name="users",
            foreign_column_name="id"
        )
    ]

    posts_table = TableInfo(
        table_name="posts",
        table_schema="public",
        table_type="BASE TABLE",
        columns=posts_columns,
        constraints=posts_constraints,
        table_comment="Blog posts",
        estimated_rows=5000,
        table_size="120 kB"
    )

    return SchemaInfo(
        schema_name="public",
        database_type="source",
        collection_time=datetime(2025, 7, 14, 10, 0, 0),
        tables=[users_table, posts_table]
    )


def create_schema_v2():
    """Create a sample schema version 2 with modifications."""
    # Modified Users table - enhanced with new fields
    users_columns = [
        ColumnInfo(
            column_name="id",
            ordinal_position=1,
            data_type="integer",
            is_nullable=False,
            column_default="nextval('users_id_seq'::regclass)",
            numeric_precision=32,
            numeric_scale=0,
            udt_name="int4",
            column_comment="Primary key"
        ),
        ColumnInfo(
            column_name="username",
            ordinal_position=2,
            data_type="character varying",
            is_nullable=False,
            character_maximum_length=60,  # Increased from 50
            udt_name="varchar",
            column_comment="Username"
        ),
        ColumnInfo(
            column_name="email",
            ordinal_position=3,
            data_type="character varying",
            is_nullable=False,
            character_maximum_length=100,
            udt_name="varchar",
            column_comment="Email address"
        ),
        ColumnInfo(  # NEW COLUMN
            column_name="full_name",
            ordinal_position=4,
            data_type="character varying",
            is_nullable=True,
            character_maximum_length=200,
            udt_name="varchar",
            column_comment="Full name"
        ),
        ColumnInfo(
            column_name="created_at",
            ordinal_position=5,  # Position changed due to new column
            data_type="timestamp without time zone",
            is_nullable=False,
            column_default="CURRENT_TIMESTAMP",
            udt_name="timestamp",
            column_comment="Creation timestamp"
        ),
        ColumnInfo(  # NEW COLUMN
            column_name="updated_at",
            ordinal_position=6,
            data_type="timestamp without time zone",
            is_nullable=True,
            udt_name="timestamp",
            column_comment="Last update timestamp"
        )
    ]

    users_constraints = [
        ConstraintInfo(
            constraint_name="users_pkey",
            table_name="users",
            constraint_type="PRIMARY KEY",
            column_name="id"
        ),
        ConstraintInfo(
            constraint_name="users_username_unique",
            table_name="users",
            constraint_type="UNIQUE",
            column_name="username"
        ),
        ConstraintInfo(  # NEW CONSTRAINT
            constraint_name="users_email_unique",
            table_name="users",
            constraint_type="UNIQUE",
            column_name="email"
        )
    ]

    users_table = TableInfo(
        table_name="users",
        table_schema="public",
        table_type="BASE TABLE",
        columns=users_columns,
        constraints=users_constraints,
        table_comment="User accounts",
        estimated_rows=1500,  # Increased
        table_size="72 kB"  # Increased
    )

    # Modified Posts table
    posts_columns = [
        ColumnInfo(
            column_name="id",
            ordinal_position=1,
            data_type="integer",
            is_nullable=False,
            column_default="nextval('posts_id_seq'::regclass)",
            numeric_precision=32,
            numeric_scale=0,
            udt_name="int4",
            column_comment="Primary key"
        ),
        ColumnInfo(
            column_name="user_id",
            ordinal_position=2,
            data_type="integer",
            is_nullable=False,
            numeric_precision=32,
            numeric_scale=0,
            udt_name="int4",
            column_comment="User reference"
        ),
        ColumnInfo(
            column_name="title",
            ordinal_position=3,
            data_type="character varying",
            is_nullable=False,
            character_maximum_length=255,
            udt_name="varchar",
            column_comment="Post title"
        ),
        ColumnInfo(
            column_name="content",
            ordinal_position=4,
            data_type="text",
            is_nullable=True,
            udt_name="text",
            column_comment="Post content"
        ),
        ColumnInfo(
            column_name="published",
            ordinal_position=5,
            data_type="boolean",
            is_nullable=False,
            column_default="false",
            udt_name="bool",
            column_comment="Publication status"
        ),
        ColumnInfo(  # NEW COLUMN
            column_name="view_count",
            ordinal_position=6,
            data_type="integer",
            is_nullable=False,
            column_default="0",
            numeric_precision=32,
            numeric_scale=0,
            udt_name="int4",
            column_comment="View count"
        ),
        ColumnInfo(
            column_name="created_at",
            ordinal_position=7,  # Position changed
            data_type="timestamp without time zone",
            is_nullable=False,
            column_default="CURRENT_TIMESTAMP",
            udt_name="timestamp",
            column_comment="Creation timestamp"
        )
    ]

    posts_constraints = [
        ConstraintInfo(
            constraint_name="posts_pkey",
            table_name="posts",
            constraint_type="PRIMARY KEY",
            column_name="id"
        ),
        ConstraintInfo(
            constraint_name="posts_user_id_fkey",
            table_name="posts",
            constraint_type="FOREIGN KEY",
            column_name="user_id",
            foreign_table_name="users",
            foreign_column_name="id"
        )
    ]

    posts_table = TableInfo(
        table_name="posts",
        table_schema="public",
        table_type="BASE TABLE",
        columns=posts_columns,
        constraints=posts_constraints,
        table_comment="Blog posts",
        estimated_rows=7500,  # Increased
        table_size="180 kB"  # Increased
    )

    # NEW Comments table
    comments_columns = [
        ColumnInfo(
            column_name="id",
            ordinal_position=1,
            data_type="integer",
            is_nullable=False,
            column_default="nextval('comments_id_seq'::regclass)",
            numeric_precision=32,
            numeric_scale=0,
            udt_name="int4",
            column_comment="Primary key"
        ),
        ColumnInfo(
            column_name="post_id",
            ordinal_position=2,
            data_type="integer",
            is_nullable=False,
            numeric_precision=32,
            numeric_scale=0,
            udt_name="int4",
            column_comment="Post reference"
        ),
        ColumnInfo(
            column_name="user_id",
            ordinal_position=3,
            data_type="integer",
            is_nullable=False,
            numeric_precision=32,
            numeric_scale=0,
            udt_name="int4",
            column_comment="User reference"
        ),
        ColumnInfo(
            column_name="content",
            ordinal_position=4,
            data_type="text",
            is_nullable=False,
            udt_name="text",
            column_comment="Comment content"
        ),
        ColumnInfo(
            column_name="created_at",
            ordinal_position=5,
            data_type="timestamp without time zone",
            is_nullable=False,
            column_default="CURRENT_TIMESTAMP",
            udt_name="timestamp",
            column_comment="Creation timestamp"
        )
    ]

    comments_constraints = [
        ConstraintInfo(
            constraint_name="comments_pkey",
            table_name="comments",
            constraint_type="PRIMARY KEY",
            column_name="id"
        ),
        ConstraintInfo(
            constraint_name="comments_post_id_fkey",
            table_name="comments",
            constraint_type="FOREIGN KEY",
            column_name="post_id",
            foreign_table_name="posts",
            foreign_column_name="id"
        ),
        ConstraintInfo(
            constraint_name="comments_user_id_fkey",
            table_name="comments",
            constraint_type="FOREIGN KEY",
            column_name="user_id",
            foreign_table_name="users",
            foreign_column_name="id"
        )
    ]

    comments_table = TableInfo(
        table_name="comments",
        table_schema="public",
        table_type="BASE TABLE",
        columns=comments_columns,
        constraints=comments_constraints,
        table_comment="Post comments",
        estimated_rows=2000,
        table_size="64 kB"
    )

    return SchemaInfo(
        schema_name="public",
        database_type="target",
        collection_time=datetime(2025, 7, 14, 10, 30, 0),
        tables=[users_table, posts_table, comments_table]
    )


def print_diff_summary(result):
    """Print a summary of differences found."""
    print("=" * 60)
    print("SCHEMA DIFFERENCE ANALYSIS RESULTS")
    print("=" * 60)
    
    # Update summary first
    result.update_summary()
    
    print(f"Total Changes: {result.summary['total_changes']}")
    print()
    
    # Tables
    print("TABLES:")
    print(f"  Added: {len(result.tables['added'])}")
    for table in result.tables["added"]:
        print(f"    + {table.table_name}")
        
    print(f"  Removed: {len(result.tables['removed'])}")
    for table in result.tables["removed"]:
        print(f"    - {table.table_name}")
        
    print(f"  Modified: {len(result.tables['modified'])}")
    for table_diff in result.tables["modified"]:
        print(f"    ~ {table_diff.name}")
    print()
    
    # Columns
    print("COLUMNS:")
    print(f"  Added: {len(result.columns['added'])}")
    for col_info in result.columns["added"]:
        print(f"    + {col_info['table']}.{col_info['column'].column_name}")
        
    print(f"  Removed: {len(result.columns['removed'])}")
    for col_info in result.columns["removed"]:
        print(f"    - {col_info['table']}.{col_info['column'].column_name}")
        
    print(f"  Modified: {len(result.columns['modified'])}")
    for col_info in result.columns["modified"]:
        print(f"    ~ {col_info['table']}.{col_info['column'].column_name}")
        for change_type, change_details in col_info["changes"].items():
            print(f"      {change_type}: {change_details['from']} -> {change_details['to']}")
    print()
    
    # Constraints
    print("CONSTRAINTS:")
    print(f"  Added: {len(result.constraints['added'])}")
    for const_info in result.constraints["added"]:
        print(f"    + {const_info['table']}.{const_info['constraint'].constraint_name}")
        
    print(f"  Removed: {len(result.constraints['removed'])}")
    for const_info in result.constraints["removed"]:
        print(f"    - {const_info['table']}.{const_info['constraint'].constraint_name}")
        
    print(f"  Modified: {len(result.constraints['modified'])}")
    for const_info in result.constraints["modified"]:
        print(f"    ~ {const_info['table']}.{const_info['constraint'].constraint_name}")
    print()


def main():
    """Run the manual test."""
    print("Diff Analyzer Manual Test")
    print("=" * 60)
    
    # Create test schemas
    print("Creating test schemas...")
    schema_v1 = create_schema_v1()
    schema_v2 = create_schema_v2()
    
    print(f"Schema V1: {len(schema_v1.tables)} tables")
    print(f"Schema V2: {len(schema_v2.tables)} tables")
    print()
    
    # Run analysis
    print("Running diff analysis...")
    analyzer = DiffAnalyzer()
    
    import time
    start_time = time.time()
    result = analyzer.analyze(schema_v1, schema_v2)
    end_time = time.time()
    
    print(f"Analysis completed in {end_time - start_time:.3f} seconds")
    print()
    
    # Print results
    print_diff_summary(result)
    
    # Validate expected results
    print("VALIDATION:")
    print("=" * 60)
    
    expected_table_added = 1  # comments table
    expected_table_modified = 2  # users and posts
    expected_column_added = 8  # 3 new columns in existing tables + 5 columns from new comments table
    expected_column_modified = 1  # username character_maximum_length (ordinal position changes filtered out)
    expected_constraint_added = 4  # users_email_unique + 3 comments constraints
    
    print(f"Expected tables added: {expected_table_added}, Actual: {len(result.tables['added'])}")
    print(f"Expected tables modified: {expected_table_modified}, Actual: {len(result.tables['modified'])}")
    print(f"Expected columns added: {expected_column_added}, Actual: {len(result.columns['added'])}")
    print(f"Expected columns modified: {expected_column_modified}, Actual: {len(result.columns['modified'])}")
    print(f"Expected constraints added: {expected_constraint_added}, Actual: {len(result.constraints['added'])}")
    
    # Check if results match expectations
    validation_passed = (
        len(result.tables["added"]) == expected_table_added and
        len(result.tables["modified"]) == expected_table_modified and
        len(result.columns["added"]) == expected_column_added and
        len(result.columns["modified"]) == expected_column_modified and
        len(result.constraints["added"]) == expected_constraint_added
    )
    
    print()
    if validation_passed:
        print("✅ VALIDATION PASSED - All results match expectations!")
    else:
        print("❌ VALIDATION FAILED - Results don't match expectations")
    
    print("=" * 60)
    return validation_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)