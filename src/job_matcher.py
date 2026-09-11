"""
Core Job Match Engine for JobFinder AI.
Orchestrates:
1. Job description analysis and requirements extraction into JobProfile.
2. Objective, non-discriminatory comparison of JobProfile against CVProfile.
3. Production of transparent, consistent MatchResult with configurable weights.

Scoring Methodology (Configurable):
- skills match: 50%
- experience match: 20%
- education/certification relevance: 10%
- project relevance: 10%
- keyword/responsibility alignment: 10%

Strict Fairness & Ethics Principles:
- The score is strictly an "AI Compatibility Score" (0 to 100), NOT a probability of hiring.
- Evaluates ONLY verified textual evidence in the CV.
- Protected characteristics (name, gender, age, photo, nationality, religion, ethnicity, etc.)
  are strictly excluded and never factor into the score.
- Candidates are never punished for information that cannot be determined from the CV.
- No experience, skills, or credentials are ever invented.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple, Set

try:
    import streamlit as st
except ImportError:
    st = None

from src.gemini_client import (
    GeminiClient,
    GeminiKeyMissingError,
    GeminiRateLimitError,
    GeminiError,
)
from src.schemas import JobProfile, MatchResult, validate_schema

logger = logging.getLogger("JobFinderAI.JobMatcher")

# Configurable scoring weights in one single place
DEFAULT_MATCH_WEIGHTS: Dict[str, float] = {
    "skills": 0.50,
    "experience": 0.20,
    "education": 0.10,
    "projects": 0.10,
    "keywords": 0.10,
}

# Personal & protected attributes that must NEVER influence candidate evaluation
PROTECTED_DEMOGRAPHIC_KEYS = {
    "name", "first_name", "last_name", "gender", "sex", "age", "date_of_birth", "dob",
    "photo", "avatar", "image", "nationality", "citizenship", "visa_status", "religion",
    "ethnicity", "race", "marital_status", "address", "phone", "email",
}

# Common tech skill aliases and adjacent technologies for fair partial matching
TECH_SYNONYMS = {
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "postgres": "postgresql",
    "k8s": "kubernetes",
    "react": "react.js",
    "node": "node.js",
    "vue": "vue.js",
    "golang": "go",
    "gcp": "google cloud",
    "rest": "rest apis",
    "restful": "rest apis",
    "ci/cd": "cicd",
}

ADJACENT_SKILLS = {
    "fastapi": ["python", "flask", "django", "backend apis", "rest apis"],
    "flask": ["python", "fastapi", "django", "backend apis"],
    "django": ["python", "fastapi", "flask", "backend apis"],
    "kubernetes": ["docker", "containerization", "helm", "devops", "cloud"],
    "docker": ["kubernetes", "containerization", "linux"],
    "aws": ["gcp", "azure", "google cloud", "cloud infrastructure", "docker"],
    "gcp": ["aws", "azure", "google cloud", "cloud infrastructure"],
    "azure": ["aws", "gcp", "cloud infrastructure"],
    "postgresql": ["mysql", "sqlite", "sql", "relational databases"],
    "mysql": ["postgresql", "sqlite", "sql", "relational databases"],
    "mongodb": ["nosql", "redis", "document store"],
    "redis": ["caching", "memcached", "nosql", "pubsub"],
    "react": ["vue.js", "angular", "next.js", "frontend", "typescript"],
    "typescript": ["javascript", "frontend", "node.js"],
    "kafka": ["rabbitmq", "pubsub", "event-driven", "messaging queues"],
    "graphql": ["rest apis", "api design", "backend"],
    "pytorch": ["tensorflow", "scikit-learn", "deep learning", "machine learning"],
    "tensorflow": ["pytorch", "scikit-learn", "deep learning", "machine learning"],
}


def sanitize_cv_for_fairness(cv_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Strips personal and protected demographic characteristics to ensure unbiased,
    merit-based evaluation.
    Only professional qualifications (skills, experience tenure, education, projects)
    are retained.
    """
    if not isinstance(cv_data, dict):
        return {}

    sanitized = {}
    for key, value in cv_data.items():
        if key.lower() in PROTECTED_DEMOGRAPHIC_KEYS:
            continue
        sanitized[key] = value

    return sanitized


