"""
Job Finder module for JobFinder AI.
Provides an extensible provider architecture:

JobProvider (ABC)
├── RealJobProvider
└── DemoJobProvider

Strict Integrity & Truthfulness Mandate:
- The real provider must only display genuine job listings returned by an authorized/legitimate job data source.
- Never invent jobs, companies, URLs or application links.
- If no real provider/API credentials are configured:
  automatically use DemoJobProvider and clearly label results: "Demo job data".
- If a job does not have a valid application URL, don't invent one.
"""

import os
import abc
import json
import logging
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set

try:
    import streamlit as st
except ImportError:
    st = None

from src.schemas import JobPosting, validate_schema

logger = logging.getLogger("JobFinderAI.JobFinder")

DEMO_LABEL = "Demo job data"


@dataclass
class JobSearchFilters:
    """Standardized search and filter criteria for job providers."""
    job_title: str = ""
    skills: List[str] = field(default_factory=list)
    location: str = ""
    work_type: str = "All"  # "All", "Remote", "Hybrid", "On-site"
    experience_level: str = "All"  # "All", "Entry-level", "Mid-level", "Senior", "Lead"
    job_type: str = "All"
    limit: int = 50

    @classmethod
    def from_inputs(
        cls,
        job_title: str = "",
        query: str = "",
        skills_str: str = "",
        skills: Optional[List[str]] = None,
        location: str = "",
        work_type: str = "All",
        experience_level: str = "All",
        job_type: str = "All",
        limit: int = 50,
        **kwargs,
    ) -> "JobSearchFilters":
        effective_title = (job_title or query or "").strip()
        skills_list = list(skills) if skills else []
        if skills_str:
            for s in skills_str.replace(";", ",").split(","):
                if s.strip() and s.strip() not in skills_list:
                    skills_list.append(s.strip())

        return cls(
            job_title=effective_title,
            skills=skills_list,
            location=location.strip(),
            work_type=work_type.strip(),
            experience_level=experience_level.strip(),
            job_type=job_type.strip(),
            limit=limit,
        )


class JobProvider(abc.ABC):
    """
    Abstract Base Class for all Job Providers.
    Ensures clean abstraction so real APIs (Adzuna, Remotive, RapidAPI, JSearch, etc.)
    can be connected without rewriting the UI or application logic.
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""
        pass

    @property
    @abc.abstractmethod
    def is_configured(self) -> bool:
        """Returns True only when authorized API credentials or active endpoints exist."""
        pass

    @property
    @abc.abstractmethod
    def is_demo(self) -> bool:
        """Flag indicating if this provider serves demonstration data."""
        pass

    @abc.abstractmethod
    def search_jobs(
        self,
        filters: Optional[JobSearchFilters] = None,
        query: str = "",
        location: str = "",
        job_type: str = "All",
        work_type: str = "All",
        experience_level: str = "All",
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Execute job search matching provided filters.
        Returns standardized list of job dictionaries.
        """
        pass


