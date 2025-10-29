#!/usr/bin/env python3
"""
Simplified unit tests for incident time parsing from ORBCOMM emails.

Tests focus on the incident duration extraction feature added in v1.1.0.
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orbcomm_processor import SimpleORBCOMMParser


class TestIncidentDurationFeature(unittest.TestCase):
    """Test the incident duration tracking feature."""

    def setUp(self):
        """Set up test parser instance."""
        self.parser = SimpleORBCOMMParser()

    def test_real_world_s003141_with_subject(self):
        """Test S-003141 incident with proper subject and body."""
        subject = "ORBCOMM Service Notification [S-003141] IDP - RESOLVED"
        body = """
        <html><body>
        <p><b>Platform:</b>&nbsp;IDP</p>
        <p><b>Status:</b>&nbsp;Resolved</p>
        <p><b>Summary:</b> Service outage resolved</p>
        <p><b>Start Time:</b>&nbsp;2025-10-22 15:05 GMT</p>
        <p><b>End Time:</b>&nbsp;2025-10-23 00:37 GMT</p>
        </body></html>
        """

        result = self.parser.parse_text(body, subject=subject)

        # Verify basic parsing
        self.assertEqual(result['reference_number'], 'S-003141')
        self.assertEqual(result['status'], 'Resolved')
        self.assertEqual(result['platform'], 'IDP')

        # Verify incident duration extraction
        self.assertEqual(result['incident_start_time'], '2025-10-22 15:05:00')
        self.assertEqual(result['incident_end_time'], '2025-10-23 00:37:00')
        self.assertEqual(result['incident_duration_minutes'], 572)

    def test_real_world_m003128_with_subject(self):
        """Test M-003128 incident (1 hour duration)."""
        subject = "ORBCOMM Service Notification [M-003128] OGx - RESOLVED"
        body = """
        <html><body>
        <p><b>Platform:</b>&nbsp;OGx</p>
        <p><b>Status:</b>&nbsp;Resolved</p>
        <p><b>Start Time:</b>&nbsp;2025-10-15 10:00 GMT</p>
        <p><b>End Time:</b>&nbsp;2025-10-15 11:00 GMT</p>
        </body></html>
        """

        result = self.parser.parse_text(body, subject=subject)

        self.assertEqual(result['reference_number'], 'M-003128')
        self.assertEqual(result['incident_duration_minutes'], 60)

    def test_resolved_without_incident_times(self):
        """Test backward compatibility - resolved email without incident times."""
        subject = "ORBCOMM Service Notification [S-003000] IDP - RESOLVED"
        body = """
        <html><body>
        <p><b>Platform:</b>&nbsp;IDP</p>
        <p><b>Status:</b>&nbsp;Resolved</p>
        <p><b>Summary:</b> Issue resolved</p>
        </body></html>
        """

        result = self.parser.parse_text(body, subject=subject)

        self.assertEqual(result['status'], 'Resolved')
        self.assertIsNone(result['incident_start_time'])
        self.assertIsNone(result['incident_end_time'])
        self.assertIsNone(result['incident_duration_minutes'])

    def test_open_notification_no_times(self):
        """Test open notification doesn't extract incident times."""
        subject = "ORBCOMM Service Notification [S-003100] IDP - OPEN"
        body = """
        <html><body>
        <p><b>Platform:</b>&nbsp;IDP</p>
        <p><b>Status:</b>&nbsp;Open</p>
        <p><b>Summary:</b> Investigation ongoing</p>
        </body></html>
        """

        result = self.parser.parse_text(body, subject=subject)

        self.assertEqual(result['status'], 'Open')
        self.assertIsNone(result['incident_start_time'])
        self.assertIsNone(result['incident_end_time'])
        self.assertIsNone(result['incident_duration_minutes'])

    def test_malformed_start_time_graceful(self):
        """Test graceful handling of malformed start time."""
        subject = "ORBCOMM Service Notification [S-003200] IDP - RESOLVED"
        body = """
        <html><body>
        <p><b>Status:</b>&nbsp;Resolved</p>
        <p><b>Start Time:</b>&nbsp;INVALID FORMAT</p>
        <p><b>End Time:</b>&nbsp;2025-10-20 14:00 GMT</p>
        </body></html>
        """

        result = self.parser.parse_text(body, subject=subject)

        self.assertEqual(result['status'], 'Resolved')
        self.assertIsNone(result['incident_start_time'])
        self.assertEqual(result['incident_end_time'], '2025-10-20 14:00:00')
        self.assertIsNone(result['incident_duration_minutes'])

    def test_multiday_incident_duration(self):
        """Test incident spanning multiple days."""
        subject = "ORBCOMM Service Notification [S-003300] IDP - RESOLVED"
        body = """
        <html><body>
        <p><b>Status:</b>&nbsp;Resolved</p>
        <p><b>Start Time:</b>&nbsp;2025-10-20 23:00 GMT</p>
        <p><b>End Time:</b>&nbsp;2025-10-22 01:00 GMT</p>
        </body></html>
        """

        result = self.parser.parse_text(body, subject=subject)

        self.assertEqual(result['incident_duration_minutes'], 1560)  # 26 hours

    def test_whitespace_variations_in_html(self):
        """Test parsing with extra whitespace."""
        subject = "ORBCOMM Service Notification [S-003400] IDP - RESOLVED"
        body = """
        <html><body>
        <p><b>Status:</b>&nbsp;Resolved</p>
        <p><b>Start Time:</b>    &nbsp;   2025-10-20 10:00 GMT   </p>
        <p><b>End Time:</b>&nbsp;2025-10-20 12:00 GMT</p>
        </body></html>
        """

        result = self.parser.parse_text(body, subject=subject)

        self.assertEqual(result['incident_start_time'], '2025-10-20 10:00:00')
        self.assertEqual(result['incident_duration_minutes'], 120)


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestIncidentDurationFeature)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