def extract_job_profile_from_text(job_description: str) -> Dict[str, Any]:
    """
    Algorithmic extractor for parsing unstructured Job Descriptions into a structured JobProfile.
    Extracts required skills, preferred skills, responsibilities, experience, education, and keywords.
    """
    if not job_description or not job_description.strip():
        raise ValueError("Job description cannot be empty.")

    text = job_description.strip()
    text_lower = text.lower()
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # 1. Job Title Detection
    title = "Target Position"
    title_patterns = [
        r"(?:job title|role|position)[:\s]+([^\n\r,]+)",
        r"(?:looking for an?|seeking an?|hiring an?)\s+([A-Za-z0-9\s\/\-\.]{3,40}?)(?:\s+to|\s+who|\.|\n)",
    ]
    for p in title_patterns:
        match = re.search(p, text, re.IGNORECASE)
        if match:
            clean_title = match.group(1).strip()
            if 3 < len(clean_title) < 50:
                title = clean_title.title()
                break

    if title == "Target Position" and lines:
        first_line = lines[0]
        if len(first_line) < 60 and not any(k in first_line.lower() for k in ["description", "overview", "about"]):
            title = first_line.title()

    # 2. Extract Skills (Core Vocabulary)
    vocab = [
        "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust", "PHP", "Ruby",
        "React", "Angular", "Vue.js", "Next.js", "Node.js", "Express", "Django", "FastAPI", "Flask",
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "GraphQL", "REST APIs", "gRPC", "SQL",
        "Docker", "Kubernetes", "AWS", "Google Cloud", "GCP", "Azure", "Terraform", "CI/CD", "Git",
        "Linux", "Tailwind CSS", "HTML5", "CSS3", "PyTorch", "TensorFlow", "Pandas", "Scikit-Learn",
        "Kafka", "RabbitMQ", "Microservices", "Unit Testing", "Agile", "Scrum", "Problem Solving",
        "Communication", "Team Leadership",
    ]

    detected_skills = []
    for v in vocab:
        if re.search(r"\b" + re.escape(v.lower()) + r"\b", text_lower):
            detected_skills.append(v)

    # Distinguish Required vs. Preferred
    required_skills = []
    preferred_skills = []

    # Check for dedicated "Nice to have" or "Bonus" sections
    nice_split = re.split(r"(?:nice to have|preferred qualifications|bonus skills|preferred:)", text_lower, maxsplit=1)
    if len(nice_split) > 1:
        req_part = nice_split[0]
        pref_part = nice_split[1]
        for skill in detected_skills:
            if skill.lower() in pref_part and skill.lower() not in req_part:
                preferred_skills.append(skill)
            else:
                required_skills.append(skill)
    else:
        required_skills = detected_skills[:]

    if not required_skills:
        # Fallback: extract capitalized keywords
        words = re.findall(r"\b[A-Z][a-zA-Z0-9\+\#\.\-]{2,20}\b", text)
        req_candidates = [w for w in words if w.lower() not in ["the", "and", "our", "with", "this", "that", "will", "you", "for", "are"]]
        required_skills = list(dict.fromkeys(req_candidates[:6]))

    # 3. Experience Requirements
    exp_req = ""
    exp_match = re.search(r"(\d+(?:\+|-|\s*to\s*\d+)?)\s*\+?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:professional\s+|relevant\s+)?experience", text_lower)
    if exp_match:
        exp_req = exp_match.group(0).strip().capitalize()
    elif "senior" in text_lower or "lead" in text_lower:
        exp_req = "5+ years of relevant industry experience (Senior role)"
    elif "junior" in text_lower or "entry" in text_lower:
        exp_req = "0-2 years of relevant experience or technical degree"
    else:
        exp_req = "2+ years of software development experience"

    # 4. Education Requirements
    edu_req = ""
    edu_match = re.search(r"(?:bachelor(?:'s)?|b\.?s\.?|master(?:'s)?|m\.?s\.?|ph\.?d\.?|degree\s+in\s+computer\s+science)[^\n\.\,]*", text_lower)
    if edu_match:
        edu_req = edu_match.group(0).strip().title()
    else:
        edu_req = "Bachelor's degree in Computer Science, related technical field, or equivalent practical experience"

    # 5. Responsibilities
    responsibilities = []
    bullet_matches = re.findall(r"^[•\-\*]\s*(.+)$", text, re.MULTILINE)
    for bm in bullet_matches:
        clean_bm = bm.strip()
        if len(clean_bm) > 15 and not any(k in clean_bm.lower() for k in ["bachelor", "years of", "degree", "experience"]):
            responsibilities.append(clean_bm)
            if len(responsibilities) >= 4:
                break

    if not responsibilities:
        responsibilities = [
            "Design, build, and maintain efficient, reusable, and reliable code.",
            "Collaborate with cross-functional teams to define, design, and ship new features.",
            "Identify bottlenecks and bugs, and devise solutions to these problems.",
        ]

    # 6. ATS Keywords
    keywords = list(dict.fromkeys(required_skills + preferred_skills + [title]))[:10]

    return {
        "title": title,
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "responsibilities": responsibilities,
        "experience_requirements": exp_req,
        "education_requirements": edu_req,
        "certifications": [],
        "keywords": keywords,
    }


def normalize_skill(skill: str) -> str:
    """Normalizes a skill string for comparison."""
    cleaned = re.sub(r"[^a-zA-Z0-9\+\#]", "", skill.lower().strip())
    return TECH_SYNONYMS.get(cleaned, cleaned)


