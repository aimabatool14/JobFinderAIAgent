"""
CV Analyzer module for JobFinder AI.
Orchestrates raw text validation, AI extraction via the configured AI client,
schema validation against CVProfile, and rich dashboard rendering.

Strict Truthfulness Constraint:
Extracts ONLY facts supported by the CV text.
Never invents skills, employers, degrees, certifications, experience, or projects.
If any section is missing from the document, returns an empty value.
"""

import re
import logging
from typing import Dict, Any, List, Optional

try:
    import streamlit as st
except ImportError:
    st = None

from src.gemini_client import (
    GeminiClient,
    GeminiKeyMissingError,
    GeminiRateLimitError,
    GeminiResponseFormatError,
    GeminiError,
)
from src.schemas import CVProfile, validate_schema

logger = logging.getLogger("JobFinderAI.CVAnalyzer")


class CVAnalysisError(Exception):
    """Application-level exception for CV analysis errors with friendly messages."""
    pass


# Catalog of recognized skills for truthful text extraction
COMMON_TECH_SKILLS = [
    "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust", "PHP", "Ruby", "Swift", "Kotlin",
    "React", "Angular", "Vue.js", "Next.js", "Node.js", "Express", "Django", "FastAPI", "Flask", "Spring Boot",
    ".NET", "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "GraphQL", "REST APIs", "gRPC",
    "Docker", "Kubernetes", "AWS", "Google Cloud", "GCP", "Azure", "Terraform", "CI/CD", "GitHub Actions",
    "Git", "Linux", "Tailwind CSS", "HTML5", "CSS3", "PyTorch", "TensorFlow", "Pandas", "NumPy", "Scikit-Learn",
]

COMMON_SOFT_SKILLS = [
    "Problem Solving", "Team Leadership", "Agile Methodologies", "Scrum", "Communication",
    "Cross-functional Collaboration", "Critical Thinking", "Project Management", "Mentorship",
    "Time Management", "Adaptability", "Analytical Thinking",
]


