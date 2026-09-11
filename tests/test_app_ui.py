"""
Tests for app.py Streamlit UI logic, session keys, and page components.
"""

import unittest
import os
import sys
from unittest.mock import MagicMock, patch

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app
from src.utils import init_session_state, set_nav_page, clear_cv_state


class TestAppUI(unittest.TestCase):

    def test_app_pages_list(self):
        """Verify all requested 8 pages are handled in app."""
        expected_pages = [
            "Home",
            "Welcome",
            "Upload CV",
            "CV Analysis",
            "Find Jobs",
            "Job Match",
            "CV Improvement",
            "About",
        ]
        # Check that page functions exist in app.py
        self.assertTrue(callable(app.page_home))
        self.assertTrue(callable(app.page_welcome))
        self.assertTrue(callable(app.page_upload_cv))
        self.assertTrue(callable(app.page_cv_analysis))
        self.assertTrue(callable(app.page_find_jobs))
        self.assertTrue(callable(app.page_job_match))
        self.assertTrue(callable(app.page_cv_improvement))
        self.assertTrue(callable(app.page_about))

    def test_video_fallback_does_not_crash(self):
        """Verify render_video_fallback runs without errors even if video is absent."""
        if app.st is not None:
            # Mock st.markdown
            with patch.object(app.st, "markdown") as mock_md:
                app.render_video_fallback()
                mock_md.assert_called()

    def test_session_state_stability(self):
        """Verify all required keys exist in session state."""
        if app.st is not None:
            init_session_state()
            required_keys = [
                "nav_page",
                "uploaded_cv",
                "extracted_text",
                "cv_profile",
                "selected_job",
                "job_profile",
                "match_result",
            ]
            for key in required_keys:
                self.assertIn(key, app.st.session_state)


if __name__ == "__main__":
    unittest.main()