class DemoJobProvider(JobProvider):
    """
    Curated demonstration provider for prototyping and offline evaluation.
    Clearly labeled as 'Demo job data'.
    Never invents application links or external URLs.
    """

    DEMO_JOBS: List[Dict[str, Any]] = [
        {
            "id": "job-demo-01",
            "title": "Backend Software Engineer (Python / FastAPI)",
            "company": "Kinetix Cloud Technologies",
            "location": "Remote",
            "work_type": "Remote",
            "experience_level": "Mid-level",
            "job_type": "Full-time",
            "salary_range": "$115,000 - $145,000",
            "required_skills": ["Python", "FastAPI", "Docker", "PostgreSQL", "REST APIs", "Redis"],
            "nice_to_have_skills": ["Kubernetes", "AWS", "Kafka", "GraphQL"],
            "short_description": "Build high-throughput microservice APIs and distributed data processing pipelines using Python and FastAPI.",
            "full_description": """Role Overview:
We are seeking a Backend Software Engineer with deep Python expertise to build resilient microservice APIs. You will partner with front-end engineers and DevOps specialists to design high-performance data systems.

Key Responsibilities:
- Design, implement, and maintain low-latency REST and async APIs using Python and FastAPI.
- Model and optimize queries for PostgreSQL and caching layers with Redis.
- Package services in Docker containers and automate CI/CD pipeline deployments.
- Participate in architectural reviews, automated testing, and sprint planning.

Requirements:
- 3+ years of professional backend development with Python.
- Proven experience with FastAPI, Flask, or Django in production.
- Solid understanding of relational databases (PostgreSQL) and schema migrations.
- Working knowledge of Docker containerization and Git workflows.
- Bachelor's in Computer Science, related technical field, or equivalent practical experience.""",
            "source": DEMO_LABEL,
            "url": None,
            "original_application_url": None,
            "is_demo": True,
        },
        {
            "id": "job-demo-02",
            "title": "Full Stack Engineer (React & Node.js)",
            "company": "NovaWave Interactive",
            "location": "San Francisco, CA",
            "work_type": "Hybrid",
            "experience_level": "Mid-level",
            "job_type": "Full-time",
            "salary_range": "$125,000 - $160,000",
            "required_skills": ["React", "TypeScript", "Node.js", "Tailwind CSS", "REST APIs", "Git"],
            "nice_to_have_skills": ["Next.js", "PostgreSQL", "Docker", "Testing Library"],
            "short_description": "Design and build user-centric collaborative web applications with modern React, TypeScript, and Node.js microservices.",
            "full_description": """Role Overview:
NovaWave is designing the future of digital workplace collaboration tools. We are looking for an experienced Full Stack Engineer who loves crafting responsive interfaces and reliable server logic.

Key Responsibilities:
- Build state-of-the-art interactive front-ends using React 18+, TypeScript, and Tailwind CSS.
- Develop secure, well-tested Node.js backend routes and real-time WebSocket services.
- Optimize client-side render cycles and bundle sizes.
- Work closely with UI/UX designers to translate Figma specifications into fluid components.

Requirements:
- 3+ years full-stack web application engineering experience.
- Deep expertise in modern JavaScript/TypeScript, React hooks, and component lifecycle.
- Practical experience designing RESTful APIs in Node.js / Express.
- Passion for accessibility, performance profiling, and responsive layouts.""",
            "source": DEMO_LABEL,
            "url": None,
            "original_application_url": None,
            "is_demo": True,
        },
        {
            "id": "job-demo-03",
            "title": "Junior Machine Learning Engineer",
            "company": "Synthetica AI Labs",
            "location": "Boston, MA",
            "work_type": "Remote",
            "experience_level": "Entry-level",
            "job_type": "Full-time",
            "salary_range": "$95,000 - $120,000",
            "required_skills": ["Python", "PyTorch", "NumPy", "Pandas", "Scikit-Learn", "Git"],
            "nice_to_have_skills": ["Hugging Face", "LLMs", "FastAPI", "Docker", "MLflow"],
            "short_description": "Support model fine-tuning, benchmark evaluation, and data preparation pipelines for generative AI solutions.",
            "full_description": """Role Overview:
Synthetica AI Labs is accelerating enterprise adoption of generative AI. We are hiring a Junior ML Engineer to support our model fine-tuning, retrieval evaluation, and data preparation pipelines.

Key Responsibilities:
- Clean, curate, and preprocess large unstructured text and multimodal datasets.
- Implement evaluation benchmarks for LLMs and domain-specific embeddings.
- Collaborate with senior scientists to deploy model inference wrappers using FastAPI and Docker.
- Monitor model drift and output safety metrics.

Requirements:
- Strong programming fundamentals in Python, Pandas, and NumPy.
- Familiarity with PyTorch or TensorFlow, and transformer architectures.
- Demonstrated portfolio or GitHub repository with ML coursework or projects.
- Bachelor's degree in Computer Science, Data Science, Math, or relevant field.""",
            "source": DEMO_LABEL,
            "url": None,
            "original_application_url": None,
            "is_demo": True,
        },
        {
            "id": "job-demo-04",
            "title": "Senior Cloud DevOps & Platform Engineer",
            "company": "Aether Infrastructures",
            "location": "London, UK",
            "work_type": "Remote",
            "experience_level": "Senior",
            "job_type": "Full-time",
            "salary_range": "£85,000 - £105,000",
            "required_skills": ["Docker", "Kubernetes", "AWS", "Terraform", "CI/CD", "Linux"],
            "nice_to_have_skills": ["Python", "Go", "Prometheus", "Grafana", "Security Hardening"],
            "short_description": "Scale multi-region Kubernetes clusters, infrastructure as code, and automated zero-downtime deployment pipelines.",
            "full_description": """Role Overview:
Help us maintain 99.99% reliability across critical multi-cloud deployments. You will architect infrastructure templates, build observability dashboards, and automate deployment workflows.

Key Responsibilities:
- Manage Amazon Web Services (AWS) infrastructure using Terraform.
- Oversee Kubernetes (EKS) workload autoscaling and container security policies.
- Build resilient GitHub Actions and GitLab CI/CD pipelines.
- Establish automated alerting with Prometheus and Grafana.

Requirements:
- 5+ years managing production Linux infrastructure in public cloud environments (AWS/GCP).
- Hands-on Kubernetes deployment and Helm packaging experience.
- Proficient in Terraform, bash scripting, or Python automation.""",
            "source": DEMO_LABEL,
            "url": None,
            "original_application_url": None,
            "is_demo": True,
        },
        {
            "id": "job-demo-05",
            "title": "Data Analyst / Analytics Engineer",
            "company": "Horizon Consumer Goods",
            "location": "Chicago, IL",
            "work_type": "Hybrid",
            "experience_level": "Mid-level",
            "job_type": "Full-time",
            "salary_range": "$85,000 - $110,000",
            "required_skills": ["SQL", "Python", "Tableau", "Data Modeling", "Excel"],
            "nice_to_have_skills": ["dbt", "Snowflake", "BigQuery", "Statistical Analysis"],
            "short_description": "Translate complex transactional data into actionable business intelligence, KPI dashboards, and growth insights.",
            "full_description": """Role Overview:
Join our Commercial Intelligence unit to empower product managers and executives with trusted analytics dashboards and strategic growth insights.

Key Responsibilities:
- Write complex SQL queries, views, and data transformation scripts.
- Build executive KPI dashboards in Tableau and Power BI.
- Perform exploratory statistical analysis in Python (Jupyter, Pandas).
- Partner with marketing and finance leaders to analyze customer retention funnels.

Requirements:
- 3+ years data analytics experience with advanced SQL proficiency.
- Proven experience creating insightful visualizations in Tableau or PowerBI.
- Working knowledge of Python for data manipulation.""",
            "source": DEMO_LABEL,
            "url": None,
            "original_application_url": None,
            "is_demo": True,
        },
        {
            "id": "job-demo-06",
            "title": "Frontend Developer (UI/UX & Web Performance)",
            "company": "Pulse Creative Studio",
            "location": "Berlin, Germany",
            "work_type": "On-site",
            "experience_level": "Mid-level",
            "job_type": "Full-time",
            "salary_range": "€65,000 - €85,000",
            "required_skills": ["React", "TypeScript", "CSS3", "HTML5", "Responsive Design", "Git"],
            "nice_to_have_skills": ["Three.js", "Framer Motion", "Next.js", "Tailwind CSS"],
            "short_description": "Craft high-polish, accessible user interfaces with smooth micro-interactions and rigorous mobile responsiveness.",
            "full_description": """Role Overview:
Pulse Creative Studio is searching for a detail-oriented Frontend Developer who bridges the gap between design vision and high-performance web implementation.

Key Responsibilities:
- Implement responsive, pixel-perfect web interfaces using modern React and CSS frameworks.
- Optimize Core Web Vitals (LCP, FID, CLS) and asset delivery.
- Ensure strict WCAG 2.1 AA accessibility compliance across all components.
- Collaborate with designers in Figma to refine animations and transitions.

Requirements:
- 2+ years professional frontend web development.
- Strong command of modern CSS (flexbox, grid, animations, custom properties).
- Solid proficiency in React and TypeScript.""",
            "source": DEMO_LABEL,
            "url": None,
            "original_application_url": None,
            "is_demo": True,
        },
        {
            "id": "job-demo-07",
            "title": "Lead Mobile Engineer (React Native & iOS/Android)",
            "company": "Apex Health Solutions",
            "location": "Austin, TX",
            "work_type": "Hybrid",
            "experience_level": "Lead",
            "job_type": "Full-time",
            "salary_range": "$160,000 - $190,000",
            "required_skills": ["React Native", "TypeScript", "iOS", "Android", "Mobile Architecture", "REST APIs"],
            "nice_to_have_skills": ["Swift", "Kotlin", "Bluetooth LE", "CI/CD Fastlane"],
            "short_description": "Lead the architecture and delivery of patient-facing mobile health applications with strict reliability standards.",
            "full_description": """Role Overview:
Apex Health is developing patient monitoring applications. As Lead Mobile Engineer, you will set architecture standards, mentor mobile engineers, and ensure reliable cross-platform execution.

Key Responsibilities:
- Architect cross-platform mobile apps using React Native and native modules.
- Ensure HIPAA compliance, data encryption at rest, and secure API handshakes.
- Mentor 4-6 mobile engineers across code reviews and design architecture.
- Automate iOS App Store and Google Play deployments via Fastlane.

Requirements:
- 6+ years mobile software engineering experience (with 3+ in React Native).
- Proven track record releasing top-tier mobile applications to app stores.
- Strong understanding of mobile memory management, offline storage, and push notifications.""",
            "source": DEMO_LABEL,
            "url": None,
            "original_application_url": None,
            "is_demo": True,
        },
        {
            "id": "job-demo-08",
            "title": "Entry-level QA Automation Engineer",
            "company": "Veritas Quality Systems",
            "location": "New York, NY",
            "work_type": "On-site",
            "experience_level": "Entry-level",
            "job_type": "Full-time",
            "salary_range": "$75,000 - $90,000",
            "required_skills": ["Python", "Selenium", "Pytest", "Git", "Unit Testing", "API Testing"],
            "nice_to_have_skills": ["Playwright", "Postman", "Docker", "CI/CD"],
            "short_description": "Write automated test suites, execute regression test scripts, and partner with developers to verify releases.",
            "full_description": """Role Overview:
Kickstart your software testing career at Veritas Quality Systems. You will build automated UI and API test suites to catch defects before they reach production.

Key Responsibilities:
- Write end-to-end regression tests using Python, Pytest, and Selenium.
- Create automated test cases from product specifications and acceptance criteria.
- Report, track, and verify software bugs in Jira.
- Collaborate with development squads to expand continuous testing pipelines.

Requirements:
- Fundamental programming skills in Python or JavaScript.
- Understanding of software testing fundamentals (black-box, boundary testing, regression).
- Eagerness to learn modern test automation frameworks (Playwright, Cypress).
- Technical degree in Computer Science, Software Engineering, or equivalent bootcamp.""",
            "source": DEMO_LABEL,
            "url": None,
            "original_application_url": None,
            "is_demo": True,
        },
    ]

    @property
    def name(self) -> str:
        return "Demo Job Provider"

    @property
    def is_configured(self) -> bool:
        return True

    @property
    def is_demo(self) -> bool:
        return True

    def search_jobs(
        self,
        filters: Optional[JobSearchFilters] = None,
        query: str = "",
        location: str = "",
        job_type: str = "All",
        work_type: str = "All",
        experience_level: str = "All",
        **kwargs,
    ) -> List[Dict[str, Any]]:
        if filters is None:
            filters = JobSearchFilters.from_inputs(
                query=query,
                location=location,
                job_type=job_type,
                work_type=work_type,
                experience_level=experience_level,
                **kwargs,
            )

        results = []
        q_title = filters.job_title.lower()
        q_loc = filters.location.lower()
        q_work = filters.work_type.lower()
        q_exp = filters.experience_level.lower()
        q_jt = filters.job_type.lower()
        filter_skills = [s.lower() for s in filters.skills if s.strip()]

        for job in self.DEMO_JOBS:
            # 1. Job Title Filter / Query
            title = job["title"].lower()
            company = job["company"].lower()
            desc = job["short_description"].lower()
            req_skills = [s.lower() for s in job.get("required_skills", [])]
            all_skills = [s.lower() for s in job.get("required_skills", []) + job.get("nice_to_have_skills", [])]

            if q_title:
                if not (q_title in title or any(q_title in s for s in req_skills)):
                    continue

            # 2. Location Filter
            job_loc = job["location"].lower()
            if q_loc and q_loc not in job_loc:
                continue

            # 3. Work Type Filter (Remote / Hybrid / On-site)
            if q_work and q_work != "all":
                job_work = job.get("work_type", "").lower()
                if q_work not in job_work and q_work not in job_loc:
                    continue

            # 4. Job Type Filter (Full-time / Contract / etc)
            if q_jt and q_jt != "all":
                jt = job.get("job_type", "").lower()
                if q_jt not in jt:
                    continue

            # 5. Experience Level Filter
            if q_exp and q_exp != "all":
                job_exp = job.get("experience_level", "").lower()
                if q_exp not in job_exp:
                    continue

            # 6. Skills Filter
            if filter_skills:
                all_text = (title + " " + desc + " " + " ".join(all_skills)).lower()
                matched_any = any(
                    any(fs in js or js in fs for js in all_skills) or fs in all_text
                    for fs in filter_skills
                )
                if not matched_any:
                    continue

            # Create clean standardized copy
            job_copy = dict(job)
            job_copy["source"] = DEMO_LABEL
            # Strict mandate: never invent fake links
            job_copy["url"] = None
            job_copy["original_application_url"] = None
            job_copy["is_demo"] = True
            results.append(job_copy)

            if len(results) >= filters.limit:
                break

        return results


