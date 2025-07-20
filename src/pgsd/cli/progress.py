"""Progress reporting functionality for CLI operations.

This module provides progress reporting capabilities for long-running
CLI operations, including progress bars and status updates.
"""

import sys
import time
from typing import Optional


class ProgressReporter:
    """Reports progress for CLI operations.
    
    Provides progress indication through console output including
    progress bars and status messages.
    """

    def __init__(self, show_progress: bool = True):
        """Initialize progress reporter.
        
        Args:
            show_progress: Whether to show progress output
        """
        self.show_progress_enabled = show_progress
        self.current_stage = ""
        self.start_time = time.time()

    def show_progress(self, stage: str, percentage: float) -> None:
        """Show progress information.
        
        Args:
            stage: Current operation stage description
            percentage: Progress percentage (0-100)
        """
        self.current_stage = stage
        
        if not self.show_progress_enabled:
            return
        
        # Create progress bar
        bar_width = 40
        filled_width = int(bar_width * percentage / 100)
        bar = '█' * filled_width + '░' * (bar_width - filled_width)
        
        # Calculate elapsed time
        elapsed_time = time.time() - self.start_time
        
        # Format output
        output = f"\r{stage}: [{bar}] {percentage:6.1f}% ({elapsed_time:.1f}s)"
        
        # Print without newline
        sys.stdout.write(output)
        sys.stdout.flush()
        
        # Add newline if complete
        if percentage >= 100:
            sys.stdout.write('\n')
            sys.stdout.flush()

    def show_status(self, message: str) -> None:
        """Show status message.
        
        Args:
            message: Status message to display
        """
        if not self.show_progress_enabled:
            return
        
        print(f"Status: {message}")

    def show_warning(self, message: str) -> None:
        """Show warning message.
        
        Args:
            message: Warning message to display
        """
        print(f"Warning: {message}")

    def show_error(self, message: str) -> None:
        """Show error message.
        
        Args:
            message: Error message to display
        """
        print(f"Error: {message}", file=sys.stderr)

    def clear_line(self) -> None:
        """Clear the current line."""
        if not self.show_progress_enabled:
            return
        
        sys.stdout.write('\r' + ' ' * 80 + '\r')
        sys.stdout.flush()

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable progress reporting.
        
        Args:
            enabled: Whether to enable progress reporting
        """
        self.show_progress_enabled = enabled


class SimpleProgressReporter(ProgressReporter):
    """Simplified progress reporter without fancy formatting.
    
    Provides basic progress reporting suitable for non-interactive
    environments or when advanced terminal features are not available.
    """

    def show_progress(self, stage: str, percentage: float) -> None:
        """Show simple progress information.
        
        Args:
            stage: Current operation stage description
            percentage: Progress percentage (0-100)
        """
        if not self.show_progress_enabled:
            return
        
        # Only show significant progress updates
        if percentage % 25 == 0 or percentage >= 100:
            elapsed_time = time.time() - self.start_time
            print(f"{stage}: {percentage:.0f}% complete ({elapsed_time:.1f}s)")


class QuietProgressReporter(ProgressReporter):
    """Progress reporter that only shows errors and warnings.
    
    Suitable for quiet mode operation where minimal output is desired.
    """

    def show_progress(self, stage: str, percentage: float) -> None:
        """Show no progress information."""
        pass

    def show_status(self, message: str) -> None:
        """Show no status messages."""
        pass


def create_progress_reporter(
    mode: str = "normal", 
    quiet: bool = False, 
    simple: bool = False
) -> ProgressReporter:
    """Create appropriate progress reporter based on mode.
    
    Args:
        mode: Progress reporting mode
        quiet: Whether to use quiet mode
        simple: Whether to use simple mode
        
    Returns:
        Configured progress reporter instance
    """
    if quiet:
        return QuietProgressReporter(show_progress=False)
    elif simple:
        return SimpleProgressReporter()
    else:
        return ProgressReporter()