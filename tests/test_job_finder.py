"""
Unit tests for the Find Jobs module and JobProvider architecture (src/job_finder.py).
Tests:
1. JobProvider ABC interface contracts
2. DemoJobProvider filtering (job title, skills, location, work type, experience level)
3. DemoJobProvider integrity (results labeled 'Demo job data', no fake URLs invented)
4. RealJobProvider unconfigured vs configured behavior
5. Automated fallback to DemoJobProvider when real credentials are absent
6. CV-based job recommendation and match score calculation
7. URL truthfulness validation (no invented links)
"""

import unittest
from unittest.mock import patch, MagicMock
from src.job_finder import (
    JobProvider,
    RealJobProvider,
    DemoJobProvider,
    JobFinderService,
    JobSearchFilters,
    calculate_job_cv_match_score,
    DEMO_LABEL,
)


class TestJobFinder(unittest.TestCase):

    def setUp(self):
        self.demo_provider = DemoJobProvider()
        self.real_unconfigured = RealJobProvider(api_key=None, endpoint_url=None)
        self.service = JobFinderService(
            real_provider=self.real_unconfigured,
            demo_provider=self.demo_provider,
        )

        self.sample_cv = {
            "name": "Alex Chen",
            "skills": ["Python", "FastAPI", "Docker", "PostgreSQL", "Redis"],
            "technical_skills": ["Python", "FastAPI", "Docker", "PostgreSQL", "Redis"],
            "years_of_experience": 4.5,
        }

    def test_job_provider_interface_abstraction(self):
        """JobProvider must enforce ABC methods."""
        class IncompleteProvider(JobProvider):
            pass

        with self.assertRaises(TypeError):
            IncompleteProvider()

    def test_demo_provider_properties_and_labeling(self):
        """Demo provider must declare is_demo=True, is_configured=True, and label results as Demo job data."""
        self.assertTrue(self.demo_provider.is_demo)
        self.assertTrue(self.demo_provider.is_configured)
        self.assertEqual(self.demo_provider.name, "Demo Job Provider")

        jobs = self.demo_provider.search_jobs(JobSearchFilters())
        self.assertGreater(len(jobs), 0)
        for job in jobs:
            self.assertEqual(job["source"], DEMO_LABEL)
            self.assertTrue(job["is_demo"])

    def test_no_invented_application_urls_in_demo_data(self):
        """Demo jobs must not invent application links or external URLs."""
        jobs = self.demo_provider.search_jobs(JobSearchFilters())
        for job in jobs:
            url = job.get("original_application_url") or job.get("url")
            # If not a genuine verified URL, must be None
            self.assertIsNone(url, f"Demo job {job.get('id')} should not invent application link, got: {url}")

    def test_filter_by_job_title(self):
        """Filters jobs matching title keyword."""
        filters = JobSearchFilters(job_title="DevOps")
        jobs = self.demo_provider.search_jobs(filters)
        self.assertGreaterEqual(len(jobs), 1)
        for job in jobs:
            self.assertIn("devops", job["title"].lower() + job["short_description"].lower())

    def test_filter_by_skills(self):
        """Filters jobs requiring specific skills."""
        filters = JobSearchFilters(skills=["React"])
        jobs = self.demo_provider.search_jobs(filters)
        self.assertGreaterEqual(len(jobs), 1)
        for job in jobs:
            skills = [s.lower() for s in job["required_skills"] + job.get("nice_to_have_skills", [])]
            self.assertTrue(any("react" in s for s in skills) or "react" in job["title"].lower())

    def test_filter_by_location(self):
        """Filters jobs matching specified location."""
        filters = JobSearchFilters(location="Berlin")
        jobs = self.demo_provider.search_jobs(filters)
        self.assertGreaterEqual(len(jobs), 1)
        for job in jobs:
            self.assertIn("berlin", job["location"].lower())

    def test_filter_by_work_type(self):
        """Filters jobs by Remote, Hybrid, or On-site."""
        remote_filters = JobSearchFilters(work_type="Remote")
        remote_jobs = self.demo_provider.search_jobs(remote_filters)
        self.assertGreater(len(remote_jobs), 0)
        for job in remote_jobs:
            self.assertEqual(job.get("work_type"), "Remote")

        hybrid_filters = JobSearchFilters(work_type="Hybrid")
        hybrid_jobs = self.demo_provider.search_jobs(hybrid_filters)
        self.assertGreater(len(hybrid_jobs), 0)
        for job in hybrid_jobs:
            self.assertEqual(job.get("work_type"), "Hybrid")

    def test_filter_by_experience_level(self):
        """Filters jobs by Entry-level, Mid-level, Senior, or Lead."""
        senior_filters = JobSearchFilters(experience_level="Senior")
        senior_jobs = self.demo_provider.search_jobs(senior_filters)
        self.assertGreaterEqual(len(senior_jobs), 1)
        for job in senior_jobs:
            self.assertEqual(job.get("experience_level"), "Senior")

    def test_real_provider_unconfigured_behavior(self):
        """Unconfigured real provider reports is_configured=False and yields empty list."""
        unconfigured = RealJobProvider(api_key=None, endpoint_url=None)
        self.assertFalse(unconfigured.is_configured)
        self.assertFalse(unconfigured.is_demo)
        results = unconfigured.search_jobs(JobSearchFilters(job_title="Python"))
        self.assertEqual(results, [])

    def test_automated_fallback_to_demo_when_no_real_provider(self):
        """When real provider is unconfigured, service automatically defaults to DemoJobProvider with Demo job data label."""
        self.assertFalse(self.service.is_using_real_provider)
        self.assertEqual(self.service.active_source_label, DEMO_LABEL)

        jobs = self.service.get_jobs(job_title="Python")
        self.assertGreater(len(jobs), 0)
        for job in jobs:
            self.assertEqual(job["source"], DEMO_LABEL)
            self.assertTrue(job["is_demo"])

    def test_cv_skills_recommend_relevant_jobs(self):
        """Analyzed CV skills should rank highly relevant jobs first."""
        recommended = self.service.recommend_jobs_for_cv(self.sample_cv, limit=3)
        self.assertEqual(len(recommended), 3)

        # Python / Backend job should be top recommendation for Python engineer
        top_job = recommended[0]
        self.assertIn("python", top_job["title"].lower() + " ".join(top_job["required_skills"]).lower())
        self.assertIsNotNone(top_job.get("match_score"))
        self.assertGreaterEqual(top_job["match_score"], 70)

    def test_match_score_calculation(self):
        """Calculate match score evaluates alignment between job and CV."""
        python_job = {
            "title": "Backend Python Developer",
            "required_skills": ["Python", "FastAPI", "Docker", "PostgreSQL"],
            "experience_level": "Mid-level",
        }
        score = calculate_job_cv_match_score(python_job, self.sample_cv)
        self.assertIsInstance(score, int)
        self.assertGreaterEqual(score, 75)
        self.assertLessEqual(score, 100)

        # Unrelated job
        design_job = {
            "title": "Graphic Designer",
            "required_skills": ["Photoshop", "Illustrator", "Typography"],
            "experience_level": "Mid-level",
        }
        unrelated_score = calculate_job_cv_match_score(design_job, self.sample_cv)
        self.assertLess(unrelated_score, 45)

    def test_real_provider_with_mocked_external_api(self):
        """When real provider is configured, queries endpoint and returns genuine items."""
        import json
        payload = {
            "results": [
                {
                    "id": "ext-101",
                    "title": "Staff Backend Engineer",
                    "company": {"display_name": "Authentic Tech Corp"},
                    "location": {"display_name": "San Francisco, CA"},
                    "description": "Genuine role requirements and specifications.",
                    "redirect_url": "https://careers.authentictech.com/jobs/101",
                    "skills": ["Python", "Kubernetes"],
                }
            ]
        }
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps(payload).encode("utf-8")
        mock_response.__enter__.return_value = mock_response

        with patch("urllib.request.urlopen", return_value=mock_response):
            real_provider = RealJobProvider(
                api_key="valid_test_key_123456",
                endpoint_url="https://api.adzuna.com/v1/api/jobs",
                provider_name="Adzuna",
            )
            self.assertTrue(real_provider.is_configured)

            service_with_real = JobFinderService(real_provider=real_provider, demo_provider=self.demo_provider)
            self.assertTrue(service_with_real.is_using_real_provider)

            jobs = service_with_real.get_jobs(job_title="Backend")
            self.assertEqual(len(jobs), 1)
            self.assertEqual(jobs[0]["company"], "Authentic Tech Corp")
            self.assertEqual(jobs[0]["original_application_url"], "https://careers.authentictech.com/jobs/101")
            self.assertFalse(jobs[0]["is_demo"])


if __name__ == "__main__":
    unittest.main()
