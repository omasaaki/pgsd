"""Simple tests for CLI progress reporting."""

import pytest
import time
from io import StringIO
from unittest.mock import Mock, patch

from pgsd.cli.progress import ProgressReporter


class TestProgressReporter:
    """Test cases for ProgressReporter class."""

    def test_init_default(self):
        """Test ProgressReporter initialization with defaults."""
        reporter = ProgressReporter()
        
        assert reporter.show_progress_enabled is True
        assert reporter.current_stage == ""
        assert isinstance(reporter.start_time, float)

    def test_init_disabled(self):
        """Test ProgressReporter initialization with progress disabled."""
        reporter = ProgressReporter(show_progress=False)
        
        assert reporter.show_progress_enabled is False
        assert reporter.current_stage == ""

    @patch('sys.stdout.write')
    @patch('sys.stdout.flush')
    def test_show_progress_enabled(self, mock_flush, mock_write):
        """Test showing progress when enabled."""
        reporter = ProgressReporter(show_progress=True)
        
        reporter.show_progress("Testing", 50.0)
        
        assert reporter.current_stage == "Testing"
        mock_write.assert_called()
        mock_flush.assert_called()

    @patch('sys.stdout.write')
    def test_show_progress_disabled(self, mock_write):
        """Test showing progress when disabled."""
        reporter = ProgressReporter(show_progress=False)
        
        reporter.show_progress("Testing", 50.0)
        
        # Should not write anything when disabled
        mock_write.assert_not_called()

    @patch('sys.stdout.write')
    @patch('sys.stdout.flush')
    def test_show_progress_zero_percent(self, mock_flush, mock_write):
        """Test showing progress at 0%."""
        reporter = ProgressReporter()
        
        reporter.show_progress("Starting", 0.0)
        
        assert reporter.current_stage == "Starting"
        mock_write.assert_called()

    @patch('sys.stdout.write')
    @patch('sys.stdout.flush')
    def test_show_progress_hundred_percent(self, mock_flush, mock_write):
        """Test showing progress at 100%."""
        reporter = ProgressReporter()
        
        reporter.show_progress("Complete", 100.0)
        
        assert reporter.current_stage == "Complete"
        mock_write.assert_called()

    @patch('sys.stdout.write')
    @patch('sys.stdout.flush')
    def test_show_progress_partial(self, mock_flush, mock_write):
        """Test showing progress at partial completion."""
        reporter = ProgressReporter()
        
        reporter.show_progress("Processing", 75.5)
        
        assert reporter.current_stage == "Processing"
        mock_write.assert_called()

    @patch('sys.stdout.write')
    @patch('sys.stdout.flush')
    def test_progress_bar_formatting(self, mock_flush, mock_write):
        """Test progress bar formatting."""
        reporter = ProgressReporter()
        
        # Test different percentages
        test_cases = [0.0, 25.0, 50.0, 75.0, 100.0]
        
        for percentage in test_cases:
            reporter.show_progress("Test", percentage)
            
            # Check that write was called with a string containing progress elements
            args, _ = mock_write.call_args
            output = args[0]
            
            assert "Test:" in output
            assert "[" in output and "]" in output  # Progress bar brackets
            assert f"{percentage:6.1f}%" in output  # Percentage display

    def test_start_time_tracking(self):
        """Test that start time is properly tracked."""
        start_time = time.time()
        reporter = ProgressReporter()
        
        # Start time should be close to when we created the reporter
        assert abs(reporter.start_time - start_time) < 0.1

    @patch('time.time')
    @patch('sys.stdout.write')
    @patch('sys.stdout.flush')
    def test_elapsed_time_calculation(self, mock_flush, mock_write, mock_time):
        """Test elapsed time calculation."""
        # Mock time progression
        mock_time.side_effect = [100.0, 105.0]  # 5 seconds elapsed
        
        reporter = ProgressReporter()
        reporter.show_progress("Test", 50.0)
        
        # Check that elapsed time is included in output
        args, _ = mock_write.call_args
        output = args[0]
        assert "(5.0s)" in output

    def test_current_stage_update(self):
        """Test that current stage is updated correctly."""
        reporter = ProgressReporter(show_progress=False)  # Disable output for this test
        
        assert reporter.current_stage == ""
        
        reporter.show_progress("Stage 1", 25.0)
        assert reporter.current_stage == "Stage 1"
        
        reporter.show_progress("Stage 2", 50.0)
        assert reporter.current_stage == "Stage 2"

    @patch('sys.stdout.write')
    @patch('sys.stdout.flush')
    def test_multiple_progress_updates(self, mock_flush, mock_write):
        """Test multiple progress updates."""
        reporter = ProgressReporter()
        
        stages = [
            ("Connecting", 10.0),
            ("Loading schema", 30.0),
            ("Comparing", 60.0),
            ("Generating report", 90.0),
            ("Complete", 100.0)
        ]
        
        for stage, percentage in stages:
            reporter.show_progress(stage, percentage)
            assert reporter.current_stage == stage
        
        # Should have been called for each stage
        assert mock_write.call_count == len(stages)

    @patch('sys.stdout.write')
    @patch('sys.stdout.flush')
    def test_progress_bar_width_consistency(self, mock_flush, mock_write):
        """Test that progress bar width is consistent."""
        reporter = ProgressReporter()
        
        # Test various percentages to ensure bar width is consistent
        percentages = [0, 10, 33, 50, 67, 90, 100]
        
        for percentage in percentages:
            reporter.show_progress("Test", percentage)
            
            args, _ = mock_write.call_args
            output = args[0]
            
            # Extract the progress bar part
            start_bracket = output.find('[')
            end_bracket = output.find(']')
            
            if start_bracket != -1 and end_bracket != -1:
                bar_content = output[start_bracket+1:end_bracket]
                # Bar should always be 40 characters wide
                assert len(bar_content) == 40

    def test_edge_case_negative_percentage(self):
        """Test handling of negative percentage."""
        reporter = ProgressReporter(show_progress=False)
        
        # Should handle gracefully without crashing
        reporter.show_progress("Test", -10.0)
        assert reporter.current_stage == "Test"

    def test_edge_case_large_percentage(self):
        """Test handling of percentage over 100."""
        reporter = ProgressReporter(show_progress=False)
        
        # Should handle gracefully without crashing
        reporter.show_progress("Test", 150.0)
        assert reporter.current_stage == "Test"

    @patch('sys.stdout.write')
    @patch('sys.stdout.flush')
    def test_special_characters_in_stage(self, mock_flush, mock_write):
        """Test handling of special characters in stage name."""
        reporter = ProgressReporter()
        
        special_stage = "Tésting spëciâl chäracters & symbols! 🚀"
        reporter.show_progress(special_stage, 50.0)
        
        assert reporter.current_stage == special_stage
        mock_write.assert_called()

    def test_initialization_parameters(self):
        """Test various initialization parameters."""
        # Test with explicit True
        reporter1 = ProgressReporter(show_progress=True)
        assert reporter1.show_progress_enabled is True
        
        # Test with explicit False
        reporter2 = ProgressReporter(show_progress=False)
        assert reporter2.show_progress_enabled is False
        
        # Test default behavior
        reporter3 = ProgressReporter()
        assert reporter3.show_progress_enabled is True

    @patch('time.time')
    def test_time_precision(self, mock_time):
        """Test time precision in output."""
        # Mock specific times for precise testing
        mock_time.side_effect = [1000.0, 1000.123]
        
        reporter = ProgressReporter()
        
        with patch('sys.stdout.write') as mock_write, \
             patch('sys.stdout.flush'):
            reporter.show_progress("Test", 50.0)
            
            args, _ = mock_write.call_args
            output = args[0]
            
            # Should show elapsed time with 1 decimal place
            assert "(0.1s)" in output