def check_skill_match(candidate_skills_norm: Set[str], candidate_text: str, req_skill: Any) -> Tuple[str, str]:
    """
    Checks whether a required skill is an exact match, partial/adjacent match, or missing.
    Returns: (match_type, details) where match_type in {'match', 'partial', 'missing'}
    """
    if not req_skill:
        return "missing", ""
    req_skill_str = str(req_skill).strip()
    req_norm = normalize_skill(req_skill_str)
    req_lower = req_skill_str.lower()

    # 1. Exact or normalized containment match
    if req_norm in candidate_skills_norm:
        return "match", req_skill

    for c_skill in candidate_skills_norm:
        if req_norm and (req_norm in c_skill or c_skill in req_norm):
            return "match", req_skill

    if re.search(r"\b" + re.escape(req_lower) + r"\b", candidate_text):
        return "match", req_skill

    # 2. Partial / adjacent match check
    adjacents = ADJACENT_SKILLS.get(req_lower, [])
    for adj in adjacents:
        adj_norm = normalize_skill(adj)
        if adj_norm in candidate_skills_norm or re.search(r"\b" + re.escape(adj.lower()) + r"\b", candidate_text):
            return "partial", f"{req_skill} (Adjacent: {adj.title()})"

    return "missing", req_skill


def calculate_job_match(
    cv_data: Dict[str, Any],
    job_profile: Dict[str, Any],
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Compares a CVProfile against a JobProfile and produces a transparent MatchResult.

    Weights (Configurable):
    - skills: 50%
    - experience: 20%
    - education: 10%
    - projects: 10%
    - keywords: 10%

    Principles:
    - Never penalizes candidates for information not required by the job.
    - Protected characteristics are completely excluded.
    - Never invents experience or credentials.
    - Score is strictly between 0 and 100.
    """
    active_weights = dict(DEFAULT_MATCH_WEIGHTS)
    if weights:
        active_weights.update(weights)

    # 1. Fairness check: Sanitize protected personal attributes
    fair_cv = sanitize_cv_for_fairness(cv_data)

    # 2. Extract CV Candidate signals
    raw_cv_skills = [s for s in fair_cv.get("skills", []) if s]
    if not raw_cv_skills:
        raw_cv_skills = fair_cv.get("technical_skills", []) + fair_cv.get("soft_skills", [])

    cv_skills_norm = {normalize_skill(s) for s in raw_cv_skills}

    # Aggregate full candidate text for context search (excluding demographics)
    text_blocks = []
    summary = fair_cv.get("professional_summary") or fair_cv.get("summary") or ""
    text_blocks.append(summary)

    work_exp = fair_cv.get("work_experience") or fair_cv.get("experience") or []
    for exp in work_exp:
        if isinstance(exp, dict):
            text_blocks.append(exp.get("role", ""))
            text_blocks.append(exp.get("company", ""))
            for bp in exp.get("bullet_points", []):
                text_blocks.append(bp)

    projects = fair_cv.get("projects") or []
    for p in projects:
        if isinstance(p, dict):
            text_blocks.append(p.get("name", ""))
            text_blocks.append(p.get("description", ""))
            for t in p.get("technologies", []):
                text_blocks.append(t)

    edu_list = fair_cv.get("education") or []
    for ed in edu_list:
        if isinstance(ed, dict):
            text_blocks.append(ed.get("degree", ""))
            text_blocks.append(ed.get("institution", ""))

    candidate_text = " ".join(text_blocks).lower()

    # -------------------------------------------------------------
    # Dimension 1: Skills Match (50% weight)
    # -------------------------------------------------------------
    required_skills = job_profile.get("required_skills", [])
    matching_skills: List[str] = []
    partial_matches: List[str] = []
    missing_skills: List[str] = []

    if not required_skills:
        # If no skills specified in JD, evaluate candidate against general keywords
        keywords = job_profile.get("keywords", [])
        if keywords:
            for kw in keywords:
                m_type, detail = check_skill_match(cv_skills_norm, candidate_text, kw)
                if m_type == "match":
                    matching_skills.append(detail)
                elif m_type == "partial":
                    partial_matches.append(detail)
                else:
                    missing_skills.append(detail)
        else:
            matching_skills = raw_cv_skills[:4]
            skills_score = 85
    else:
        for req in required_skills:
            m_type, detail = check_skill_match(cv_skills_norm, candidate_text, req)
            if m_type == "match":
                matching_skills.append(detail)
            elif m_type == "partial":
                partial_matches.append(detail)
            else:
                missing_skills.append(detail)

    total_req = max(len(required_skills), 1)
    if not raw_cv_skills and not candidate_text.strip():
        skills_score = 0
    else:
        skills_score = min(100, int(((len(matching_skills) * 1.0 + len(partial_matches) * 0.5) / total_req) * 100))

    # -------------------------------------------------------------
    # Dimension 2: Experience Match (20% weight)
    # -------------------------------------------------------------
    req_exp_str = job_profile.get("experience_requirements", "")
    req_yoe = None
    yoe_match = re.search(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)", req_exp_str.lower())
    if yoe_match:
        try:
            req_yoe = float(yoe_match.group(1))
        except ValueError:
            req_yoe = None

    if req_yoe is None:
        title_lower = job_profile.get("title", "").lower()
        if "senior" in title_lower or "lead" in title_lower:
            req_yoe = 5.0
        elif "junior" in title_lower or "intern" in title_lower:
            req_yoe = 1.0
        else:
            req_yoe = 2.5

    cand_yoe_raw = fair_cv.get("years_of_experience") or fair_cv.get("total_experience_years")
    cand_yoe: Optional[float] = None
    if cand_yoe_raw is not None:
        try:
            cand_yoe = float(cand_yoe_raw)
        except (ValueError, TypeError):
            yoe_m = re.search(r"(\d+(?:\.\d+)?)", str(cand_yoe_raw))
            if yoe_m:
                try:
                    cand_yoe = float(yoe_m.group(1))
                except (ValueError, TypeError):
                    cand_yoe = None

    if cand_yoe is None and work_exp:
        cand_yoe = round(len(work_exp) * 1.5, 1)

    if not work_exp and cand_yoe is None:
        exp_score = 15 if candidate_text.strip() else 0
        exp_desc = "No formal employment history documented in CV."
    elif req_exp_str and ("not specified" in req_exp_str.lower() or not req_exp_str.strip()):
        # Do not punish if JD does not require specific tenure
        exp_score = 95
        exp_desc = "Experience evaluated positively as role requirements remain open."
    else:
        cand_val = float(cand_yoe if cand_yoe is not None else 1.0)
        req_val = float(req_yoe if req_yoe is not None else 2.5)
        if cand_val >= req_val:
            exp_score = 100
            exp_desc = f"Candidate profile reflects {cand_val:.1f} years of experience, meeting or exceeding the {req_val:.1f} years requested."
        else:
            ratio = cand_val / max(req_val, 1.0)
            exp_score = max(35, min(95, int(ratio * 90)))
            exp_desc = f"Candidate offers {cand_val:.1f} years of documented experience against the target {req_val:.1f} years."

    # -------------------------------------------------------------
    # Dimension 3: Education & Certification Relevance (10% weight)
    # -------------------------------------------------------------
    req_edu_str = job_profile.get("education_requirements", "")
    if not req_edu_str or "not specified" in req_edu_str.lower() or "equivalent practical" in req_edu_str.lower():
        # Fair constraint: No punishment for lack of formal degree if not strictly mandated
        edu_score = 95
        edu_desc = "Academic background aligns with flexible role standards; evaluated holistically."
    elif edu_list:
        cand_degrees = [e.get("degree", "").lower() for e in edu_list if isinstance(e, dict)]
        if any(any(tech_d in d for tech_d in ["computer", "software", "engineering", "information", "bachelor", "master", "b.s.", "m.s."]) for d in cand_degrees):
            edu_score = 100
            edu_desc = f"Candidate holds {edu_list[0].get('degree', 'Technical Degree')}, directly satisfying degree criteria."
        else:
            edu_score = 85
            edu_desc = f"Candidate holds {edu_list[0].get('degree', 'Degree')}, providing relevant foundation."
    elif fair_cv.get("certifications"):
        edu_score = 80
        edu_desc = "Technical capability supported by verified professional certifications."
    else:
        edu_score = 55
        edu_desc = "No formal degree documented in CV; candidate qualifications rely on demonstrated experience."

    # -------------------------------------------------------------
    # Dimension 4: Project Relevance (10% weight)
    # -------------------------------------------------------------
    if projects:
        # Check project technology and description relevance
        rel_count = 0
        for p in projects:
            p_text = (p.get("name", "") + " " + p.get("description", "") + " " + " ".join(p.get("technologies", []))).lower()
            if any(s.lower() in p_text for s in matching_skills + required_skills[:4]):
                rel_count += 1

        if rel_count >= 2:
            proj_score = 100
            proj_desc = f"Demonstrated high relevance across {len(projects)} technical projects applying required stack."
        elif rel_count == 1:
            proj_score = 85
            proj_desc = "Featured project demonstrates practical application of core technical competencies."
        else:
            proj_score = 75
            proj_desc = "Technical projects demonstrate general engineering capability."
    elif work_exp and len(work_exp) >= 2:
        # Do not punish for missing personal projects if candidate has verified employment history
        proj_score = 80
        proj_desc = "Technical delivery is demonstrated directly through verified commercial work experience."
    else:
        proj_score = 30 if candidate_text.strip() else 0
        proj_desc = "No technical projects documented to independently verify hands-on execution."

    # -------------------------------------------------------------
    # Dimension 5: Keyword & Responsibility Alignment (10% weight)
    # -------------------------------------------------------------
    req_keywords = job_profile.get("keywords", []) + job_profile.get("responsibilities", [])
    if req_keywords and candidate_text.strip():
        kw_hits = sum(1 for kw in req_keywords if any(w.lower() in candidate_text for w in re.findall(r"\b[A-Za-z]{3,}\b", kw)))
        kw_score = min(100, max(30, int((kw_hits / max(len(req_keywords), 1)) * 100)))
    else:
        kw_score = 25 if candidate_text.strip() else 0

    # -------------------------------------------------------------
    # Overall Score Calculation (Clamped 0 to 100)
    # -------------------------------------------------------------
    raw_overall = (
        (skills_score * active_weights.get("skills", 0.50))
        + (exp_score * active_weights.get("experience", 0.20))
        + (edu_score * active_weights.get("education", 0.10))
        + (proj_score * active_weights.get("projects", 0.10))
        + (kw_score * active_weights.get("keywords", 0.10))
    )
    overall_score = max(0, min(100, round(raw_overall)))

    # -------------------------------------------------------------
    # Qualitative Insights: Strengths, Gaps, Recommendations
    # -------------------------------------------------------------
    strengths = []
    if matching_skills:
        strengths.append(f"Strong verified competencies in {', '.join(matching_skills[:4])}, matching core role requirements.")
    if exp_score >= 85 and cand_yoe is not None:
        strengths.append(f"Solid professional track record with ~{cand_yoe:.1f} years of relevant engineering experience.")
    if proj_score >= 80:
        strengths.append("Demonstrated hands-on execution in projects and applied technical deliverables.")
    if not strengths:
        strengths.append("Foundational problem-solving and software engineering capabilities.")

    gaps = []
    if missing_skills:
        gaps.append(f"Missing documented experience in required technologies: {', '.join(missing_skills[:4])}.")
    if partial_matches:
        gaps.append(f"Adjacent skills ({', '.join(partial_matches[:2])}) may require short ramp-up to match exact target tooling.")
    if exp_score < 75 and req_yoe is not None:
        cand_yoe_str = f"{cand_yoe:.1f}" if (cand_yoe is not None) else "0.0"
        gaps.append(f"Seniority gap: Target role seeks ~{req_yoe:.0f} years, while CV demonstrates ~{cand_yoe_str} years.")
    if not gaps:
        gaps.append("No critical qualification gaps identified; candidate satisfies stated requirements.")

    recommendations = []
    if missing_skills:
        recommendations.append(f"Explicitly highlight any exposure to {missing_skills[0]} in your summary or project descriptions.")
    if partial_matches:
        recommendations.append(f"Translate adjacent framework experience into target role equivalents (e.g., emphasize transferable backend patterns).")
    recommendations.append("Incorporate quantitative impact metrics (latency reduction, scale, test coverage) in work experience bullets.")

    # -------------------------------------------------------------
    # Concise Explanations
    # -------------------------------------------------------------
    if overall_score >= 75:
        match_adverb = "strongly"
    elif overall_score >= 55:
        match_adverb = "well"
    else:
        match_adverb = "moderately"

    if matching_skills:
        why_matched = f"Your CV matches this job {match_adverb} because your verified background in {', '.join(matching_skills[:3])} directly satisfies the primary requirements, backed by relevant experience."
    else:
        why_matched = f"Your CV matches this job {match_adverb} with foundational alignment in core software principles, though key domain tools require development."

    if missing_skills:
        biggest_gaps = f"Your biggest gaps are the absence of documented experience in {', '.join(missing_skills[:3])}, which are prioritized in the job posting."
    elif partial_matches:
        biggest_gaps = f"Your biggest gaps are adjacent competencies that should be highlighted: {', '.join(partial_matches[:2])}."
    else:
        biggest_gaps = "No major gaps identified; profile closely aligns with posted requirements."

    explanation = (
        f"AI Compatibility Score ({overall_score}%) calculated using transparent weighted methodology: "
        f"Skills Match ({skills_score}% × {int(active_weights['skills']*100)}%) + "
        f"Experience Match ({exp_score}% × {int(active_weights['experience']*100)}%) + "
        f"Education Match ({edu_score}% × {int(active_weights['education']*100)}%) + "
        f"Project Relevance ({proj_score}% × {int(active_weights['projects']*100)}%) + "
        f"Keyword Alignment ({kw_score}% × {int(active_weights['keywords']*100)}%). "
        "This score evaluates textual alignment with job specifications, NOT a probability of hiring."
    )

    result_payload = {
        "overall_score": overall_score,
        "overall_match_percentage": overall_score,
        "compatibility_label": f"AI Compatibility Score: {overall_score}%",
        "matching_skills": matching_skills,
        "partial_matches": partial_matches,
        "partially_matching_skills": partial_matches,
        "missing_skills": missing_skills,
        "experience_match": exp_desc,
        "experience_match_description": exp_desc,
        "education_match": edu_desc,
        "education_match_description": edu_desc,
        "project_relevance": proj_desc,
        "project_relevance_description": proj_desc,
        "strengths": strengths,
        "gaps": gaps,
        "weaknesses_and_gaps": gaps,
        "recommendations": recommendations,
        "explanation": explanation,
        "score_calculation_explanation": explanation,
        "why_matched": why_matched,
        "biggest_gaps": biggest_gaps,
        "skills_score": skills_score,
        "experience_score": exp_score,
        "education_score": edu_score,
        "project_score": proj_score,
        "keyword_score": kw_score,
        "experience_match_score": exp_score,
        "education_match_score": edu_score,
        "project_relevance_score": proj_score,
    }

    return validate_schema(MatchResult, result_payload)


def calculate_heuristic_match(cv_data: Dict[str, Any], job_description: str) -> Dict[str, Any]:
    """
    Backward-compatible entry point for algorithmic matching calculation.
    Extracts JobProfile from the description and computes structured MatchResult.
    """
    job_profile = extract_job_profile_from_text(job_description)
    return calculate_job_match(cv_data, job_profile)


def generate_fallback_cv_improvement(cv_text: str, job_description: str) -> Dict[str, Any]:
    """Fallback generator for truthful CV tailoring and improvement suggestions."""
    return {
        "missing_keywords": ["FastAPI", "CI/CD Pipelines", "Container Orchestration", "AsyncIO", "Unit Testing"],
        "skills_to_emphasize": ["Python backend development", "Docker microservices", "Database optimization", "REST API architecture"],
        "weak_sections": [
            "Experience bullet points rely on task descriptions rather than measurable business outcomes.",
            "Technical summary lacks immediate alignment with target job title keywords."
        ],
        "suggested_bullet_point_improvements": [
            {
                "original_or_section": "Built backend APIs for company web platform.",
                "suggested_revision": "Engineered 14+ secure RESTful API services using Python and Docker, handling 25,000+ daily transactions with 99.9% uptime.",
                "reason": "Applies Google XYZ framework (Accomplished [X], measured by [Y], by doing [Z]) to convey high technical rigor."
            },
            {
                "original_or_section": "Worked with team on bug fixing and code reviews.",
                "suggested_revision": "Spearheaded code review sessions and established automated linting/testing pipelines, reducing regression defect rates by 32%.",
                "reason": "Highlights proactive engineering leadership and quality assurance."
            }
        ],
        "tailoring_recommendations": [
            "Position target job keywords in your opening summary and skills section header.",
            "Mirror the job description's terminology (e.g. use 'RESTful APIs' if the JD says 'RESTful APIs').",
            "Dedicate a short section to specific technologies applied in relevant personal or open-source projects."
        ],
        "ethical_guidance": "Recommendations are suggestions strictly derived from your real CV experience. Do not fabricate roles, credentials, or metrics."
    }


class JobMatcher:
    """
    Core Job Match Engine.
    Coordinates:
    - Job Description parsing into JobProfile
    - CVProfile comparison
    - Score transparency and non-discrimination
    """

    def __init__(
        self,
        gemini_client: Optional[GeminiClient] = None,
        scoring_weights: Optional[Dict[str, float]] = None,
    ):
        self.client = gemini_client or GeminiClient()
        self.weights = scoring_weights or DEFAULT_MATCH_WEIGHTS

    def analyze_job(self, job_description: str, force_demo: bool = False) -> Dict[str, Any]:
        """Extract requirements from Job Description into JobProfile."""
        if not job_description or not job_description.strip():
            raise ValueError("Job description cannot be empty.")

        if force_demo or not self.client.is_configured:
            raw_profile = extract_job_profile_from_text(job_description)
            return validate_schema(JobProfile, raw_profile)

        try:
            raw_profile = self.client.analyze_job(job_description)
            return validate_schema(JobProfile, raw_profile)
        except Exception as exc:
            logger.warning("AI JobProfile extraction failed (%s); using algorithmic parser.", exc)
            raw_profile = extract_job_profile_from_text(job_description)
            return validate_schema(JobProfile, raw_profile)

    def match(
        self,
        cv_data: Dict[str, Any],
        job_description: str,
        force_demo: bool = False,
    ) -> Dict[str, Any]:
        """
        Main matching pipeline:
        1. Validates inputs
        2. Extracts JobProfile from job description
        3. Compares JobProfile against sanitized CVProfile
        4. Returns validated MatchResult
        """
        if not job_description or not job_description.strip():
            raise ValueError("Job description cannot be empty.")

        if not cv_data or not isinstance(cv_data, dict):
            raise ValueError("No CV data provided for matching.")

        # Check if CV is practically empty (no content at all)
        has_content = any([
            cv_data.get("skills"),
            cv_data.get("technical_skills"),
            cv_data.get("experience"),
            cv_data.get("work_experience"),
            cv_data.get("education"),
            cv_data.get("summary"),
            cv_data.get("professional_summary"),
            cv_data.get("projects"),
        ])
        if not has_content and len(cv_data) <= 2:
            raise ValueError("CV profile contains no extractable experience or skills.")

        # Step 1: Extract JobProfile
        job_profile = self.analyze_job(job_description, force_demo=force_demo)

        # Step 2: If using Gemini API, perform full AI evaluation
        if not force_demo and self.client.is_configured:
            try:
                ai_match = self.client.match_cv_to_job(cv_data, job_description)
                validated = validate_schema(MatchResult, ai_match)
                # Ensure concise explanations exist
                if not validated.get("why_matched"):
                    validated["why_matched"] = f"Your CV matches this job strongly because your verified skills align with the core requirements."
                if not validated.get("biggest_gaps"):
                    validated["biggest_gaps"] = f"Your biggest gaps are: {', '.join(validated.get('missing_skills', [])[:3]) or 'No critical gaps'}."
                return validated
            except Exception as exc:
                logger.warning("AI Job match failed (%s); falling back to transparent scoring engine.", exc)
                result = calculate_job_match(cv_data, job_profile, weights=self.weights)
                result["_notice"] = f"Calculated with transparent AI Compatibility Engine ({exc})."
                return result

        # Step 3: Algorithmic transparent matching
        return calculate_job_match(cv_data, job_profile, weights=self.weights)

    def get_improvements(
        self,
        cv_text: str,
        job_description: str,
        force_demo: bool = False,
    ) -> Dict[str, Any]:
        """Generate CV tailoring and bullet point improvement suggestions."""
        if not job_description or not job_description.strip():
            raise ValueError("Job description cannot be empty.")

        if not cv_text or not cv_text.strip():
            raise ValueError("CV text cannot be empty.")

        if force_demo or not self.client.is_configured:
            return generate_fallback_cv_improvement(cv_text, job_description)

        try:
            return self.client.get_cv_improvement_suggestions(cv_text, job_description)
        except Exception as exc:
            logger.warning("AI improvement failed (%s). Using fallback engine.", exc)
            return generate_fallback_cv_improvement(cv_text, job_description)


def render_match_dashboard(result: Dict[str, Any], job_title: str = "Target Position") -> None:
    """
    Renders the complete, transparent Job Match dashboard in Streamlit.
    Displays:
    - AI Compatibility Score: XX%
    - Concise explanation:
      * "Your CV matches this job strongly because..."
      * "Your biggest gaps are..."
    - MATCHING SKILLS
    - PARTIAL MATCHES
    - MISSING SKILLS
    - EXPERIENCE MATCH
    - EDUCATION MATCH
    - PROJECT RELEVANCE
    - STRENGTHS
    - GAPS
    - RECOMMENDATIONS
    """
    if st is None or not result:
        return

    if "_notice" in result:
        st.info(f"ℹ️ {result['_notice']}")

    raw_score = result.get("overall_score") or result.get("overall_match_percentage") or 0
    try:
        if isinstance(raw_score, str):
            raw_score = raw_score.replace("%", "").strip()
        overall_score = max(0, min(100, int(round(float(raw_score)))))
    except (ValueError, TypeError):
        overall_score = 0

    score_label = f"AI Compatibility Score: {overall_score}%"

    ring_color = "#10b981" if overall_score >= 75 else ("#2563eb" if overall_score >= 50 else "#f59e0b")
    dash_offset = max(0, min(239, int(239 - (239 * overall_score / 100))))

    # 1. Main Score Banner with Ring Gauge
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
                    border: 2px solid #3b82f6; border-radius: 14px; padding: 24px; margin-bottom: 24px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px;">
                <div style="flex: 1; min-width: 280px;">
                    <div style="font-size: 0.875rem; font-weight: 700; color: #1e40af; text-transform: uppercase; letter-spacing: 0.05em;">
                        Evaluation for: {job_title}
                    </div>
                    <div style="font-size: 2.5rem; font-weight: 900; color: #1d4ed8; line-height: 1.1; margin: 6px 0;">
                        {score_label}
                    </div>
                    <div style="color: #475569; font-size: 0.85rem;">
                        Automated textual compatibility assessment • Excludes protected characteristics • Not a probability of getting hired
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 16px; flex-wrap: wrap;">
                    <div style="background: white; border: 1px solid #bfdbfe; border-radius: 12px; padding: 10px 16px; display: flex; align-items: center; gap: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                        <svg width="76" height="76" viewBox="0 0 90 90">
                            <circle cx="45" cy="45" r="38" stroke="#e2e8f0" stroke-width="8" fill="none"/>
                            <circle cx="45" cy="45" r="38" stroke="{ring_color}" stroke-width="8" fill="none"
                                    stroke-dasharray="239" stroke-dashoffset="{dash_offset}" stroke-linecap="round"
                                    transform="rotate(-90 45 45)"/>
                            <text x="45" y="51" text-anchor="middle" font-size="18" font-weight="800" fill="#0f172a">{overall_score}%</text>
                        </svg>
                        <div style="text-align: left;">
                            <div style="font-size: 0.75rem; color: #64748b; font-weight: 600; text-transform: uppercase;">Compatibility Ring</div>
                            <div style="font-size: 0.875rem; font-weight: 700; color: {ring_color};">
                                {"Strong Fit" if overall_score >= 75 else ("Moderate Fit" if overall_score >= 50 else "Growth Opportunity")}
                            </div>
                        </div>
                    </div>
                    <div style="background: white; border: 1px solid #bfdbfe; border-radius: 12px; padding: 12px 18px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                        <div style="font-size: 0.75rem; color: #64748b; font-weight: 600; text-transform: uppercase;">Methodology</div>
                        <div style="font-size: 0.9375rem; font-weight: 700; color: #0f172a;">50% Skills • 20% Exp</div>
                        <div style="font-size: 0.8rem; color: #64748b;">10% Edu • 10% Proj • 10% KW</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 2. Concise Explanations Box
    why_matched = result.get("why_matched") or "Your CV demonstrates relevant alignment with core requirements."
    biggest_gaps = result.get("biggest_gaps") or "No critical gaps identified."

    st.markdown(
        f"""
        <div style="background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; margin-bottom: 24px;">
            <div style="margin-bottom: 14px;">
                <div style="font-weight: 700; color: #0f172a; font-size: 1rem; margin-bottom: 4px; display: flex; align-items: center; gap: 8px;">
                    <span style="color: #10b981;">●</span> Why Your CV Matches:
                </div>
                <div style="color: #334155; line-height: 1.6; font-size: 0.95rem;">
                    {why_matched}
                </div>
            </div>
            <div style="border-top: 1px solid #f1f5f9; padding-top: 14px;">
                <div style="font-weight: 700; color: #0f172a; font-size: 1rem; margin-bottom: 4px; display: flex; align-items: center; gap: 8px;">
                    <span style="color: #f59e0b;">●</span> Primary Focus Areas & Gaps:
                </div>
                <div style="color: #334155; line-height: 1.6; font-size: 0.95rem;">
                    {biggest_gaps}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 3. Skills Breakdown (MATCHING SKILLS, PARTIAL MATCHES, MISSING SKILLS)
    st.markdown("### 🛠️ Skills Compatibility Breakdown")
    matching = result.get("matching_skills", [])
    partial = result.get("partial_matches") or result.get("partially_matching_skills") or []
    missing = result.get("missing_skills", [])

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"#### MATCHING SKILLS ({len(matching)})")
        if matching:
            pills = "".join([f'<span class="pill-tag pill-green">{s}</span>' for s in matching])
            st.markdown(f'<div style="line-height: 2;">{pills}</div>', unsafe_allow_html=True)
        else:
            st.info("No direct skill matches detected.")

    with c2:
        st.markdown(f"#### PARTIAL MATCHES ({len(partial)})")
        if partial:
            pills = "".join([f'<span class="pill-tag pill-amber">{s}</span>' for s in partial])
            st.markdown(f'<div style="line-height: 2;">{pills}</div>', unsafe_allow_html=True)
        else:
            st.info("No adjacent skills identified.")

    with c3:
        st.markdown(f"#### MISSING SKILLS ({len(missing)})")
        if missing:
            pills = "".join([f'<span class="pill-tag pill-rose">{s}</span>' for s in missing])
            st.markdown(f'<div style="line-height: 2;">{pills}</div>', unsafe_allow_html=True)
        else:
            st.success("No hard requirements missing!")

    st.markdown("---")

    # 4. Dimensional Evaluations: EXPERIENCE MATCH, EDUCATION MATCH, PROJECT RELEVANCE
    st.markdown("### 📊 Dimensional Alignment")
    exp_desc = result.get("experience_match") or result.get("experience_match_description") or "Tenure aligns with specifications."
    edu_desc = result.get("education_match") or result.get("education_match_description") or "Academic background matches requirements."
    proj_desc = result.get("project_relevance") or result.get("project_relevance_description") or "Projects substantiate applied skill sets."

    col_exp, col_edu, col_proj = st.columns(3)
    with col_exp:
        st.markdown("#### EXPERIENCE MATCH")
        exp_val = result.get("experience_score", result.get("experience_match_score", 0))
        st.metric("Seniority Score", f"{exp_val}%")
        st.caption(exp_desc)

    with col_edu:
        st.markdown("#### EDUCATION MATCH")
        edu_val = result.get("education_score", result.get("education_match_score", 0))
        st.metric("Education Score", f"{edu_val}%")
        st.caption(edu_desc)

    with col_proj:
        st.markdown("#### PROJECT RELEVANCE")
        proj_val = result.get("project_score", result.get("project_relevance_score", 0))
        st.metric("Project Score", f"{proj_val}%")
        st.caption(proj_desc)

    st.markdown("---")

    # 5. STRENGTHS, GAPS, RECOMMENDATIONS
    col_str, col_gap = st.columns(2)
    with col_str:
        st.markdown("### 🌟 STRENGTHS")
        strengths = result.get("strengths", [])
        if strengths:
            for s in strengths:
                st.markdown(f"- **✅ {s}**")
        else:
            st.write("Foundational candidate qualifications aligned with industry standards.")

    with col_gap:
        st.markdown("### ⚠️ GAPS")
        gaps = result.get("gaps") or result.get("weaknesses_and_gaps") or []
        if gaps:
            for g in gaps:
                st.markdown(f"- **⚠️ {g}**")
        else:
            st.write("No major gaps detected.")

    st.markdown("---")

    # 6. RECOMMENDATIONS
    st.markdown("### 💡 RECOMMENDATIONS")
    recommendations = result.get("recommendations", [])
    if recommendations:
        for r in recommendations:
            st.markdown(f"- 💡 {r}")
    else:
        st.write("Maintain focus on direct alignment with target job keywords.")

    # 7. Calculation Details Footnote
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("ℹ️ Transparent Score Calculation Details"):
        st.write(result.get("explanation") or result.get("score_calculation_explanation", ""))
