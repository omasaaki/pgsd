"""Tests for security utilities."""

import pytest
from src.pgsd.utils.security import mask_password, sanitize_for_logging


class TestMaskPassword:
    """Test cases for mask_password function."""

    def test_mask_password_basic(self):
        """Test basic password masking."""
        conn_str = "host=localhost user=admin password=secret123 dbname=test"
        expected = "host=localhost user=admin password=******** dbname=test"
        
        result = mask_password(conn_str)
        
        assert result == expected

    def test_mask_password_case_insensitive(self):
        """Test case-insensitive password masking."""
        conn_str = "host=localhost user=admin PASSWORD=secret123 dbname=test"
        expected = "host=localhost user=admin PASSWORD=******** dbname=test"
        
        result = mask_password(conn_str)
        
        assert result == expected

    def test_mask_password_custom_mask_char(self):
        """Test password masking with custom mask character."""
        conn_str = "host=localhost user=admin password=secret123 dbname=test"
        expected = "host=localhost user=admin password=######## dbname=test"
        
        result = mask_password(conn_str, mask_char="#")
        
        assert result == expected

    def test_mask_password_url_format(self):
        """Test password masking in URL format."""
        conn_str = "postgresql://user:secret123@localhost:5432/testdb"
        expected = "postgresql://user:********@localhost:5432/testdb"
        
        result = mask_password(conn_str)
        
        assert result == expected

    def test_mask_password_url_format_custom_char(self):
        """Test password masking in URL format with custom character."""
        conn_str = "postgresql://user:secret123@localhost:5432/testdb"
        expected = "postgresql://user:XXXXXXXX@localhost:5432/testdb"
        
        result = mask_password(conn_str, mask_char="X")
        
        assert result == expected

    def test_mask_password_multiple_passwords(self):
        """Test masking multiple password occurrences."""
        conn_str = "password=secret1;password=secret2"
        expected = "password=********;password=********"
        
        result = mask_password(conn_str)
        
        assert result == expected

    def test_mask_password_no_password(self):
        """Test masking when no password is present."""
        conn_str = "host=localhost user=admin dbname=test"
        
        result = mask_password(conn_str)
        
        assert result == conn_str

    def test_mask_password_empty_string(self):
        """Test masking with empty string."""
        result = mask_password("")
        
        assert result == ""

    def test_mask_password_complex_connection_string(self):
        """Test masking with complex connection string."""
        conn_str = (
            "host=localhost port=5432 user=admin password=complex_pass_123 "
            "dbname=test sslmode=require"
        )
        expected = (
            "host=localhost port=5432 user=admin password=******** "
            "dbname=test sslmode=require"
        )
        
        result = mask_password(conn_str)
        
        assert result == expected

    def test_mask_password_with_spaces_in_password(self):
        """Test masking password that contains spaces."""
        conn_str = "host=localhost user=admin password=secret_no_spaces dbname=test"
        expected = "host=localhost user=admin password=******** dbname=test"
        
        result = mask_password(conn_str)
        
        assert result == expected

    def test_mask_password_url_with_port(self):
        """Test masking URL format with port number."""
        conn_str = "postgresql://admin:mypassword@db.example.com:5432/production"
        expected = "postgresql://admin:********@db.example.com:5432/production"
        
        result = mask_password(conn_str)
        
        assert result == expected

    def test_mask_password_url_without_port(self):
        """Test masking URL format without port number."""
        conn_str = "postgresql://admin:mypassword@localhost/testdb"
        expected = "postgresql://admin:********@localhost/testdb"
        
        result = mask_password(conn_str)
        
        assert result == expected

    def test_mask_password_mixed_formats(self):
        """Test masking with mixed connection string formats."""
        conn_str = (
            "postgresql://user:urlpass@localhost/db1; "
            "host=localhost password=keypass dbname=db2"
        )
        expected = (
            "postgresql://user:********@localhost/db1; "
            "host=localhost password=******** dbname=db2"
        )
        
        result = mask_password(conn_str)
        
        assert result == expected

    def test_mask_password_edge_cases(self):
        """Test password masking edge cases."""
        # Password at end of string
        conn_str = "host=localhost user=admin password=endpass"
        expected = "host=localhost user=admin password=********"
        
        result = mask_password(conn_str)
        
        assert result == expected

    def test_mask_password_special_characters(self):
        """Test masking password with special characters."""
        conn_str = "password=p@$$w0rd!123"
        expected = "password=********"
        
        result = mask_password(conn_str)
        
        assert result == expected


