"""Security utilities for PGSD application."""

import re


def mask_password(connection_string: str, mask_char: str = "*") -> str:
    """Mask password in connection string for logging.

    Args:
        connection_string: Connection string that may contain password
        mask_char: Character to use for masking

    Returns:
        Connection string with password masked
    """
    # Pattern to match password in connection string
    password_pattern = r"(password=)[^;\s]+"

    # Replace password with masked version
    masked = re.sub(
        password_pattern, r"\1" + mask_char * 8, connection_string, flags=re.IGNORECASE
    )

    # Also handle URL format
    url_pattern = r"(://[^:]+:)[^@]+(@)"
    masked = re.sub(url_pattern, r"\1" + mask_char * 8 + r"\2", masked)

    return masked


def sanitize_for_logging(value: str, max_length: int = 100) -> str:
    """Sanitize value for safe logging.

    Args:
        value: Value to sanitize
        max_length: Maximum length for logged value

    Returns:
        Sanitized value safe for logging
    """
    if not value:
        return "<empty>"

    # Truncate if too long
    if len(value) > max_length:
        return value[:max_length] + "..."

    return value
