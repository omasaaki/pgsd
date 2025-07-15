"""
Unit tests for database exception classes.
"""

import pytest
from unittest.mock import Mock
import psycopg2

from pgsd.exceptions.base import ErrorSeverity, ErrorCategory
from pgsd.exceptions.database import (
    DatabaseError,
    DatabaseConnectionError,
    SchemaNotFoundError,
    InsufficientPrivilegesError,
    QueryExecutionError,
)


@pytest.mark.unit
class TestDatabaseError:
    """Test DatabaseError base class."""

    def test_database_error_defaults(self):
        """Test DatabaseError default values."""
        error = DatabaseError("Database error")

        assert error.error_code == "DATABASE_ERROR"
        assert error.severity == ErrorSeverity.HIGH
        assert error.category == ErrorCategory.CONNECTION
        assert error.get_exit_code() == 10
        assert error.is_retriable() is True
        assert error.base_retry_delay == 2.0
        assert error.max_retry_delay == 30.0


@pytest.mark.unit
class TestDatabaseConnectionError:
    """Test DatabaseConnectionError class."""

    def test_basic_connection_error(self):
        """Test basic database connection error creation."""
        error = DatabaseConnectionError(host="localhost", port=5432, database="testdb")

        assert "localhost:5432" in str(error)
        assert "testdb" in str(error)
        assert error.error_code == "DB_CONNECTION_FAILED"
        assert error.severity == ErrorSeverity.CRITICAL
        assert error.get_exit_code() == 11
        assert error.is_retriable() is True

        # Check technical details
        assert error.technical_details["host"] == "localhost"
        assert error.technical_details["port"] == 5432
        assert error.technical_details["database"] == "testdb"
        assert error.technical_details["connection_type"] == "postgresql"
        assert error.technical_details["user"] is None

        # Check recovery suggestions
        assert len(error.recovery_suggestions) > 0
        assert any(
            "PostgreSQL server is running" in suggestion
            for suggestion in error.recovery_suggestions
        )

    def test_connection_error_with_user(self):
        """Test connection error with user information."""
        error = DatabaseConnectionError(
            host="db.example.com", port=5433, database="myapp", user="appuser"
        )

        assert "db.example.com:5433" in str(error)
        assert "myapp" in str(error)
        assert "appuser" in str(error)
        assert error.technical_details["user"] == "appuser"

    def test_connection_error_with_original_error(self):
        """Test connection error with original exception."""
        original = ConnectionError("Network unreachable")

        error = DatabaseConnectionError(
            host="localhost", port=5432, database="testdb", original_error=original
        )

        assert error.original_error == original
        assert error.technical_details["original_error_type"] == "ConnectionError"
        assert (
            error.technical_details["original_error_message"] == "Network unreachable"
        )

    def test_from_psycopg2_error(self):
        """Test creation from psycopg2 error."""
        # Mock psycopg2 OperationalError
        pg_error = Mock(spec=psycopg2.OperationalError)
        pg_error.pgcode = "08006"  # connection_failure
        pg_error.pgerror = "could not connect to server"

        error = DatabaseConnectionError.from_psycopg2_error(
            pg_error, host="localhost", port=5432, database="testdb", user="testuser"
        )

        assert isinstance(error, DatabaseConnectionError)
        assert error.original_error == pg_error
        assert error.technical_details["postgres_error_code"] == "08006"
        assert (
            error.technical_details["postgres_error_message"]
            == "could not connect to server"
        )
        assert error.technical_details["host"] == "localhost"
        assert error.technical_details["user"] == "testuser"

    def test_from_psycopg2_error_without_pgcode(self):
        """Test handling psycopg2 error without pgcode."""
        pg_error = Mock(spec=psycopg2.OperationalError)
        # Explicitly delete pgcode and pgerror attributes if they exist
        if hasattr(pg_error, "pgcode"):
            delattr(pg_error, "pgcode")
        if hasattr(pg_error, "pgerror"):
            delattr(pg_error, "pgerror")

        error = DatabaseConnectionError.from_psycopg2_error(
            pg_error, host="localhost", port=5432, database="testdb"
        )

        assert isinstance(error, DatabaseConnectionError)
        assert error.original_error == pg_error
        # Should not have postgres-specific details
        assert "postgres_error_code" not in error.technical_details
        assert "postgres_error_message" not in error.technical_details


