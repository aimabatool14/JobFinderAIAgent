"""
Unit tests for the CVAnalyzer module.
Tests:
- Strict factual extraction without inventing skills, employers, or degrees
- Empty extraction handling and missing field defaults
- Short text error handling
- Schema normalization and alias consistency
- Fallback analyzer consistency
"""

import unittest
from unittest.mock import patch, MagicMock

from src.cv_analyzer import (
    CVAnalyzer,
    CVAnalysisError,
    extract_supported_cv_facts,
    generate_fallback_cv_analysis,
)
from src.schemas import CVProfile


class TestCVAnalyzer(unittest.TestCase):

    def setUp(self):
        self.analyzer = CVAnalyzer()

    def test_strict_truthfulness_no_invented_degrees_or_skills(self):
        """Verify the extractor does NOT invent degrees or skills not mentioned."""
        plain_text = (
            "Alex Smith\n"
            "Software engineer with 2 years of experience.\n"
            "I write code in Python and SQL.\n"
            "Contact: alex@example.com"
        )
        data = extract_supported_cv_facts(plain_text)

        # Verified present
        self.assertIn("Python", data["technical_skills"])
        self.assertIn("SQL", data["technical_skills"])

        # Not present in text -> MUST NOT be invented!
        self.assertNotIn("AWS", data["technical_skills"])
        self.assertNotIn("Docker", data["technical_skills"])
        self.assertNotIn("Kubernetes", data["technical_skills"])
        self.assertEqual(data["certifications"], [])
        self.assertEqual(data["languages"], [])

    def test_missing_fields_return_empty_values(self):
        """Ensure missing sections return empty lists/strings rather than hallucinations."""
        minimal_text = (
            "Jordan Taylor\n"
            "Recent applicant.\n"
            "Skills: Git, Linux.\n"
            "No formal degree or certifications listed."
        )
        data = extract_supported_cv_facts(minimal_text)
        self.assertEqual(data["certifications"], [])
        self.assertEqual(data["projects"], [])
        self.assertEqual(data["languages"], [])
        self.assertIn("Git", data["technical_skills"])
        self.assertIn("Linux", data["technical_skills"])

    def test_short_text_raises_analysis_error(self):
        """Ensure inputs with fewer than 10 words raise CVAnalysisError."""
        short_text = "Hi my name is Bob developer."
        with self.assertRaises(CVAnalysisError) as ctx:
            self.analyzer.analyze(short_text)
        self.assertIn("contains only", str(ctx.exception))

    def test_empty_text_raises_analysis_error(self):
        """Ensure empty string raises CVAnalysisError."""
        with self.assertRaises(CVAnalysisError) as ctx:
            self.analyzer.analyze("    ")
        self.assertIn("empty", str(ctx.exception).lower())

    def test_analyze_force_demo_returns_valid_cv_profile(self):
        """Ensure analyzer in demo mode returns valid CVProfile structure."""
        sample_cv = (
            "Taylor Reed\n"
            "Full Stack Developer\n"
            "Summary: Experienced developer with 3 years of experience in web systems.\n"
            "Technical Skills: Python, TypeScript, React, PostgreSQL, Docker\n"
            "Soft Skills: Team Leadership, Agile Methodologies\n"
            "Education: Bachelor in Computer Science\n"
            "Languages: English, Spanish"
        )
        result = self.analyzer.analyze(sample_cv, force_demo=True)
        self.assertEqual(result["name"], "Taylor Reed")
        self.assertIn("Python", result["technical_skills"])
        self.assertIn("TypeScript", result["technical_skills"])
        self.assertIn("Team Leadership", result["soft_skills"])
        self.assertIn("English", result["languages"])
        self.assertIn("Spanish", result["languages"])
        # Aliases
        self.assertIn("professional_summary", result)
        self.assertIn("work_experience", result)

    def test_gemini_client_integration(self):
        """Ensure analyzer correctly routes to GeminiClient when configured."""
        mock_gemini = MagicMock()
        mock_gemini.is_configured = True
        mock_gemini.analyze_cv.return_value = {
            "name": "Morgan Chase",
            "summary": "AI Engineer",
            "skills": ["Python", "PyTorch"],
            "technical_skills": ["Python", "PyTorch"],
            "soft_skills": ["Problem Solving"],
            "education": [{"degree": "M.S. in AI", "institution": "Tech Institute"}],
            "certifications": [],
            "experience": [{"role": "ML Engineer", "company": "DataCorp", "duration": "2022-2024", "years": 2.0}],
            "projects": [],
            "languages": ["English"],
            "total_experience_years": 2.0,
        }

        analyzer = CVAnalyzer(gemini_client=mock_gemini)
        sample_cv = "Morgan Chase ML Engineer with 2 years experience in Python and PyTorch. M.S. in AI from Tech Institute."
        result = analyzer.analyze(sample_cv)

        self.assertEqual(result["name"], "Morgan Chase")
        self.assertIn("PyTorch", result["technical_skills"])
        self.assertEqual(result["years_of_experience"], 2.0)
        mock_gemini.analyze_cv.assert_called_once_with(sample_cv)


if __name__ == "__main__":
    unittest.main()
