"""
Unit tests for JobFinder AI core utilities and job finding services.
"""

import unittest
from src.job_finder import DemoJobProvider, JobFinderService
from src.cv_analyzer import generate_fallback_cv_analysis
from src.utils import export_report_markdown


class TestAppCore(unittest.TestCase):

    def test_demo_job_provider_returns_jobs(self):
        provider = DemoJobProvider()
        jobs = provider.search_jobs()
        self.assertGreater(len(jobs), 0)
        first_job = jobs[0]
        self.assertIn("title", first_job)
        self.assertIn("company", first_job)
        self.assertIn("required_skills", first_job)
        self.assertTrue(first_job.get("is_demo"))

    def test_demo_job_filtering(self):
        provider = DemoJobProvider()
        python_jobs = provider.search_jobs(query="Python")
        self.assertTrue(all("python" in (j["title"] + " " + " ".join(j["required_skills"])).lower() for j in python_jobs))

        remote_jobs = provider.search_jobs(location="Remote")
        self.assertTrue(all("remote" in j["location"].lower() for j in remote_jobs))

    def test_job_finder_service_match_scores(self):
        service = JobFinderService()
        candidate_skills = ["Python", "FastAPI", "Docker", "PostgreSQL"]
        jobs_with_scores = service.get_jobs(query="Python", cv_skills=candidate_skills)
        self.assertGreater(len(jobs_with_scores), 0)
        self.assertIsNotNone(jobs_with_scores[0].get("match_score"))

    def test_fallback_cv_analysis_schema(self):
        sample = "Samantha Ray\nFull Stack Engineer\nSkills: React, Node.js, TypeScript, SQL\nExperience: 3 years"
        parsed = generate_fallback_cv_analysis(sample)
        self.assertIn("name", parsed)
        self.assertIn("technical_skills", parsed)
        self.assertIn("work_experience", parsed)
        self.assertIn("education", parsed)

    def test_export_report_markdown(self):
        cv = {"name": "Test User", "skills": ["Python"], "years_of_experience": 2}
        match = {
            "compatibility_label": "AI Compatibility Score: 85%",
            "matching_skills": ["Python"],
            "missing_skills": ["Docker"],
            "strengths": ["Good coding"],
            "weaknesses_and_gaps": ["No docker"],
            "recommendations": ["Learn docker"],
        }
        report = export_report_markdown(cv, match, "Backend Developer")
        self.assertIn("JobFinder AI - Comprehensive Analysis Report", report)
        self.assertIn("Test User", report)
        self.assertIn("AI Compatibility Score: 85%", report)


if __name__ == "__main__":
    unittest.main()
