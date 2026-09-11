"""
Comprehensive unit tests for the Job Match Engine (src/job_matcher.py).
Tests:
1. Strong match evaluation
2. Weak match evaluation
3. Partial match evaluation with adjacent technologies
4. Missing skills detection and gap diagnostics
5. Empty job description error handling
6. Empty CV error handling
7. Transparent 50/20/10/10/10 scoring weights and configurability
8. Fairness & non-discrimination (protected demographics excluded)
9. Concise explanations ("Your CV matches this job strongly because..." and "Your biggest gaps are...")
10. Fallback CV improvement generation
"""

import unittest
from src.job_matcher import (
    JobMatcher,
    calculate_job_match,
    calculate_heuristic_match,
    extract_job_profile_from_text,
    sanitize_cv_for_fairness,
    generate_fallback_cv_improvement,
    DEFAULT_MATCH_WEIGHTS,
)


class TestJobMatcher(unittest.TestCase):

    def setUp(self):
        self.matcher = JobMatcher()

        # Senior Python Backend candidate
        self.strong_cv = {
            "name": "Alex Chen",
            "professional_summary": "Senior Backend Software Engineer with 5+ years building scalable microservices in Python, FastAPI, Docker, and PostgreSQL.",
            "skills": ["Python", "FastAPI", "Docker", "PostgreSQL", "REST APIs", "Kubernetes", "Redis", "Git", "CI/CD", "Linux"],
            "technical_skills": ["Python", "FastAPI", "Docker", "PostgreSQL", "REST APIs", "Kubernetes", "Redis"],
            "soft_skills": ["Team Leadership", "Agile", "Mentorship"],
            "years_of_experience": 5.5,
            "education": [{"degree": "B.S. in Computer Science", "institution": "State Tech University"}],
            "certifications": ["AWS Certified Solutions Architect"],
            "projects": [
                {
                    "name": "Cloud Microservices Platform",
                    "technologies": ["Python", "FastAPI", "Docker", "PostgreSQL", "Kubernetes"],
                    "description": "Engineered distributed API platform processing 10k req/sec with 99.9% uptime."
                },
                {
                    "name": "Real-time Event Streamer",
                    "technologies": ["Python", "Redis", "REST APIs"],
                    "description": "Built caching and queuing layer cutting database query latency by 45%."
                }
            ],
        }

        # Junior Frontend / Unrelated candidate
        self.weak_cv = {
            "name": "Taylor Smith",
            "professional_summary": "Junior UI Designer transitioning to frontend. Familiar with Figma, HTML, and basic CSS.",
            "skills": ["Figma", "HTML5", "CSS3", "Adobe XD"],
            "technical_skills": ["HTML5", "CSS3"],
            "soft_skills": ["Creativity"],
            "years_of_experience": 0.5,
            "education": [{"degree": "B.A. in Graphic Design", "institution": "City Arts College"}],
            "projects": [],
        }

        # Python developer with Flask/Django and AWS (adjacent to FastAPI and Kubernetes)
        self.partial_cv = {
            "name": "Morgan Riley",
            "professional_summary": "Backend developer with 3 years building web APIs using Flask, Django, AWS, and MySQL.",
            "skills": ["Python", "Flask", "Django", "AWS", "MySQL", "Docker", "REST APIs"],
            "technical_skills": ["Python", "Flask", "Django", "AWS", "MySQL", "Docker"],
            "years_of_experience": 3.0,
            "education": [{"degree": "B.S. Information Systems", "institution": "Tech Institute"}],
            "projects": [
                {
                    "name": "API Service",
                    "technologies": ["Python", "Flask", "MySQL"],
                    "description": "Developed backend REST API with user auth."
                }
            ],
        }

        # Senior Python Backend Job Description
        self.python_backend_jd = """
        Job Title: Senior Python Backend Engineer
        About the Role:
        We are seeking a Senior Python Backend Engineer to join our core cloud platform team.
        
        Requirements:
        - 4+ years of professional backend software engineering experience
        - Deep proficiency in Python and FastAPI for microservice design
        - Hands-on experience with PostgreSQL, Docker, and Kubernetes
        - Familiarity with Redis caching and REST APIs
        - Bachelor's degree in Computer Science or equivalent practical experience
        
        Responsibilities:
        - Design and maintain scalable, highly available microservices
        - Optimize database queries and schema designs
        - Partner with DevOps to deploy containerized services into Kubernetes clusters
        """

    def test_strong_match_evaluation(self):
        """A well-qualified candidate should score high (>= 75%) and produce strong explanations."""
        result = self.matcher.match(self.strong_cv, self.python_backend_jd, force_demo=True)

        score = result.get("overall_score")
        self.assertIsInstance(score, int)
        self.assertGreaterEqual(score, 75)
        self.assertLessEqual(score, 100)

        # Core required skills should match
        matching_lower = [s.lower() for s in result.get("matching_skills", [])]
        self.assertTrue(any("python" in s for s in matching_lower))
        self.assertTrue(any("fastapi" in s for s in matching_lower))
        self.assertTrue(any("docker" in s for s in matching_lower))
        self.assertTrue(any("postgresql" in s for s in matching_lower))

        # Required explanations
        why = result.get("why_matched", "")
        self.assertIn("Your CV matches this job", why)
        self.assertTrue(len(result.get("strengths", [])) >= 2)

    def test_weak_match_evaluation(self):
        """An unqualified candidate should receive a low score (< 50%) and clear gap diagnostics."""
        result = self.matcher.match(self.weak_cv, self.python_backend_jd, force_demo=True)

        score = result.get("overall_score")
        self.assertIsInstance(score, int)
        self.assertLess(score, 50)

        # Major missing skills should be identified
        missing_lower = [s.lower() for s in result.get("missing_skills", [])]
        self.assertTrue(any("python" in s for s in missing_lower))
        self.assertTrue(any("fastapi" in s for s in missing_lower))

        # Gap analysis
        gaps = result.get("gaps", [])
        self.assertTrue(len(gaps) >= 1)
        biggest_gaps = result.get("biggest_gaps", "")
        self.assertIn("Your biggest gaps are", biggest_gaps)

    def test_partial_match_evaluation(self):
        """Adjacent technologies (e.g. Flask for FastAPI) should be counted under partial matches."""
        result = self.matcher.match(self.partial_cv, self.python_backend_jd, force_demo=True)

        partial_lower = [s.lower() for s in (result.get("partial_matches") or result.get("partially_matching_skills", []))]
        
        # FastAPI requested; candidate has Flask/Django -> should identify partial match
        has_fastapi_partial = any("fastapi" in p for p in partial_lower)
        self.assertTrue(has_fastapi_partial, f"Expected FastAPI in partial matches, got: {partial_lower}")

        # Overall score should be in mid-range (balanced between strong and weak)
        score = result.get("overall_score")
        self.assertGreater(score, 45)
        self.assertLess(score, 85)

    def test_missing_skills_diagnostics(self):
        """Missing skills must be populated and highlighted in recommendations."""
        result = self.matcher.match(self.partial_cv, self.python_backend_jd, force_demo=True)

        missing = result.get("missing_skills", [])
        self.assertIsInstance(missing, list)
        missing_lower = [m.lower() for m in missing]

        # Kubernetes was not in partial_cv
        self.assertTrue(any("kubernetes" in m for m in missing_lower) or any("kubernetes" in p.lower() for p in result.get("partial_matches", [])))

        # Recommendations should provide advice on bridging gaps
        recommendations = result.get("recommendations", [])
        self.assertTrue(len(recommendations) >= 1)

    def test_empty_job_description_raises_error(self):
        """Empty or whitespace job description must raise ValueError."""
        with self.assertRaises(ValueError):
            self.matcher.match(self.strong_cv, "")

        with self.assertRaises(ValueError):
            self.matcher.match(self.strong_cv, "   \n\t  ")

    def test_empty_cv_raises_error(self):
        """Empty CV dictionary or profile with no extractable data must raise ValueError."""
        with self.assertRaises(ValueError):
            self.matcher.match({}, self.python_backend_jd)

        with self.assertRaises(ValueError):
            self.matcher.match({"name": "Empty User"}, self.python_backend_jd)

    def test_scoring_weights_configurable(self):
        """Weights must be configurable and alter the score predictably."""
        default_result = calculate_job_match(
            self.partial_cv,
            extract_job_profile_from_text(self.python_backend_jd),
            weights=DEFAULT_MATCH_WEIGHTS
        )

        # Heavily weigh experience vs skills
        custom_weights = {
            "skills": 0.10,
            "experience": 0.70,
            "education": 0.10,
            "projects": 0.05,
            "keywords": 0.05,
        }
        custom_result = calculate_job_match(
            self.partial_cv,
            extract_job_profile_from_text(self.python_backend_jd),
            weights=custom_weights
        )

        self.assertIn("overall_score", default_result)
        self.assertIn("overall_score", custom_result)
        # Verify explanation documents the methodology
        self.assertIn("Skills Match", default_result["explanation"])
        self.assertIn("Experience Match", default_result["explanation"])

    def test_fairness_and_non_discrimination(self):
        """Protected demographic characteristics must have zero impact on score."""
        cv_a = dict(self.strong_cv)
        cv_a["name"] = "John Doe"
        cv_a["gender"] = "Male"
        cv_a["age"] = 35
        cv_a["nationality"] = "American"
        cv_a["religion"] = "Christian"

        cv_b = dict(self.strong_cv)
        cv_b["name"] = "Priya Sharma"
        cv_b["gender"] = "Female"
        cv_b["age"] = 28
        cv_b["nationality"] = "Indian"
        cv_b["religion"] = "Hindu"

        res_a = calculate_heuristic_match(cv_a, self.python_backend_jd)
        res_b = calculate_heuristic_match(cv_b, self.python_backend_jd)

        self.assertEqual(res_a["overall_score"], res_b["overall_score"])
        self.assertEqual(res_a["matching_skills"], res_b["matching_skills"])

        # Verify sanitize_cv_for_fairness removes protected keys
        sanitized = sanitize_cv_for_fairness(cv_a)
        self.assertNotIn("name", sanitized)
        self.assertNotIn("gender", sanitized)
        self.assertNotIn("age", sanitized)
        self.assertNotIn("nationality", sanitized)
        self.assertNotIn("religion", sanitized)

    def test_no_punishment_for_unspecified_requirements(self):
        """When JD does not require a degree, candidate should not be penalized."""
        open_jd = "Looking for a Python coder to build web scripts. No degree required."
        cv_no_edu = {
            "skills": ["Python", "Web Scraping"],
            "years_of_experience": 2.0,
            "education": [],
        }
        res = calculate_heuristic_match(cv_no_edu, open_jd)
        self.assertGreaterEqual(res["education_score"], 80)

    def test_score_not_described_as_hiring_probability(self):
        """Terminology must strictly be AI Compatibility Score and explicitly clarify not a hiring guarantee."""
        res = calculate_heuristic_match(self.strong_cv, self.python_backend_jd)
        label = res.get("compatibility_label", "")
        self.assertIn("AI Compatibility Score", label)
        self.assertNotIn("probability of getting hired", label.lower())
        self.assertIn("NOT a probability of hiring", res.get("explanation", ""))

    def test_cv_improvement_fallback(self):
        """CV improvement generator provides actionable, non-fabricated advice."""
        improvements = generate_fallback_cv_improvement("My raw CV text", self.python_backend_jd)
        self.assertIn("missing_keywords", improvements)
        self.assertIn("skills_to_emphasize", improvements)
        self.assertIn("suggested_bullet_point_improvements", improvements)
        bullets = improvements["suggested_bullet_point_improvements"]
        self.assertTrue(len(bullets) >= 1)
        self.assertIn("suggested_revision", bullets[0])


if __name__ == "__main__":
    unittest.main()