@pytest.mark.unit
class TestSchemaNotFoundError:
    """Test SchemaNotFoundError class."""

    def test_basic_schema_not_found(self):
        """Test basic schema not found error."""
        error = SchemaNotFoundError(schema_name="test_schema", database="testdb")

        assert "test_schema" in str(error)
        assert "testdb" in str(error)
        assert error.error_code == "SCHEMA_NOT_FOUND"
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.get_exit_code() == 12
        assert error.is_retriable() is False

        # Check technical details
        assert error.technical_details["schema_name"] == "test_schema"
        assert error.technical_details["database"] == "testdb"
        assert error.technical_details["available_schemas"] == []

        # Check recovery suggestions
        assert len(error.recovery_suggestions) > 0
        assert any(
            "test_schema" in suggestion for suggestion in error.recovery_suggestions
        )

    def test_schema_not_found_with_available_schemas(self):
        """Test schema not found with list of available schemas."""
        available_schemas = ["public", "information_schema", "pg_catalog"]

        error = SchemaNotFoundError(
            schema_name="missing_schema",
            database="testdb",
            available_schemas=available_schemas,
        )

        assert error.technical_details["available_schemas"] == available_schemas

        # Should include available schemas in recovery suggestions
        assert any(
            "public, information_schema, pg_catalog" in suggestion
            for suggestion in error.recovery_suggestions
        )

    def test_schema_not_found_empty_available_list(self):
        """Test schema not found with empty available schemas list."""
        error = SchemaNotFoundError(
            schema_name="test_schema", database="testdb", available_schemas=[]
        )

        assert error.technical_details["available_schemas"] == []
        # Should not include empty available schemas suggestion
        assert not any(
            "Available schemas:" in suggestion
            for suggestion in error.recovery_suggestions
        )


@pytest.mark.unit
class TestInsufficientPrivilegesError:
    """Test InsufficientPrivilegesError class."""

    def test_basic_privileges_error(self):
        """Test basic insufficient privileges error."""
        error = InsufficientPrivilegesError(
            operation="read schema", required_privileges=["USAGE", "SELECT"]
        )

        assert "read schema" in str(error)
        assert error.error_code == "INSUFFICIENT_PRIVILEGES"
        assert error.severity == ErrorSeverity.HIGH
        assert error.category == ErrorCategory.AUTHORIZATION
        assert error.get_exit_code() == 13
        assert error.is_retriable() is False

        # Check technical details
        assert error.technical_details["operation"] == "read schema"
        assert error.technical_details["required_privileges"] == ["USAGE", "SELECT"]
        assert error.technical_details["user"] is None
        assert error.technical_details["object_name"] is None

        # Check recovery suggestions
        assert len(error.recovery_suggestions) > 0
        assert any(
            "USAGE, SELECT" in suggestion for suggestion in error.recovery_suggestions
        )

    def test_privileges_error_with_user_and_object(self):
        """Test privileges error with user and object information."""
        error = InsufficientPrivilegesError(
            operation="execute function",
            required_privileges=["EXECUTE"],
            user="appuser",
            object_name="my_function()",
        )

        assert "execute function" in str(error)
        assert "my_function()" in str(error)
        assert "appuser" in str(error)

        assert error.technical_details["user"] == "appuser"
        assert error.technical_details["object_name"] == "my_function()"
        assert error.technical_details["required_privileges"] == ["EXECUTE"]

    def test_privileges_error_single_privilege(self):
        """Test privileges error with single required privilege."""
        error = InsufficientPrivilegesError(
            operation="create table", required_privileges=["CREATE"]
        )

        # Should handle single privilege correctly
        assert any("CREATE" in suggestion for suggestion in error.recovery_suggestions)


@pytest.mark.unit
class TestQueryExecutionError:
    """Test QueryExecutionError class."""

    def test_basic_query_error(self):
        """Test basic query execution error."""
        query = "SELECT * FROM non_existent_table"
        error_message = 'relation "non_existent_table" does not exist'

        error = QueryExecutionError(query=query, error_message=error_message)

        assert error_message in str(error)
        assert error.error_code == "QUERY_EXECUTION_FAILED"
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.get_exit_code() == 14
        assert error.is_retriable() is True

        # Check technical details
        assert error.technical_details["query"] == query
        assert error.technical_details["error_message"] == error_message
        assert error.technical_details["postgres_error_code"] is None

        # Check recovery suggestions
        assert len(error.recovery_suggestions) > 0
        assert any(
            "SQL query syntax" in suggestion
            for suggestion in error.recovery_suggestions
        )

    def test_query_error_with_postgres_code(self):
        """Test query error with PostgreSQL error code."""
        query = "INSERT INTO table VALUES (1, 'duplicate')"
        error_message = "duplicate key value violates unique constraint"
        postgres_code = "23505"

        error = QueryExecutionError(
            query=query, error_message=error_message, postgres_error_code=postgres_code
        )

        assert error.technical_details["postgres_error_code"] == postgres_code

    def test_query_error_with_original_error(self):
        """Test query error with original exception."""
        original = psycopg2.ProgrammingError("syntax error")
        query = "SELCT * FROM table"  # Intentional typo
        error_message = 'syntax error at or near "SELCT"'

        error = QueryExecutionError(
            query=query, error_message=error_message, original_error=original
        )

        assert error.original_error == original

    def test_long_query_truncation(self):
        """Test that very long queries are truncated in technical details."""
        long_query = "SELECT * FROM table WHERE " + "x = 1 AND " * 100 + "y = 2"
        error_message = "Some error"

        error = QueryExecutionError(query=long_query, error_message=error_message)

        stored_query = error.technical_details["query"]
        assert len(stored_query) <= 503  # 500 + "..."
        assert stored_query.endswith("...")

    def test_short_query_not_truncated(self):
        """Test that short queries are not truncated."""
        short_query = "SELECT 1"
        error_message = "Some error"

        error = QueryExecutionError(query=short_query, error_message=error_message)

        stored_query = error.technical_details["query"]
        assert stored_query == short_query
        assert not stored_query.endswith("...")