class RealJobProvider(JobProvider):
    """
    Adapter for genuine external job search APIs (such as Adzuna, Remotive, RapidAPI / JSearch,
    USAJobs, or Arbeitnow).
    
    Strict Integrity Rules:
    - Must ONLY display genuine job listings returned by an authorized/legitimate job data source.
    - Never invent jobs, companies, URLs or application links.
    - If no valid API credentials/endpoint are configured, is_configured is False and returns empty.
    - If a job does not have a valid application URL, don't invent one.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        app_id: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        provider_name: str = "External Job API",
    ):
        self._api_key = api_key or os.getenv("REAL_JOB_API_KEY") or os.getenv("JOB_API_KEY") or os.getenv("RAPIDAPI_KEY")
        self._app_id = app_id or os.getenv("JOB_API_APP_ID") or os.getenv("ADZUNA_APP_ID")
        self._endpoint_url = endpoint_url or os.getenv("JOB_API_ENDPOINT")
        self._provider_name = provider_name

    @property
    def name(self) -> str:
        return self._provider_name

    @property
    def is_configured(self) -> bool:
        """
        True only if real credentials or an authorized live endpoint is configured.
        """
        return bool(self._api_key and len(self._api_key.strip()) >= 6) or bool(self._endpoint_url)

    @property
    def is_demo(self) -> bool:
        return False

    def search_jobs(
        self,
        filters: Optional[JobSearchFilters] = None,
        query: str = "",
        location: str = "",
        job_type: str = "All",
        work_type: str = "All",
        experience_level: str = "All",
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Queries authorized external job endpoint.
        Returns only genuine listings with authentic URLs.
        Never invents jobs or application links.
        """
        if not self.is_configured:
            logger.info("RealJobProvider is not configured with valid credentials.")
            return []

        if filters is None:
            filters = JobSearchFilters.from_inputs(
                query=query,
                location=location,
                job_type=job_type,
                work_type=work_type,
                experience_level=experience_level,
                **kwargs,
            )

        try:
            headers = {
                "User-Agent": "JobFinderAI-StudentClient/1.0",
                "Accept": "application/json",
            }
            if self._api_key:
                headers["Authorization"] = f"Bearer {self._api_key}"
                headers["X-Api-Key"] = self._api_key

            import urllib.parse
            q_param = filters.job_title or (filters.skills[0] if filters.skills else "developer")
            params = {
                "query": q_param,
                "location": filters.location or "",
                "limit": str(min(filters.limit, 20)),
            }
            query_str = urllib.parse.urlencode(params)
            base_url = self._endpoint_url or "https://api.adzuna.com/v1/api/jobs"
            sep = "&" if "?" in base_url else "?"
            full_url = f"{base_url}{sep}{query_str}"

            req = urllib.request.Request(full_url, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as response:
                if response.status != 200:
                    logger.warning("Real job provider returned status %s", response.status)
                    return []
                content = response.read().decode("utf-8")
                data = json.loads(content)

            raw_items = data.get("results") or data.get("jobs") or data.get("data") or []
            standardized = []

            for idx, item in enumerate(raw_items):
                # Only accept items with authentic company and title
                title = item.get("title") or item.get("role") or ""
                company = item.get("company", {}).get("display_name") if isinstance(item.get("company"), dict) else item.get("company")
                if not title or not company:
                    continue

                loc = item.get("location", {}).get("display_name") if isinstance(item.get("location"), dict) else item.get("location", "Unspecified")
                app_url = item.get("redirect_url") or item.get("url") or item.get("link")
                # Validate URL strictly: never invent one
                if app_url and not (str(app_url).startswith("http://") or str(app_url).startswith("https://")):
                    app_url = None

                skills = item.get("skills") or item.get("tags") or []
                if isinstance(skills, str):
                    skills = [s.strip() for s in skills.split(",") if s.strip()]

                standardized.append({
                    "id": str(item.get("id") or f"real-job-{idx}"),
                    "title": str(title),
                    "company": str(company),
                    "location": str(loc),
                    "work_type": "Remote" if "remote" in str(loc).lower() else "On-site",
                    "experience_level": "Mid-level",
                    "job_type": item.get("contract_type", "Full-time"),
                    "salary_range": item.get("salary_range"),
                    "required_skills": skills,
                    "nice_to_have_skills": [],
                    "short_description": item.get("description", "")[:250],
                    "full_description": item.get("description", ""),
                    "source": f"Authorized Provider ({self.name})",
                    "url": app_url,
                    "original_application_url": app_url,
                    "is_demo": False,
                })

            return standardized

        except Exception as exc:
            logger.error("Error retrieving genuine jobs from RealJobProvider: %s", exc)
            return []


def calculate_job_cv_match_score(job: Dict[str, Any], cv_data: Dict[str, Any]) -> int:
    """
    Computes an estimated AI Compatibility Score (0 to 100) between a job posting and an analyzed CV.
    Uses verified skills, seniority, and technical alignment.
    """
    if not cv_data or not isinstance(cv_data, dict):
        return 0

    # 1. Candidate skills
    cand_skills = [s.lower().strip() for s in cv_data.get("skills", []) if s]
    if not cand_skills:
        cand_skills = [s.lower().strip() for s in (cv_data.get("technical_skills", []) + cv_data.get("soft_skills", []))]

    # 2. Required skills
    req_skills = [s.lower().strip() for s in job.get("required_skills", []) if s]
    if not req_skills:
        req_skills = [s.lower().strip() for s in job.get("nice_to_have_skills", []) if s]

    if not req_skills:
        # Evaluate against job title and description keywords
        title_tokens = [t.lower() for t in job.get("title", "").split() if len(t) > 3]
        matched = sum(1 for t in title_tokens if any(t in cs for cs in cand_skills))
        return min(90, max(45, int((matched / max(len(title_tokens), 1)) * 100)))

    # Compute skill overlap with partial substring awareness
    hit_count = 0
    for req in req_skills:
        if any(req in cs or cs in req for cs in cand_skills):
            hit_count += 1
        elif any(part in req for part in ["react", "python", "docker", "sql", "aws", "node", "linux"]):
            for cs in cand_skills:
                if any(p in cs for p in ["react", "python", "docker", "sql", "aws", "node", "linux"]):
                    hit_count += 0.5
                    break

    skill_ratio = hit_count / max(len(req_skills), 1)
    raw_score = int(skill_ratio * 75) + 20

    # Experience alignment adjustment
    cand_exp_raw = cv_data.get("years_of_experience") or cv_data.get("total_experience_years")
    cand_exp = None
    if cand_exp_raw is not None:
        try:
            cand_exp = float(cand_exp_raw)
        except (ValueError, TypeError):
            import re
            m = re.search(r"(\d+(?:\.\d+)?)", str(cand_exp_raw))
            if m:
                try:
                    cand_exp = float(m.group(1))
                except (ValueError, TypeError):
                    cand_exp = None

    job_level = job.get("experience_level", "").lower()
    if cand_exp is not None:
        if "senior" in job_level and cand_exp >= 4.0:
            raw_score += 5
        elif "entry" in job_level:
            raw_score += 5

    return max(15, min(98, raw_score))


class JobFinderService:
    """
    Unified Job Finder Service.
    Orchestrates:
    - Provider resolution: Checks RealJobProvider; if not configured, uses DemoJobProvider.
    - Clear dataset labeling: "Demo job data" whenever demo provider is active.
    - Multi-factor filtering: job title, skills, location, work_type, experience_level.
    - CV Skill Recommendation: ranks or highlights positions matching an analyzed CV.
    - Compatibility scoring.
    """

    def __init__(
        self,
        real_provider: Optional[RealJobProvider] = None,
        demo_provider: Optional[DemoJobProvider] = None,
    ):
        self.real_provider = real_provider or RealJobProvider()
        self.demo_provider = demo_provider or DemoJobProvider()

    @property
    def is_using_real_provider(self) -> bool:
        """Returns True if an authorized real job provider is configured."""
        return self.real_provider.is_configured

    @property
    def active_source_label(self) -> str:
        """Human-readable badge for the active provider."""
        if self.is_using_real_provider:
            return f"Live Data ({self.real_provider.name})"
        return DEMO_LABEL

    def get_jobs(
        self,
        filters: Optional[JobSearchFilters] = None,
        job_title: str = "",
        query: str = "",
        skills: Optional[List[str]] = None,
        cv_skills: Optional[List[str]] = None,
        location: str = "",
        work_type: str = "All",
        experience_level: str = "All",
        job_type: str = "All",
        cv_profile: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Fetches job postings matching filters.
        If real provider credentials are not configured, automatically uses DemoJobProvider
        and clearly labels all items as 'Demo job data'.
        Calculates compatibility match score if cv_profile or cv_skills is provided.
        """
        if cv_skills and cv_profile is None:
            cv_profile = {"skills": cv_skills}

        if filters is None:
            filters = JobSearchFilters.from_inputs(
                job_title=job_title,
                query=query,
                skills=skills or [],
                location=location,
                work_type=work_type,
                experience_level=experience_level,
                job_type=job_type,
                limit=limit,
                **kwargs,
            )

        jobs: List[Dict[str, Any]] = []

        # 1. Attempt RealJobProvider first if configured
        if self.real_provider.is_configured:
            try:
                jobs = self.real_provider.search_jobs(filters)
                if not jobs:
                    logger.info("Real provider returned 0 results; falling back to DemoJobProvider.")
            except Exception as exc:
                logger.error("Error from RealJobProvider: %s", exc)
                jobs = []

        # 2. Fallback to DemoJobProvider if no real provider or no results
        if not jobs:
            jobs = self.demo_provider.search_jobs(filters)
            for j in jobs:
                j["source"] = DEMO_LABEL
                # Ensure no fake URLs exist
                if not j.get("original_application_url") or not str(j.get("original_application_url")).startswith("http"):
                    j["original_application_url"] = None
                    j["url"] = None

        # 3. Calculate Match Score if CV is analyzed
        if cv_profile:
            for job in jobs:
                job["match_score"] = calculate_job_cv_match_score(job, cv_profile)
        else:
            for job in jobs:
                job["match_score"] = None

        return jobs

    def recommend_jobs_for_cv(
        self,
        cv_profile: Dict[str, Any],
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Uses analyzed CV skills to recommend and rank relevant jobs.
        """
        if not cv_profile or not isinstance(cv_profile, dict):
            return self.get_jobs(limit=limit)

        cand_skills = cv_profile.get("skills", [])
        if not cand_skills:
            cand_skills = cv_profile.get("technical_skills", [])

        filters = JobSearchFilters(
            skills=cand_skills[:5],
            limit=limit * 2,
        )

        matched_jobs = self.get_jobs(filters=filters, cv_profile=cv_profile, limit=limit * 2)
        if not matched_jobs:
            # Broader search if strict skills return empty
            matched_jobs = self.get_jobs(cv_profile=cv_profile, limit=limit * 2)

        # Sort jobs by match score descending
        matched_jobs.sort(key=lambda j: j.get("match_score") or 0, reverse=True)
        return matched_jobs[:limit]


def render_find_jobs_dashboard(
    job_service: JobFinderService,
    cv_profile: Optional[Dict[str, Any]] = None,
    on_select_job_for_match: Optional[Any] = None,
) -> None:
    """
    Renders the complete Find Jobs interface in Streamlit:
    - Filters: job title, skills, location, remote/hybrid/on-site, experience level.
    - CV Recommendation quick button when CV is analyzed.
    - Clear data source labeling ("Demo job data" or genuine provider).
    - For each job card:
      * title
      * company
      * location
      * work type
      * required skills
      * short description
      * match score
      * source
      * original application URL (only if genuine/valid; never invent one)
    """
    if st is None:
        return

    st.markdown("## 🔍 Find Jobs")
    st.markdown(
        "Browse open developer and technical positions. Connect an authorized external job feed "
        "or explore our structured catalog with automatic CV alignment scoring."
    )

    # 1. Data Source Transparency Banner
    if not job_service.is_using_real_provider:
        st.markdown(
            f"""
            <div style="background: #fffbeb; border: 1px solid #fde68a; border-left: 5px solid #d97706;
                        border-radius: 8px; padding: 12px 16px; margin-bottom: 20px;">
                <div style="font-weight: 700; color: #92400e; font-size: 0.95rem; display: flex; align-items: center; gap: 8px;">
                    <span>📌</span> {DEMO_LABEL}
                </div>
                <div style="color: #78350f; font-size: 0.85rem; margin-top: 4px;">
                    No external job API credentials are currently configured. Results are populated from our verified prototype
                    catalog. External application links are omitted to prevent invalid redirects.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.success(f"🌐 Active Job Feed: **{job_service.active_source_label}**")

    # 2. Analyzed CV Recommendation Banner
    candidate_name = cv_profile.get("name", "Candidate") if cv_profile else None
    cv_skills = cv_profile.get("skills", []) if cv_profile else []

    if cv_profile and cv_skills:
        st.markdown(
            f"""
            <div style="background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 10px; padding: 14px 18px; margin-bottom: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
                    <div>
                        <div style="font-weight: 700; color: #1e40af; font-size: 0.95rem;">
                            🎯 Active CV Profile: {candidate_name}
                        </div>
                        <div style="color: #3b82f6; font-size: 0.85rem; margin-top: 2px;">
                            Detected skills: {', '.join(cv_skills[:6])}
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 3. Search & Filter Bar
    with st.expander("🔎 Filter & Search Criteria", expanded=True):
        f_col1, f_col2 = st.columns([3, 3])
        with f_col1:
            title_input = st.text_input(
                "Job Title / Role Keyword",
                placeholder="e.g. Python Backend, React Developer, DevOps...",
                key="filter_title",
            )
        with f_col2:
            default_skills_str = ", ".join(cv_skills[:4]) if (cv_skills and st.session_state.get("use_cv_skills")) else ""
            skills_input = st.text_input(
                "Required Skills (comma-separated)",
                value=default_skills_str,
                placeholder="e.g. Python, FastAPI, Docker, TypeScript...",
                key="filter_skills",
            )

        f_col3, f_col4, f_col5 = st.columns([3, 2, 2])
        with f_col3:
            loc_input = st.text_input(
                "Location",
                placeholder="e.g. Remote, San Francisco, London...",
                key="filter_location",
            )
        with f_col4:
            work_type_input = st.selectbox(
                "Work Type",
                ["All", "Remote", "Hybrid", "On-site"],
                index=0,
                key="filter_work_type",
            )
        with f_col5:
            exp_level_input = st.selectbox(
                "Experience Level",
                ["All", "Entry-level", "Mid-level", "Senior", "Lead"],
                index=0,
                key="filter_exp_level",
            )

        col_b1, col_b2, col_b3 = st.columns([2, 3, 2])
        with col_b1:
            st.button("Apply Filters", type="primary", use_container_width=True, key="apply_job_filters_btn")
        with col_b2:
            if cv_profile and cv_skills:
                if st.button("✨ Recommend for My CV", use_container_width=True, key="recommend_cv_jobs_btn"):
                    st.session_state["filter_skills"] = ", ".join(cv_skills[:4])
                    st.session_state["use_cv_skills"] = True
                    st.rerun()
        with col_b3:
            if st.button("Reset Filters", use_container_width=True, key="reset_job_filters_btn"):
                st.session_state["filter_title"] = ""
                st.session_state["filter_skills"] = ""
                st.session_state["filter_location"] = ""
                st.session_state["filter_work_type"] = "All"
                st.session_state["filter_exp_level"] = "All"
                st.session_state["use_cv_skills"] = False
                st.rerun()

    # 4. Fetch filtered jobs
    filters = JobSearchFilters.from_inputs(
        job_title=title_input,
        skills_str=skills_input,
        location=loc_input,
        work_type=work_type_input,
        experience_level=exp_level_input,
    )

    jobs = job_service.get_jobs(filters=filters, cv_profile=cv_profile)

    # Sort if CV loaded and match scores present
    if cv_profile and any(j.get("match_score") for j in jobs):
        jobs.sort(key=lambda j: j.get("match_score") or 0, reverse=True)

    st.markdown(f"### Open Positions ({len(jobs)})")
    st.caption(f"Filtered by role specifications • Provider status: **{job_service.active_source_label}**")

    if not jobs:
        st.info("No job openings match your current filter parameters. Try clearing some filters or selecting 'All' for work type and experience level.")
        return

    # 5. Render Job Cards
    for idx, job in enumerate(jobs):
        with st.container():
            score = job.get("match_score")
            score_badge = ""
            if score is not None:
                if score >= 75:
                    score_badge = f'<div style="background: #ecfdf5; border: 1px solid #10b981; color: #065f46; font-weight: 700; border-radius: 8px; padding: 6px 14px; font-size: 0.95rem;">AI Compatibility: {score}%</div>'
                elif score >= 50:
                    score_badge = f'<div style="background: #fffbeb; border: 1px solid #f59e0b; color: #92400e; font-weight: 700; border-radius: 8px; padding: 6px 14px; font-size: 0.95rem;">AI Compatibility: {score}%</div>'
                else:
                    score_badge = f'<div style="background: #f8fafc; border: 1px solid #cbd5e1; color: #475569; font-weight: 700; border-radius: 8px; padding: 6px 14px; font-size: 0.95rem;">AI Compatibility: {score}%</div>'

            work_type = job.get("work_type", "Remote")
            work_pill = f'<span class="pill-tag pill-blue">{work_type}</span>'
            exp_pill = f'<span class="pill-tag pill-slate">{job.get("experience_level", "Mid-level")}</span>'

            # Skills tags
            skills_html = "".join([f'<span class="pill-tag pill-slate">{s}</span>' for s in job.get("required_skills", [])])

            source_label = job.get("source", DEMO_LABEL)

            st.markdown(
                f"""
                <div class="metric-card" style="border-left: 5px solid #2563eb; margin-bottom: 18px;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px;">
                        <div>
                            <h3 style="margin-top: 0; margin-bottom: 4px; color: #0f172a; font-size: 1.25rem;">
                                {job.get('title')}
                            </h3>
                            <div style="font-weight: 600; color: #2563eb; margin-bottom: 6px;">
                                {job.get('company')} • <span style="color: #64748b; font-weight: 400;">{job.get('location')}</span>
                            </div>
                            <div style="margin-bottom: 8px;">
                                {work_pill} {exp_pill}
                                {f'<span style="color: #64748b; font-size: 0.85rem; margin-left: 8px;">💰 {job.get("salary_range")}</span>' if job.get("salary_range") else ''}
                            </div>
                        </div>
                        <div>
                            {score_badge}
                        </div>
                    </div>
                    <p style="color: #475569; font-size: 0.9375rem; margin: 8px 0 12px 0; line-height: 1.5;">
                        {job.get('short_description')}
                    </p>
                    <div style="margin-bottom: 12px;">
                        <strong style="font-size: 0.8rem; color: #64748b; text-transform: uppercase;">Required Skills: </strong>
                        {skills_html}
                    </div>
                    <div style="font-size: 0.8rem; color: #94a3b8;">
                        Data Source: <strong>{source_label}</strong>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            btn_col1, btn_col2 = st.columns([3, 4])
            with btn_col1:
                match_button_key = f"match_job_btn_{job.get('id', idx)}"
                if st.button("Evaluate Match with My CV ➔", key=match_button_key, type="primary"):
                    if on_select_job_for_match:
                        on_select_job_for_match(job)
                    else:
                        st.session_state["selected_job"] = job
                        desc = job.get("full_description") or job.get("short_description") or ""
                        st.session_state["target_job_description"] = desc
                        st.session_state["job_match_jd_input"] = desc
                        st.session_state["target_job_title"] = f"{job.get('title')} at {job.get('company')}"
                        st.session_state["nav_page"] = "Job Match"
                        st.session_state["sidebar_nav_selection"] = "Job Match"
                        st.rerun()

            with btn_col2:
                # Truthfulness rule: If a job does not have a valid application URL, don't invent one.
                app_url = job.get("original_application_url") or job.get("url")
                if app_url and (str(app_url).startswith("http://") or str(app_url).startswith("https://")):
                    st.link_button("Apply / View Original Posting ↗", app_url, key=f"apply_link_btn_{job.get('id', idx)}")
                else:
                    st.caption("🔒 Verified external application link unavailable for demo position.")
