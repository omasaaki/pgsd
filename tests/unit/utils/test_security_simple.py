"""Simple tests for security utilities."""

import pytest
import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from pgsd.utils.security import (
    mask_password,
    sanitize_for_logging
)


class TestMaskPassword:
    """Test password masking functionality."""

    def test_mask_password_basic(self):
        """Test basic password masking."""
        conn_str = "postgresql://user:password@localhost:5432/dbname"
        result = mask_password(conn_str)
        
        assert "password" not in result
        assert "********" in result
        assert "user" in result
        assert "localhost" in result

    def test_mask_password_with_special_chars(self):
        """Test password masking with special characters."""
        conn_str = "postgresql://user:p@ssw0rd!@localhost:5432/dbname"
        result = mask_password(conn_str)
        
        assert "p@ssw0rd!" not in result
        assert "********" in result

    def test_mask_password_no_password(self):
        """Test connection string without password."""
        conn_str = "postgresql://user@localhost:5432/dbname"
        result = mask_password(conn_str)
        
        assert result == conn_str

    def test_mask_password_empty(self):
        """Test empty connection string."""
        result = mask_password("")
        assert result == ""

    def test_mask_password_custom_mask(self):
        """Test custom mask character."""
        conn_str = "postgresql://user:secret@localhost:5432/dbname"
        result = mask_password(conn_str, mask_char="X")
        
        assert "secret" not in result
        assert "XXXXXXXX" in result

    def test_mask_password_key_value_format(self):
        """Test password masking in key=value format."""
        conn_str = "host=localhost dbname=test user=admin password=secret123"
        result = mask_password(conn_str)
        
        assert "secret123" not in result
        assert "password=********" in result
        assert "host=localhost" in result

    def test_mask_password_case_insensitive(self):
        """Test case insensitive password masking."""
        conn_str = "host=localhost PASSWORD=Secret123 user=admin"
        result = mask_password(conn_str)
        
        assert "Secret123" not in result
        assert "PASSWORD=********" in result


class TestSanitizeForLogging:
    """Test logging sanitization functionality."""

    def test_sanitize_for_logging_basic(self):
        """Test basic sanitization."""
        value = "normal string"
        result = sanitize_for_logging(value)
        
        assert result == "normal string"

    def test_sanitize_for_logging_empty(self):
        """Test sanitization of empty string."""
        result = sanitize_for_logging("")
        assert result == "<empty>"

    def test_sanitize_for_logging_none(self):
        """Test sanitization of None."""
        result = sanitize_for_logging(None)
        assert result == "<empty>"

    def test_sanitize_for_logging_long_string(self):
        """Test sanitization of long string."""
        long_string = "a" * 200
        result = sanitize_for_logging(long_string)
        
        assert len(result) <= 103  # 100 + "..."
        assert result.endswith("...")

    def test_sanitize_for_logging_custom_length(self):
        """Test sanitization with custom max length."""
        long_string = "a" * 100
        result = sanitize_for_logging(long_string, max_length=50)
        
        assert len(result) <= 53  # 50 + "..."
        assert result.endswith("...")

    def test_sanitize_for_logging_exact_length(self):
        """Test sanitization with exact length."""
        value = "a" * 100
        result = sanitize_for_logging(value, max_length=100)
        
        assert result == value  # Should not be truncated

    def test_sanitize_for_logging_whitespace(self):
        """Test sanitization of whitespace."""
        value = "   "
        result = sanitize_for_logging(value)
        
        assert result == "   "  # Should preserve whitespace


class TestSecurityIntegration:
    """Integration tests for security utilities."""

    def test_combined_security_operations(self):
        """Test combining security operations."""
        conn_str = "postgresql://user:very_long_password_123@localhost:5432/database_name"
        
        # First mask password
        masked = mask_password(conn_str)
        assert "very_long_password_123" not in masked
        
        # Then sanitize for logging
        sanitized = sanitize_for_logging(masked, max_length=50)
        assert len(sanitized) <= 53
        assert "********" in sanitized

    def test_security_with_various_formats(self):
        """Test security functions with various connection formats."""
        test_cases = [
            "postgresql://user:pass@localhost/db",
            "host=localhost user=admin password=secret dbname=test",
            "mysql://root:password@localhost:3306/mydb",
            "mongodb://user:pass@localhost:27017/db"
        ]
        
        for conn_str in test_cases:
            masked = mask_password(conn_str)
            sanitized = sanitize_for_logging(masked)
            
            # Should not contain obvious passwords
            assert "pass" not in masked.lower() or "password" not in masked.lower()
            assert "secret" not in masked.lower()
            
            # Should be safe for logging
            assert len(sanitized) <= 103

    def test_security_error_handling(self):
        """Test security functions handle errors gracefully."""
        # Test with various edge cases
        edge_cases = [
            None,
            "",
            "   ",
            "no_password_here",
            "user:@host",  # Empty password
            "://no_user_pass@host",
            "password=",  # Empty password value
        ]
        
        for case in edge_cases:
            try:
                if case is not None:
                    masked = mask_password(case)
                    sanitized = sanitize_for_logging(masked)
                    
                    # Should not crash
                    assert isinstance(masked, str)
                    assert isinstance(sanitized, str)
                else:
                    sanitized = sanitize_for_logging(case)
                    assert sanitized == "<empty>"
            except Exception as e:
                pytest.fail(f"Security function failed on input {case}: {e}")

    def test_security_consistency(self):
        """Test that security functions are consistent."""
        test_string = "postgresql://user:password123@localhost/db"
        
        # Multiple calls should give same result
        result1 = mask_password(test_string)
        result2 = mask_password(test_string)
        
        assert result1 == result2
        
        # Sanitization should be consistent
        sanitized1 = sanitize_for_logging(result1)
        sanitized2 = sanitize_for_logging(result1)
        
        assert sanitized1 == sanitized2

    def test_security_with_real_scenarios(self):
        """Test security functions with realistic scenarios."""
        # Database connection strings from different environments
        scenarios = [
            {
                "name": "development",
                "conn_str": "postgresql://dev_user:dev_pass@localhost:5432/dev_db",
                "should_mask": True
            },
            {
                "name": "production",
                "conn_str": "postgresql://prod_user:super_secure_password_123!@prod-db.example.com:5432/prod_db",
                "should_mask": True
            },
            {
                "name": "no_password",
                "conn_str": "postgresql://user@localhost:5432/db",
                "should_mask": False
            },
            {
                "name": "key_value_format",
                "conn_str": "host=localhost port=5432 dbname=mydb user=myuser password=mypass",
                "should_mask": True
            }
        ]
        
        for scenario in scenarios:
            masked = mask_password(scenario["conn_str"])
            sanitized = sanitize_for_logging(masked)
            
            if scenario["should_mask"]:
                # Should contain masked password
                assert "********" in masked
                # Should not contain original password patterns
                assert "pass" not in masked.lower() or "password=********" in masked.lower()
            else:
                # Should be unchanged if no password
                assert masked == scenario["conn_str"]
            
            # Should be safe for logging
            assert isinstance(sanitized, str)
            assert len(sanitized) <= 103