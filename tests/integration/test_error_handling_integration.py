"""
Integration tests for error handling system.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch
import psycopg2

from pgsd.exceptions.base import ErrorSeverity, ErrorCategory
from pgsd.exceptions.database import (
    DatabaseConnectionError,
    SchemaNotFoundError,
    QueryExecutionError,
)
from pgsd.exceptions.config import (
    MissingConfigurationError,
)
from pgsd.error_handling.retry import retry_on_error


@pytest.mark.integration
class TestErrorHandlingWorkflow:
    """Test complete error handling workflows."""

    def test_database_connection_error_workflow(self):
        """Test complete database connection error handling workflow."""
        # Simulate database connection failure
        with patch("psycopg2.connect") as mock_connect:
            # Create a mock psycopg2 error with required attributes
            pg_error = Mock(spec=psycopg2.OperationalError)
            pg_error.args = ("could not connect to server",)
            pg_error.pgcode = "08006"
            pg_error.pgerror = "Connection refused"
            mock_connect.side_effect = pg_error

            # Create error from psycopg2 exception
            error = DatabaseConnectionError.from_psycopg2_error(
                pg_error,
                host="localhost",
                port=5432,
                database="testdb",
                user="testuser",
            )

            # Verify error structure
            assert isinstance(error, DatabaseConnectionError)
            assert error.is_retriable()
            assert error.severity == ErrorSeverity.CRITICAL
            assert error.category == ErrorCategory.CONNECTION

            # Verify technical details
            assert error.technical_details["postgres_error_code"] == "08006"
            assert error.technical_details["host"] == "localhost"
            assert error.technical_details["port"] == 5432

            # Verify recovery suggestions
            assert len(error.recovery_suggestions) > 0
            assert any(
                "PostgreSQL server is running" in suggestion
                for suggestion in error.recovery_suggestions
            )

            # Test serialization
            error_dict = error.to_dict()
            assert error_dict["error_code"] == "DB_CONNECTION_FAILED"
            assert error_dict["severity"] == "critical"

            json_str = error.to_json()
            parsed = json.loads(json_str)
            assert parsed["error_code"] == "DB_CONNECTION_FAILED"

    def test_schema_analysis_error_workflow(self):
        """Test schema analysis error handling workflow."""
        # Simulate schema not found scenario
        error = SchemaNotFoundError(
            schema_name="nonexistent_schema",
            database="testdb",
            available_schemas=["public", "information_schema", "pg_catalog"],
        )

        # Add context from analysis process
        error.add_context("analysis_step", "schema_discovery")
        error.add_context("user_input", "nonexistent_schema")
        error.add_context("connection_successful", True)

        # Verify error properties
        assert not error.is_retriable()  # Schema errors are not retriable
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.get_exit_code() == 12

        # Verify context was added
        assert error.context["analysis_step"] == "schema_discovery"
        assert error.context["user_input"] == "nonexistent_schema"

        # Verify available schemas in recovery suggestions
        suggestions_text = " ".join(error.recovery_suggestions)
        assert "public, information_schema, pg_catalog" in suggestions_text

    def test_configuration_error_workflow(self):
        """Test configuration error handling workflow."""
        # Simulate missing configuration
        missing_keys = ["database.host", "database.port", "database.name"]
        config_file = Path("/tmp/nonexistent_config.yaml")

        error = MissingConfigurationError(
            missing_keys=missing_keys,
            config_file=config_file,
            config_section="database",
        )

        # Add context
        error.add_context("config_source", "command_line_argument")
        error.add_context("attempted_paths", [str(config_file)])

        # Verify error properties
        assert not error.is_retriable()
        assert error.severity == ErrorSeverity.HIGH
        assert error.category == ErrorCategory.CONFIGURATION
        assert error.get_exit_code() == 22

        # Verify all missing keys are mentioned
        error_message = str(error)
        for key in missing_keys:
            assert key in error_message

        # Verify technical details
        assert error.technical_details["missing_keys"] == missing_keys
        assert error.technical_details["config_section"] == "database"

    @patch("time.sleep")
    def test_retry_integration_with_database_errors(self, mock_sleep):
        """Test retry mechanism integration with database errors."""
        call_count = 0

        @retry_on_error(
            max_attempts=3,
            base_delay=0.01,
            retriable_exceptions=(DatabaseConnectionError,),
        )
        def simulate_database_operation():
            nonlocal call_count
            call_count += 1

            if call_count <= 2:
                # First two attempts fail
                raise DatabaseConnectionError(
                    host="localhost",
                    port=5432,
                    database="testdb",
                    original_error=psycopg2.OperationalError("connection timeout"),
                )
            else:
                # Third attempt succeeds
                return {"status": "connected", "schema_count": 5}

        # Execute the function
        result = simulate_database_operation()

        # Verify retry behavior
        assert call_count == 3
        assert result["status"] == "connected"
        assert mock_sleep.call_count == 2  # Two retries

    def test_error_context_propagation(self):
        """Test error context propagation through error handling chain."""
        # Create initial error
        original_error = psycopg2.OperationalError("network error")

        # Create database error with context
        db_error = DatabaseConnectionError(
            host="db.example.com",
            port=5432,
            database="production_db",
            user="app_user",
            original_error=original_error,
        )

        # Add operation context
        db_error.add_context("operation", "schema_comparison")
        db_error.add_context("comparison_id", "comp_123")
        db_error.add_context("source_schema", "public")
        db_error.add_context("target_schema", "staging")

        # Add retry context
        db_error.add_context("retry_attempt", 1)
        db_error.add_context("total_attempts", 3)

        # Verify context is preserved in serialization
        error_dict = db_error.to_dict()

        assert error_dict["context"]["operation"] == "schema_comparison"
        assert error_dict["context"]["comparison_id"] == "comp_123"
        assert error_dict["context"]["source_schema"] == "public"
        assert error_dict["context"]["target_schema"] == "staging"
        assert error_dict["context"]["retry_attempt"] == 1

        # Verify original error information is preserved
        assert error_dict["original_error"] == "network error"
        assert (
            error_dict["technical_details"]["original_error_type"] == "OperationalError"
        )

    def test_error_recovery_suggestions_aggregation(self):
        """Test aggregation of recovery suggestions from multiple sources."""
        error = DatabaseConnectionError("localhost", 5432, "testdb")

        # Add custom recovery suggestions based on context
        error.add_context("previous_failures", ["timeout", "auth_failed"])
        error.add_recovery_suggestion("Check if database is in maintenance mode")
        error.add_recovery_suggestion("Verify network connectivity with ping")
        error.add_recovery_suggestion("Try connecting with different credentials")

        # Verify all suggestions are present
        all_suggestions = error.recovery_suggestions

        # Should have original suggestions plus custom ones
        assert len(all_suggestions) >= 6  # Original + 3 custom
        assert "Check if database is in maintenance mode" in all_suggestions
        assert "Verify network connectivity with ping" in all_suggestions
        assert "Try connecting with different credentials" in all_suggestions

        # Should not have duplicates
        assert len(all_suggestions) == len(set(all_suggestions))

    def test_error_serialization_with_complex_data(self):
        """Test error serialization with complex technical details."""
        # Create error with complex technical details
        error = QueryExecutionError(
            query="SELECT * FROM complex_view WHERE conditions = complex",
            error_message="Complex query failed",
        )

        # Add complex technical details
        error.technical_details.update(
            {
                "query_plan": {
                    "nodes": [
                        {"type": "SeqScan", "relation": "table1", "cost": 100.0},
                        {"type": "HashJoin", "inner": "table2", "cost": 200.0},
                    ]
                },
                "execution_stats": {
                    "rows_examined": 1000000,
                    "execution_time_ms": 5000,
                    "memory_used_mb": 128,
                },
                "connection_info": {
                    "host": "localhost",
                    "port": 5432,
                    "ssl": True,
                    "protocol_version": 3,
                },
            }
        )

        # Add context with various data types
        error.add_context("timestamp", "2025-07-14T10:30:00Z")
        error.add_context("user_id", 12345)
        error.add_context("session_active", True)
        error.add_context("query_params", ["param1", "param2", None])

        # Test serialization
        error_dict = error.to_dict()

        # Verify complex data is preserved
        assert (
            error_dict["technical_details"]["query_plan"]["nodes"][0]["type"]
            == "SeqScan"
        )
        assert (
            error_dict["technical_details"]["execution_stats"]["rows_examined"]
            == 1000000
        )
        assert error_dict["context"]["user_id"] == 12345
        assert error_dict["context"]["session_active"] is True

        # Test JSON serialization
        json_str = error.to_json()
        parsed = json.loads(json_str)

        # Verify JSON roundtrip preserves data
        assert (
            parsed["technical_details"]["execution_stats"]["execution_time_ms"] == 5000
        )
        assert parsed["context"]["query_params"] == ["param1", "param2", None]


@pytest.mark.integration
class TestErrorHandlingWithExternalSystems:
    """Test error handling integration with external systems."""

    def test_error_handling_with_file_operations(self):
        """Test error handling with file system operations."""
        # Test configuration file not found
        nonexistent_file = Path("/tmp/nonexistent_config.yaml")

        try:
            with open(nonexistent_file, "r") as f:
                content = f.read()
        except FileNotFoundError as e:
            # Convert to PGSD error
            config_error = MissingConfigurationError(
                missing_keys=["config_file"], config_file=nonexistent_file
            )
            config_error.original_error = e
            config_error.add_context("operation", "load_configuration")
            config_error.add_context("attempted_path", str(nonexistent_file))

            # Verify error handling
            assert config_error.error_code == "MISSING_CONFIGURATION"
            assert config_error.original_error == e
            assert "config_file" in str(config_error)
            # Check that the context contains the file path
            assert "attempted_path" in config_error.context
            assert config_error.context["attempted_path"] == str(nonexistent_file)

    def test_error_handling_with_network_operations(self):
        """Test error handling with network operations."""
        with patch("psycopg2.connect") as mock_connect:
            # Simulate network timeout
            mock_connect.side_effect = psycopg2.OperationalError("timeout expired")

            try:
                # Simulate connection attempt
                raise psycopg2.OperationalError("timeout expired")
            except psycopg2.OperationalError as e:
                # Convert to PGSD error
                network_error = DatabaseConnectionError.from_psycopg2_error(
                    e, "remote.db.com", 5432, "production"
                )

                network_error.add_context("network_condition", "high_latency")
                network_error.add_context("connection_pool", "exhausted")

                # Verify network-specific context
                assert network_error.context["network_condition"] == "high_latency"
                assert (
                    network_error.is_retriable()
                )  # Network errors should be retriable

    def test_error_logging_integration(self):
        """Test error handling integration with logging system."""
        with patch("pgsd.utils.logger.get_logger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            # Create error with logging context
            error = DatabaseConnectionError("localhost", 5432, "testdb")
            error.add_context("log_level", "ERROR")
            error.add_context("correlation_id", "req_12345")

            # Simulate error logging (this would be done by error handler)
            error_dict = error.to_dict()

            # Verify logging-relevant information is available
            assert error_dict["id"]  # Unique error ID for correlation
            assert error_dict["timestamp"]  # Timestamp for log ordering
            assert error_dict["context"]["correlation_id"] == "req_12345"
            assert error_dict["severity"] == "critical"


@pytest.mark.integration
class TestErrorHandlingPerformance:
    """Test performance characteristics of error handling system."""

    def test_error_creation_and_serialization_performance(self):
        """Test performance of error creation and serialization."""
        import time

        # Test creating many errors
        start_time = time.time()

        errors = []
        for i in range(100):
            error = DatabaseConnectionError(
                host=f"host{i}.example.com",
                port=5432,
                database=f"db_{i}",
                user=f"user_{i}",
            )
            error.add_context("iteration", i)
            error.add_context("batch_id", "batch_001")
            errors.append(error)

        creation_time = time.time() - start_time

        # Test serializing all errors
        start_time = time.time()

        serialized = [error.to_json() for error in errors]

        serialization_time = time.time() - start_time

        # Performance assertions
        assert creation_time < 1.0  # Should create 100 errors in < 1 second
        assert serialization_time < 1.0  # Should serialize 100 errors in < 1 second
        assert len(serialized) == 100

        # Verify serialization quality
        for json_str in serialized[:5]:  # Check first 5
            parsed = json.loads(json_str)
            assert "error_code" in parsed
            assert "timestamp" in parsed
            assert "context" in parsed

    def test_retry_mechanism_performance(self):
        """Test performance of retry mechanism."""
        import time

        call_count = 0

        @retry_on_error(max_attempts=5, base_delay=0.001)  # Very short delay
        def fast_failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 4:
                raise DatabaseConnectionError("localhost", 5432, "testdb")
            return "success"

        start_time = time.time()
        result = fast_failing_function()
        execution_time = time.time() - start_time

        assert result == "success"
        assert call_count == 4
        # Should complete quickly even with retries
        assert execution_time < 1.0


@pytest.mark.integration
class TestErrorHandlingRealWorldScenarios:
    """Test error handling in realistic scenarios."""

    def test_concurrent_database_operations_error_handling(self):
        """Test error handling with concurrent database operations."""
        import threading
        import queue

        error_queue = queue.Queue()

        def simulate_concurrent_operation(operation_id):
            try:
                # Simulate database operation that might fail
                if operation_id % 3 == 0:  # Every third operation fails
                    raise DatabaseConnectionError(
                        "localhost", 5432, f"db_{operation_id}"
                    )
                return f"success_{operation_id}"
            except Exception as e:
                # Add operation context to error
                if isinstance(e, DatabaseConnectionError):
                    e.add_context("operation_id", operation_id)
                    e.add_context("thread_name", threading.current_thread().name)
                error_queue.put(e)

        # Start multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(
                target=simulate_concurrent_operation, args=(i,), name=f"Operation-{i}"
            )
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Collect errors
        errors = []
        while not error_queue.empty():
            errors.append(error_queue.get())

        # Verify error handling in concurrent environment
        assert len(errors) > 0  # Should have some errors (every 3rd operation)

        for error in errors:
            assert isinstance(error, DatabaseConnectionError)
            assert "operation_id" in error.context
            assert "thread_name" in error.context
            assert error.context["thread_name"].startswith("Operation-")

    def test_error_handling_with_cleanup_operations(self):
        """Test error handling that includes cleanup operations."""
        cleanup_called = False

        def cleanup_operation():
            nonlocal cleanup_called
            cleanup_called = True

        try:
            # Simulate operation that needs cleanup
            error = DatabaseConnectionError("localhost", 5432, "testdb")
            error.add_context("requires_cleanup", True)
            error.add_context(
                "cleanup_operations", ["close_connections", "clear_cache"]
            )

            # In real scenario, this would be in finally block
            cleanup_operation()

            raise error

        except DatabaseConnectionError as e:
            # Verify cleanup context is preserved
            assert e.context["requires_cleanup"] is True
            assert "close_connections" in e.context["cleanup_operations"]
            assert cleanup_called is True

    def test_error_handling_with_user_feedback(self):
        """Test error handling with user-friendly feedback generation."""
        # Simulate user operation that fails
        error = SchemaNotFoundError(
            schema_name="user_provided_schema",
            database="production",
            available_schemas=["public", "app_data", "reporting"],
        )

        # Add user context
        error.add_context("user_input", "user_provided_schema")
        error.add_context("operation_type", "schema_comparison")
        error.add_context("ui_context", "command_line")

        # Generate user-friendly message
        user_message = f"""
Error: {error.message}

What you can do:
"""
        for suggestion in error.recovery_suggestions:
            user_message += f"• {suggestion}\n"

        if error.technical_details.get("available_schemas"):
            user_message += f"\nAvailable schemas: {', '.join(error.technical_details['available_schemas'])}"

        # Verify user message contains helpful information
        assert "user_provided_schema" in user_message
        assert "Available schemas:" in user_message
        assert "public, app_data, reporting" in user_message
        assert len(user_message.split("•")) > 1  # Has bullet points
