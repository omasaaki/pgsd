"""Main entry point for PGSD."""

import sys
from typing import Optional


def main(args: Optional[list] = None) -> int:
    """Main entry point."""
    if args is None:
        args = sys.argv[1:]

    print("PostgreSQL Schema Diff Tool v0.1.0")
    print("Not implemented yet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
