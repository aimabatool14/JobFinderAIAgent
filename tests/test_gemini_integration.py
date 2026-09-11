"""
Unit tests for Gemini client, prompt formatting, and structured schemas.
"""

import unittest
from unittest.mock import patch, MagicMock

from src.schemas import (
    CVProfile,
    JobProfile,
    MatchResult,
    CVImprovementResult,
    validate_schema,
)
from src.gemini_client import (
    GeminiClient,
    GeminiKeyMissingError,
    GeminiResponseFormatError,
    clean_and_parse_json,
    get_api_key,
)
from src.prompts import (
    CV_ANALYSIS_USER_PROMPT,
    JOB_ANALYSIS_USER_PROMPT,
    JOB_MATCH_USER_PROMPT,
)


class TestSchemas(unittest.TestCase):
    def test_cv_profile_schema_fields(self):
        sample_cv_dict = {
            "name": "Jane Doe",
            "summary": "Experienced Full-Stack Developer",
            "skills": ["Python", "React", "Docker"],
            "technical_skills": ["Python", "Docker"],
            "soft_skills": ["Leadership"],
            "education": [{"degree": "B.S. Software Engineering", "institution": "State University", "year": "2020"}],
            "certifications": ["AWS Solution Architect"],
            "experience": [{"role": "Senior Dev", "company": "Acme Corp", "duration": "2020-Present", "years": 4.0}],
            "projects": [{"name": "TaskFlow", "description": "Workflow engine", "technologies": ["Python"]}],
            "languages": ["English"],
            "total_experience_years": 4.0,
        }
        validated = validate_schema(CVProfile, sample_cv_dict)
        self.assertEqual(validated["name"], "Jane Doe")
        self.assertEqual(validated["summary"], "Experienced Full-Stack Developer")
        self.assertIn("Python", validated["technical_skills"])
        self.assertEqual(validated["total_experience_years"], 4.0)
        # Check backward compatibility aliases
        self.assertEqual(validated["professional_summary"], "Experienced Full-Stack Developer")
        self.assertEqual(validated["years_of_experience"], 4.0)

    def test_job_profile_schema_fields(self):
        sample_job_dict = {
            "title": "Senior Backend Engineer",
            "required_skills": ["Python", "FastAPI", "PostgreSQL"],
            "preferred_skills": ["Kafka", "Kubernetes"],
            "responsibilities": ["Design microservices", "Lead code reviews"],
            "experience_requirements": "5+ years backend experience",
            "education_requirements": "B.S. in CS or equivalent",
            "certifications": ["GCP Cloud Engineer"],
            "keywords": ["Microservices", "REST", "CI/CD"],
        }
        validated = validate_schema(JobProfile, sample_job_dict)
        self.assertEqual(validated["title"], "Senior Backend Engineer")
        self.assertIn("FastAPI", validated["required_skills"])
        self.assertIn("Kafka", validated["preferred_skills"])

    def test_match_result_schema_fields(self):
        sample_match_dict = {
            "overall_score": 88,
            "matching_skills": ["Python", "Docker"],
            "partial_matches": ["Flask (similar to FastAPI)"],
            "missing_skills": ["Kubernetes"],
            "experience_match": "Senior level aligns with 5-year requirement.",
            "education_match": "B.S. satisfies academic requirement.",
            "strengths": ["Strong Python foundation"],
            "gaps": ["Lacks container orchestration experience"],
            "recommendations": ["Highlight Docker Swarm / Kube cluster knowledge"],
            "explanation": "Calculated as 45% skills + 25% exp + 15% edu + 15% proj = 88%",
        }
        validated = validate_schema(MatchResult, sample_match_dict)
        self.assertEqual(validated["overall_score"], 88)
        self.assertEqual(validated["overall_match_percentage"], 88)
        self.assertIn("AI Compatibility Score: 88%", validated["compatibility_label"])
        self.assertIn("Kubernetes", validated["missing_skills"])


class TestGeminiClientHelpers(unittest.TestCase):
    def test_clean_and_parse_json_markdown_block(self):
        raw = "```json\n{\n  \"title\": \"Data Scientist\",\n  \"required_skills\": [\"Python\", \"PyTorch\"]\n}\n```"
        parsed = clean_and_parse_json(raw)
        self.assertEqual(parsed["title"], "Data Scientist")
        self.assertEqual(parsed["required_skills"], ["Python", "PyTorch"])

    def test_clean_and_parse_json_embedded_braces(self):
        raw = "Here is the result:\n{\n  \"overall_score\": 92,\n  \"matching_skills\": [\"Go\"]\n}\nHope this helps!"
        parsed = clean_and_parse_json(raw)
        self.assertEqual(parsed["overall_score"], 92)

    def test_clean_and_parse_json_invalid(self):
        with self.assertRaises(GeminiResponseFormatError):
            clean_and_parse_json("Definitely not valid json format at all.")

    def test_missing_api_key_raises_error(self):
        with patch("src.gemini_client.get_api_key", return_value=None):
            client = GeminiClient(api_key=None)
            self.assertFalse(client.is_configured)
            with self.assertRaises(GeminiKeyMissingError):
                client.analyze_cv("Sample CV text that is long enough to trigger parsing.")

    def test_prompt_formatting_integrity(self):
        formatted = CV_ANALYSIS_USER_PROMPT.format(cv_text="Software Engineer with Python skills.")
        self.assertIn("Software Engineer with Python skills.", formatted)
        self.assertIn("CVProfile", formatted)


if __name__ == "__main__":
    unittest.main()