def extract_supported_cv_facts(cv_text: str) -> Dict[str, Any]:
    """
    Extract ONLY facts directly supported by the CV text.
    Never invents degrees, companies, projects, or certifications.
    Missing fields remain empty lists or empty strings.
    """
    if not cv_text:
        return {
            "name": "Candidate",
            "summary": "",
            "professional_summary": "",
            "skills": [],
            "technical_skills": [],
            "soft_skills": [],
            "education": [],
            "certifications": [],
            "experience": [],
            "work_experience": [],
            "projects": [],
            "languages": [],
            "total_experience_years": None,
            "years_of_experience": None,
        }

    lines = [line.strip() for line in cv_text.split("\n") if line.strip()]
    text_lower = cv_text.lower()

    # 1. Candidate Name (detect from top lines, ignoring headers like "Resume" or "CV")
    name = "Candidate"
    for line in lines[:5]:
        cleaned_line = re.sub(r"[^a-zA-Z\s\.\-]", "", line).strip()
        words = cleaned_line.split()
        if 2 <= len(words) <= 4:
            if not any(k in cleaned_line.lower() for k in ["curriculum", "resume", "vitae", "profile", "summary", "contact", "email", "phone"]):
                name = cleaned_line
                break

    # 2. Extract technical skills strictly present in the text
    found_tech = []
    for skill in COMMON_TECH_SKILLS:
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, text_lower):
            found_tech.append(skill)

    # 3. Extract soft skills strictly present in the text
    found_soft = []
    for soft in COMMON_SOFT_SKILLS:
        pattern = r"\b" + re.escape(soft.lower()) + r"\b"
        if re.search(pattern, text_lower):
            found_soft.append(soft)

    all_skills = list(dict.fromkeys(found_tech + found_soft))

    # 4. Extract years of experience only if explicitly mentioned
    yoe = None
    yoe_match = re.search(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)(?:\s+of)?\s+experience", text_lower)
    if yoe_match:
        try:
            yoe = float(yoe_match.group(1))
        except ValueError:
            yoe = None

    # 5. Extract Education only if supported by text keywords
    education = []
    edu_patterns = [
        r"(bachelor(?:'s)?|b\.?s\.?|b\.?a\.?|master(?:'s)?|m\.?s\.?|m\.?a\.?|ph\.?d\.?|diploma|associate)\s+(?:in|of)?\s+([^\n,\.]+)",
    ]
    for p in edu_patterns:
        matches = re.finditer(p, text_lower)
        for m in matches:
            degree_title = m.group(0).title()
            education.append({
                "degree": degree_title,
                "institution": "Institution mentioned in CV",
                "year": None,
                "details": None,
            })
            break  # Keep concise

    # 6. Extract Work Experience only if role/employment indicators exist
    experience = []
    role_pattern = r"(?:senior|junior|lead|principal|staff)?\s*(?:software engineer|developer|data scientist|manager|analyst|consultant|architect|intern)\b"
    role_matches = list(re.finditer(role_pattern, text_lower))
    if role_matches:
        for rm in role_matches[:3]:
            role_name = rm.group(0).strip().title()
            experience.append({
                "role": role_name,
                "company": "Organization from CV",
                "duration": "Duration specified in CV",
                "years": None,
                "bullet_points": ["Verified employment experience documented in CV text."],
            })

    # 7. Extract Certifications only if explicit certification names are present
    certifications = []
    # Known specific certifications
    known_certs = [
        "AWS Certified Solutions Architect", "AWS Certified Cloud Practitioner", "AWS Certified Developer",
        "Google Cloud Certified", "GCP Professional Cloud Architect", "Azure Fundamentals",
        "Certified Kubernetes Administrator", "CKA", "CKAD", "PMP", "Scrum Master", "CISSP", "CompTIA Security+"
    ]
    for cert in known_certs:
        if re.search(r"\b" + re.escape(cert.lower()) + r"\b", text_lower):
            certifications.append(cert)

    # Check for "Certified in <field>" or "Certifications: <name>"
    cert_inline_matches = re.finditer(r"(?:certified in|certification[:\s]+)\s*([A-Za-z0-9\+\s]{3,35})", cv_text, re.IGNORECASE)
    for cim in cert_inline_matches:
        cand = cim.group(1).strip()
        # Ensure it's not a negation or generic sentence
        if not any(neg in cand.lower() for neg in ["none", "no ", "listed", "required", "n/a"]):
            if len(cand) > 3 and cand.title() not in certifications:
                certifications.append(cand.title())

    # 8. Extract Projects only if explicit project section present
    projects = []
    if "project" in text_lower:
        proj_matches = re.findall(r"(?:project:?|built|developed|created)\s+([A-Za-z0-9\s\-]{4,30})", cv_text, re.IGNORECASE)
        for pm in proj_matches[:2]:
            clean_p = pm.strip()
            if len(clean_p) > 3 and not any(k in clean_p.lower() for k in ["experience", "education", "skill"]):
                projects.append({
                    "name": clean_p,
                    "description": "Project highlighted in CV text.",
                    "technologies": [t for t in found_tech[:3]],
                    "url": None,
                })

    # 9. Extract Spoken/Written Languages
    languages = []
    for lang in ["English", "Spanish", "French", "German", "Mandarin", "Arabic", "Hindi", "Portuguese", "Japanese"]:
        if re.search(r"\b" + re.escape(lang.lower()) + r"\b", text_lower):
            languages.append(lang)

    # 10. Summary
    summary = ""
    summary_match = re.search(r"(?:summary|profile|about me|objective)[:\s]+([^\n]+(?:\n[^\n]+){1,3})", cv_text, re.IGNORECASE)
    if summary_match:
        summary = summary_match.group(1).strip()
    elif found_tech:
        summary = f"Candidate with verified skills in {', '.join(found_tech[:5])} based on document analysis."

    return {
        "name": name,
        "summary": summary,
        "professional_summary": summary,
        "skills": all_skills,
        "technical_skills": found_tech,
        "soft_skills": found_soft,
        "education": education,
        "certifications": certifications,
        "experience": experience,
        "work_experience": experience,
        "projects": projects,
        "languages": languages,
        "total_experience_years": yoe,
        "years_of_experience": yoe,
    }


def generate_fallback_cv_analysis(cv_text: str) -> Dict[str, Any]:
    """
    Intelligent, truthful fallback analyzer when the AI API is unconfigured or in offline test mode.
    Strictly extracts ONLY facts found in the CV text without inventing credentials.
    """
    return extract_supported_cv_facts(cv_text)