@pytest.mark.unit
class TestDatabaseErrorIntegration:
    """Test integration scenarios for database errors."""

    def test_error_hierarchy(self):
        """Test that all database errors inherit correctly."""
        connection_error = DatabaseConnectionError("localhost", 5432, "testdb")
        schema_error = SchemaNotFoundError("test_schema", "testdb")
        privileges_error = InsufficientPrivilegesError("read", ["SELECT"])
        query_error = QueryExecutionError("SELECT 1", "error")

        # All should be instances of DatabaseError
        assert isinstance(connection_error, DatabaseError)
        assert isinstance(schema_error, DatabaseError)
        assert isinstance(privileges_error, DatabaseError)
        assert isinstance(query_error, DatabaseError)

        # All should have different exit codes
        exit_codes = {
            connection_error.get_exit_code(),
            schema_error.get_exit_code(),
            privileges_error.get_exit_code(),
            query_error.get_exit_code(),
        }
        assert len(exit_codes) == 4  # All different

    def test_retriable_vs_non_retriable(self):
        """Test retriable vs non-retriable database errors."""
        # Retriable errors
        connection_error = DatabaseConnectionError("localhost", 5432, "testdb")
        query_error = QueryExecutionError("SELECT 1", "timeout")

        # Non-retriable errors
        schema_error = SchemaNotFoundError("missing", "testdb")
        privileges_error = InsufficientPrivilegesError("read", ["SELECT"])

        assert connection_error.is_retriable() is True
        assert query_error.is_retriable() is True
        assert schema_error.is_retriable() is False
        assert privileges_error.is_retriable() is False

    def test_serialization_compatibility(self):
        """Test that all database errors can be serialized."""
        errors = [
            DatabaseConnectionError("localhost", 5432, "testdb", "user"),
            SchemaNotFoundError("schema", "db", ["available"]),
            InsufficientPrivilegesError("op", ["priv"], "user", "object"),
            QueryExecutionError("query", "error", "code"),
        ]

        for error in errors:
            # Should be able to serialize to dict
            error_dict = error.to_dict()
            assert isinstance(error_dict, dict)
            assert "error_type" in error_dict
            assert "error_code" in error_dict

            # Should be able to serialize to JSON
            json_str = error.to_json()
            assert isinstance(json_str, str)
            assert len(json_str) > 0

    def test_context_and_suggestions_management(self):
        """Test context and recovery suggestions management."""
        error = DatabaseConnectionError("localhost", 5432, "testdb")

        # Add context
        error.add_context("retry_attempt", 1)
        error.add_context("connection_timeout", 30)

        # Add custom recovery suggestion
        error.add_recovery_suggestion("Check firewall settings")

        assert error.context["retry_attempt"] == 1
        assert error.context["connection_timeout"] == 30
        assert "Check firewall settings" in error.recovery_suggestions

        # Should maintain original suggestions
        original_suggestion_count = len(
            DatabaseConnectionError("localhost", 5432, "testdb").recovery_suggestions
        )
        assert len(error.recovery_suggestions) == original_suggestion_count + 1


@pytest.mark.unit
class TestDatabaseErrorEdgeCases:
    """Test edge cases for database errors."""

    def test_connection_error_with_zero_port(self):
        """Test connection error with zero port."""
        error = DatabaseConnectionError("localhost", 0, "testdb")

        assert "localhost:0" in str(error)
        assert error.technical_details["port"] == 0

    def test_connection_error_with_high_port(self):
        """Test connection error with high port number."""
        error = DatabaseConnectionError("localhost", 65535, "testdb")

        assert "localhost:65535" in str(error)
        assert error.technical_details["port"] == 65535

    def test_schema_error_with_special_characters(self):
        """Test schema error with special characters in names."""
        error = SchemaNotFoundError(schema_name="test-schema_123", database="test.db")

        assert "test-schema_123" in str(error)
        assert "test.db" in str(error)

    def test_privileges_error_with_empty_privileges(self):
        """Test privileges error with empty privileges list."""
        error = InsufficientPrivilegesError(
            operation="test operation", required_privileges=[]
        )

        assert error.technical_details["required_privileges"] == []
        # Should still have recovery suggestions
        assert len(error.recovery_suggestions) > 0

    def test_query_error_with_empty_query(self):
        """Test query error with empty query string."""
        error = QueryExecutionError(query="", error_message="Empty query")

        assert error.technical_details["query"] == ""
        assert "Empty query" in str(error)