class TestSanitizeForLogging:
    """Test cases for sanitize_for_logging function."""

    def test_sanitize_normal_string(self):
        """Test sanitizing normal string within limit."""
        value = "normal string"
        
        result = sanitize_for_logging(value)
        
        assert result == "normal string"

    def test_sanitize_empty_string(self):
        """Test sanitizing empty string."""
        result = sanitize_for_logging("")
        
        assert result == "<empty>"

    def test_sanitize_none_value(self):
        """Test sanitizing None value."""
        result = sanitize_for_logging(None)
        
        assert result == "<empty>"

    def test_sanitize_long_string_default_limit(self):
        """Test sanitizing string exceeding default limit."""
        value = "a" * 150  # Longer than default 100
        expected = "a" * 100 + "..."
        
        result = sanitize_for_logging(value)
        
        assert result == expected

    def test_sanitize_long_string_custom_limit(self):
        """Test sanitizing string with custom limit."""
        value = "a" * 50
        expected = "a" * 20 + "..."
        
        result = sanitize_for_logging(value, max_length=20)
        
        assert result == expected

    def test_sanitize_string_at_limit(self):
        """Test sanitizing string exactly at limit."""
        value = "a" * 100
        
        result = sanitize_for_logging(value, max_length=100)
        
        assert result == value

    def test_sanitize_string_one_char_over_limit(self):
        """Test sanitizing string one character over limit."""
        value = "a" * 11
        expected = "a" * 10 + "..."
        
        result = sanitize_for_logging(value, max_length=10)
        
        assert result == expected

    def test_sanitize_short_string_large_limit(self):
        """Test sanitizing short string with large limit."""
        value = "short"
        
        result = sanitize_for_logging(value, max_length=1000)
        
        assert result == "short"

    def test_sanitize_special_characters(self):
        """Test sanitizing string with special characters."""
        value = "special@#$%^&*()chars"
        
        result = sanitize_for_logging(value)
        
        assert result == "special@#$%^&*()chars"

    def test_sanitize_unicode_characters(self):
        """Test sanitizing string with unicode characters."""
        value = "unicode 日本語 test"
        
        result = sanitize_for_logging(value)
        
        assert result == "unicode 日本語 test"

    def test_sanitize_newlines_and_tabs(self):
        """Test sanitizing string with newlines and tabs."""
        value = "line1\nline2\tcolumn"
        
        result = sanitize_for_logging(value)
        
        assert result == "line1\nline2\tcolumn"

    def test_sanitize_zero_max_length(self):
        """Test sanitizing with zero max length."""
        value = "test"
        expected = "..."
        
        result = sanitize_for_logging(value, max_length=0)
        
        assert result == expected

    def test_sanitize_negative_max_length(self):
        """Test sanitizing with negative max length."""
        value = "test"
        expected = "..."
        
        result = sanitize_for_logging(value, max_length=-5)
        
        assert result == expected

    def test_sanitize_very_long_string(self):
        """Test sanitizing very long string."""
        value = "x" * 10000
        expected = "x" * 100 + "..."
        
        result = sanitize_for_logging(value)
        
        assert result == expected
        assert len(result) == 103  # 100 chars + "..."

    def test_sanitize_whitespace_only(self):
        """Test sanitizing whitespace-only string."""
        value = "   "
        
        result = sanitize_for_logging(value)
        
        assert result == "   "

    def test_sanitize_sql_injection_attempt(self):
        """Test sanitizing potential SQL injection string."""
        value = "'; DROP TABLE users; --"
        
        result = sanitize_for_logging(value)
        
        assert result == "'; DROP TABLE users; --"


class TestSecurityUtilitiesIntegration:
    """Integration tests for security utilities."""

    def test_mask_and_sanitize_combined(self):
        """Test combining mask_password and sanitize_for_logging."""
        conn_str = "postgresql://user:verylongpassword123456789@localhost/db"
        
        # First mask the password
        masked = mask_password(conn_str)
        
        # Then sanitize for logging
        sanitized = sanitize_for_logging(masked, max_length=50)
        
        expected = "postgresql://user:********@localhost/db"
        assert sanitized == expected

    def test_real_world_connection_strings(self):
        """Test with real-world connection string patterns."""
        test_cases = [
            # PostgreSQL URL
            "postgresql://admin:secret@localhost:5432/mydb",
            # Connection string with multiple params
            "host=localhost port=5432 user=admin password=secret dbname=test sslmode=require",
            # Mixed case
            "Host=localhost PORT=5432 User=admin Password=secret Dbname=test",
            # With special chars in password
            "postgresql://user:p@ssw0rd!@example.com:5432/production"
        ]
        
        for conn_str in test_cases:
            masked = mask_password(conn_str)
            sanitized = sanitize_for_logging(masked)
            
            # Verify no actual passwords remain
            assert "secret" not in masked
            assert "p@ssw0rd!" not in masked
            
            # Verify masking pattern exists
            assert "********" in masked
            
            # Verify sanitization doesn't break the string
            assert len(sanitized) <= 103  # max_length + "..."

    def test_empty_and_edge_cases(self):
        """Test empty and edge cases for both functions."""
        edge_cases = ["", None, "   ", "password=", "://user:@host/db"]
        
        for case in edge_cases:
            # Should not raise exceptions
            if case is not None:
                masked = mask_password(case)
                sanitized = sanitize_for_logging(masked)
                
                assert isinstance(masked, str)
                assert isinstance(sanitized, str)
            else:
                sanitized = sanitize_for_logging(case)
                assert sanitized == "<empty>"

    def test_performance_with_large_strings(self):
        """Test performance with large connection strings."""
        # Create a large connection string
        large_conn = "password=secret;" * 1000
        
        # Should handle large strings efficiently
        masked = mask_password(large_conn)
        sanitized = sanitize_for_logging(masked)
        
        # Verify all passwords are masked
        assert "secret" not in masked
        assert masked.count("********") == 1000
        
        # Verify sanitization works
        assert len(sanitized) <= 103