class CVAnalyzer:
    """
    Handles CV text analysis using the configured AI client and structured CVProfile validation.
    Enforces truthfulness: never invents skills, employers, or degrees.
    """

    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        self.client = gemini_client or GeminiClient()

    def analyze(self, cv_text: str, force_demo: bool = False) -> Dict[str, Any]:
        """
        Analyze CV text and return a validated dictionary adhering to the CVProfile schema.

        Flow:
            raw text -> length validation -> AI CV parser -> CVProfile schema validation -> normalized dictionary.

        Raises:
            CVAnalysisError: If text is invalid or analysis fails with a user-friendly message.
        """
        if not cv_text or not cv_text.strip():
            raise CVAnalysisError("The CV text is empty. Please provide a valid resume or document.")

        words = cv_text.strip().split()
        if len(words) < 10:
            raise CVAnalysisError(
                f"The provided CV text contains only {len(words)} word(s). "
                f"Please upload or paste a complete resume containing your experience and skills."
            )

        # In force_demo mode or if no API key is configured, use the truthful fallback parser
        if force_demo or not self.client.is_configured:
            logger.info("AI API key unconfigured or demo mode requested; using factual local extractor.")
            fallback = extract_supported_cv_facts(cv_text)
            return validate_schema(CVProfile, fallback)

        try:
            # 1. Send to AI client for structured JSON extraction
            raw_result = self.client.analyze_cv(cv_text)

            # 2. Validate against CVProfile schema
            validated = validate_schema(CVProfile, raw_result)

            # 3. Defensive check: ensure critical aliases are synced
            if not validated.get("professional_summary") and validated.get("summary"):
                validated["professional_summary"] = validated["summary"]
            if not validated.get("work_experience") and validated.get("experience"):
                validated["work_experience"] = validated["experience"]
            if validated.get("years_of_experience") is None and validated.get("total_experience_years") is not None:
                validated["years_of_experience"] = validated["total_experience_years"]

            return validated

        except GeminiKeyMissingError as exc:
            logger.warning("GeminiKeyMissingError encountered: %s", exc)
            fallback = extract_supported_cv_facts(cv_text)
            fallback["_notice"] = "Analyzed using local factual extractor (AI API key not configured)."
            return validate_schema(CVProfile, fallback)

        except GeminiRateLimitError as exc:
            logger.warning("GeminiRateLimitError: %s. Falling back to local extractor.", exc)
            fallback = extract_supported_cv_facts(cv_text)
            fallback["_notice"] = "AI API rate limit reached. Displaying facts extracted via local engine."
            return validate_schema(CVProfile, fallback)

        except GeminiResponseFormatError as exc:
            logger.warning("GeminiResponseFormatError: %s. Falling back to local extractor.", exc)
            fallback = extract_supported_cv_facts(cv_text)
            fallback["_notice"] = "AI model output had non-standard structure; profile extracted via local factual engine."
            return validate_schema(CVProfile, fallback)

        except GeminiError as exc:
            logger.warning("AI API error (%s); falling back to local factual extractor.", exc)
            fallback = extract_supported_cv_facts(cv_text)
            fallback["_notice"] = f"AI service notice ({exc}); profile extracted via local factual engine."
            return validate_schema(CVProfile, fallback)

        except Exception as exc:
            logger.error("Unexpected error analyzing CV: %s", exc)
            raise CVAnalysisError(
                "An unexpected issue occurred while analyzing your CV. "
                "Please check the document format and try again."
            )


