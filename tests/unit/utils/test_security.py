"""Tests for security utilities."""

import pytest
import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from pgsd.utils.security import mask_password, sanitize_for_logging


class TestMaskPassword:
    """Test password masking functionality."""

    def test_mask_password_basic(self):
        """Test basic password masking in connection string."""
        connection_str = "host=localhost port=5432 dbname=test password=secret123 user=admin"
        result = mask_password(connection_str)
        
        assert "password=********" in result
        assert "secret123" not in result
        assert "host=localhost" in result
        assert "user=admin" in result

    def test_mask_password_case_insensitive(self):
        """Test password masking is case insensitive."""
        connection_str = "PASSWORD=secret123"
        result = mask_password(connection_str)
        
        assert "PASSWORD=********" in result
        assert "secret123" not in result

    def test_mask_password_url_format(self):
        """Test password masking in URL format."""
        url = "postgresql://username:password123@localhost:5432/dbname"
        result = mask_password(url)
        
        assert "://username:********@" in result
        assert "password123" not in result
        assert "localhost:5432/dbname" in result

    def test_mask_password_complex_url(self):
        """Test password masking in complex URL."""
        url = "postgresql://user:complex@pass@word@host:5432/db"
        result = mask_password(url)
        
        assert "://user:********@" in result
        assert "complex@pass@word" not in result

    def test_mask_password_custom_mask_char(self):
        """Test password masking with custom mask character."""
        connection_str = "password=secret"
        result = mask_password(connection_str, mask_char="X")
        
        assert "password=XXXXXXXX" in result
        assert "secret" not in result

    def test_mask_password_no_password(self):
        """Test masking when no password is present."""
        connection_str = "host=localhost port=5432 dbname=test user=admin"
        result = mask_password(connection_str)
        
        assert result == connection_str

    def test_mask_password_empty_string(self):
        """Test masking with empty string."""
        result = mask_password("")
        assert result == ""

    def test_mask_password_multiple_passwords(self):
        """Test masking multiple password occurrences."""
        connection_str = "password=first password=second"
        result = mask_password(connection_str)
        
        assert "password=********" in result
        assert result.count("password=********") == 2
        assert "first" not in result
        assert "second" not in result

    def test_mask_password_special_characters(self):
        """Test masking passwords with special characters."""
        connection_str = "password=p@$$w0rd!"
        result = mask_password(connection_str)
        
        assert "password=********" in result
        assert "p@$$w0rd!" not in result

    def test_mask_password_with_semicolon_delimiter(self):
        """Test masking with semicolon as delimiter."""
        connection_str = "host=localhost;password=secret;user=admin"
        result = mask_password(connection_str)
        
        assert "password=********" in result
        assert "secret" not in result
        assert "host=localhost" in result


class TestSanitizeForLogging:
    """Test sanitization for logging functionality."""

    def test_sanitize_normal_string(self):
        """Test sanitization of normal string."""
        value = "normal string"
        result = sanitize_for_logging(value)
        
        assert result == "normal string"

    def test_sanitize_empty_string(self):
        """Test sanitization of empty string."""
        result = sanitize_for_logging("")
        assert result == "<empty>"

    def test_sanitize_none_value(self):
        """Test sanitization of None value."""
        result = sanitize_for_logging(None)
        assert result == "<empty>"

    def test_sanitize_long_string_default_length(self):
        """Test sanitization of long string with default max length."""
        long_string = "a" * 150
        result = sanitize_for_logging(long_string)
        
        assert len(result) == 103  # 100 + "..."
        assert result.endswith("...")
        assert result.startswith("a" * 97)

    def test_sanitize_long_string_custom_length(self):
        """Test sanitization of long string with custom max length."""
        long_string = "b" * 50
        result = sanitize_for_logging(long_string, max_length=20)
        
        assert len(result) == 23  # 20 + "..."
        assert result.endswith("...")
        assert result.startswith("b" * 17)

    def test_sanitize_exact_max_length(self):
        """Test sanitization of string exactly at max length."""
        value = "a" * 100
        result = sanitize_for_logging(value, max_length=100)
        
        assert result == value  # Should not truncate

    def test_sanitize_whitespace_string(self):
        """Test sanitization of whitespace-only string."""
        value = "   "
        result = sanitize_for_logging(value)
        
        assert result == "   "  # Whitespace is preserved

    def test_sanitize_special_characters(self):
        """Test sanitization of string with special characters."""
        value = "special !@#$%^&*() chars"
        result = sanitize_for_logging(value)
        
        assert result == value

    def test_sanitize_unicode_characters(self):
        """Test sanitization of string with unicode characters."""
        value = "unicode 文字列 テスト"
        result = sanitize_for_logging(value)
        
        assert result == value

    def test_sanitize_zero_max_length(self):
        """Test sanitization with zero max length."""
        value = "test"
        result = sanitize_for_logging(value, max_length=0)
        
        assert result == "..."

    def test_sanitize_negative_max_length(self):
        """Test sanitization with negative max length."""
        value = "test"
        result = sanitize_for_logging(value, max_length=-5)
        
        assert result == "..."