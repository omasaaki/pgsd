"""Entry point for python -m pgsd command.

This module provides the entry point when PGSD is executed as a module
using 'python -m pgsd'. It imports and calls the main function from
the main module with proper error handling.

Usage:
    python -m pgsd --help
    python -m pgsd version
    python -m pgsd compare --source-host localhost --source-db db1 --target-host localhost --target-db db2
"""

import sys
from .main import main

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(130)  # SIGINT exit code
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)