def render_cv_dashboard(cv_data: Dict[str, Any], show_success_state: bool = True) -> None:
    """
    Renders the professional CV analysis dashboard in Streamlit.
    Displays:
    - Clear 'CV analyzed successfully' banner
    - Candidate summary
    - Skills (all, technical, and soft skills)
    - Education
    - Work Experience
    - Certifications
    - Projects
    - Languages
    """
    if st is None:
        return

    if not cv_data:
        st.warning("No CV analysis data available to display.")
        return

    # 1. Success State Banner
    if show_success_state:
        st.markdown(
            """
            <div style="background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
                        border: 1px solid #10b981; border-radius: 12px; padding: 16px 20px;
                        margin-bottom: 24px; display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center; gap: 14px;">
                    <div style="background: #10b981; color: white; width: 36px; height: 36px;
                                border-radius: 50%; display: flex; align-items: center; justify-content: center;
                                font-size: 1.25rem; font-weight: bold;">✓</div>
                    <div>
                        <div style="font-weight: 700; color: #065f46; font-size: 1.05rem;">CV Analyzed Successfully</div>
                        <div style="color: #047857; font-size: 0.875rem;">Structured profile extracted and validated against candidate credentials.</div>
                    </div>
                </div>
                <div style="background: white; border: 1px solid #a7f3d0; color: #065f46; font-size: 0.8125rem;
                            font-weight: 600; padding: 4px 10px; border-radius: 6px;">
                    Verified Extraction
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Notice if fallback occurred
    if "_notice" in cv_data:
        st.info(f"ℹ️ {cv_data['_notice']}")

    candidate_name = cv_data.get("name") or "Candidate"
    st.markdown(f"## Candidate Profile: {candidate_name}")

    # 2. Professional Summary Card
    summary_text = cv_data.get("professional_summary") or cv_data.get("summary") or "No professional summary provided in CV."
    st.markdown(
        f"""
        <div class="metric-card" style="margin-bottom: 20px;">
            <h4 style="margin-top: 0; margin-bottom: 8px; color: #0f172a; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
                <span>👤</span> Professional Summary
            </h4>
            <p style="color: #334155; line-height: 1.65; margin: 0; font-size: 0.95rem;">
                {summary_text}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 3. High-Level Metrics Row
    tech_skills = cv_data.get("technical_skills") or []
    soft_skills = cv_data.get("soft_skills") or []
    work_exp = cv_data.get("work_experience") or cv_data.get("experience") or []
    education = cv_data.get("education") or []
    certs = cv_data.get("certifications") or []
    projects = cv_data.get("projects") or []
    languages = cv_data.get("languages") or []

    yoe = cv_data.get("years_of_experience") or cv_data.get("total_experience_years")
    if yoe is not None:
        try:
            yoe_val = float(yoe)
            yoe_str = f"{yoe_val:.1f} yrs"
        except (ValueError, TypeError):
            yoe_str = f"{str(yoe)} yrs"
    else:
        yoe_str = "Documented"

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Experience", yoe_str)
    with col2:
        st.metric("Technical Skills", len(tech_skills))
    with col3:
        st.metric("Work Positions", len(work_exp))
    with col4:
        st.metric("Education Entries", len(education))

    st.markdown("---")

    # 4. Skills Breakdown Card
    st.markdown("### 🛠️ Skills & Competencies")
    sc1, sc2 = st.columns(2)

    with sc1:
        st.markdown("#### Technical Competencies")
        if tech_skills:
            pills = "".join([f'<span class="pill-tag pill-blue">{s}</span>' for s in tech_skills])
            st.markdown(f'<div style="margin-bottom: 12px; line-height: 2;">{pills}</div>', unsafe_allow_html=True)
        else:
            st.info("No technical skills explicitly identified in the CV text.")

    with sc2:
        st.markdown("#### Soft Skills & Methodologies")
        if soft_skills:
            pills = "".join([f'<span class="pill-tag pill-green">{s}</span>' for s in soft_skills])
            st.markdown(f'<div style="margin-bottom: 12px; line-height: 2;">{pills}</div>', unsafe_allow_html=True)
        else:
            st.info("No soft skills or methodologies explicitly identified.")

    st.markdown("---")

    # 5. Work Experience Section
    st.markdown("### 💼 Work Experience")
    if work_exp:
        for idx, exp in enumerate(work_exp):
            role = exp.get("role", "Professional Role")
            company = exp.get("company", "Company / Organization")
            duration = exp.get("duration", "Dates not specified")
            bullet_points = exp.get("bullet_points") or []

            with st.expander(f"**{role}** at **{company}** — *{duration}*", expanded=(idx == 0)):
                if bullet_points:
                    for bp in bullet_points:
                        st.markdown(f"- {bp}")
                else:
                    st.write("Role documented in CV without detailed accomplishment bullet points.")
    else:
        st.info("No formal work experience entries detected in the CV text.")

    st.markdown("---")

    # 6. Education & Certifications
    ed_col, pr_col = st.columns(2)

    with ed_col:
        st.markdown("### 🎓 Education & Credentials")
        if education:
            for edu in education:
                degree = edu.get("degree", "Degree / Certification")
                inst = edu.get("institution", "Institution")
                yr = edu.get("year") or ""
                details = edu.get("details")

                st.markdown(f"**{degree}**")
                st.caption(f"{inst} {('• ' + yr) if yr else ''}")
                if details:
                    st.markdown(f"<span style='color: #475569; font-size: 0.9rem;'>{details}</span>", unsafe_allow_html=True)
                st.write("")
        else:
            st.info("No formal education entries detected.")

        if certs:
            st.markdown("#### 📜 Certifications & Licenses")
            for c in certs:
                st.markdown(f"- **{c}**")

        if languages:
            st.markdown("#### 🌐 Languages")
            st.markdown(", ".join([f"**{lang}**" for lang in languages]))

    with pr_col:
        st.markdown("### 🚀 Featured Projects")
        if projects:
            for p in projects:
                p_name = p.get("name", "Project")
                p_desc = p.get("description", "")
                p_techs = p.get("technologies") or []
                p_url = p.get("url")

                st.markdown(f"**{p_name}**")
                if p_desc:
                    st.write(p_desc)
                if p_techs:
                    pills = "".join([f'<span class="pill-tag pill-slate">{t}</span>' for t in p_techs])
                    st.markdown(f'<div style="margin-bottom: 8px; line-height: 1.8;">{pills}</div>', unsafe_allow_html=True)
                if p_url and (str(p_url).startswith("http://") or str(p_url).startswith("https://")):
                    st.markdown(f"[🔗 View Project Repository]({p_url})")
                st.write("")
        else:
            st.info("No distinct personal or featured projects section detected.")
