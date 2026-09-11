"""
JobFinder AI - Intelligent CV & Job Matching Assistant
Main Streamlit Application
"""

import os
import io
import json
import logging
from typing import Optional, Dict, Any

try:
    import streamlit as st
except ImportError:
    st = None

from src.gemini_client import GeminiClient, get_api_key
from src.cv_parser import parse_cv, parse_cv_file, parse_cv_file_detailed, CVParserError
from src.cv_analyzer import CVAnalyzer, CVAnalysisError, render_cv_dashboard
from src.job_matcher import JobMatcher, render_match_dashboard
from src.job_finder import JobFinderService, render_find_jobs_dashboard
from src.utils import (
    init_session_state,
    set_nav_page,
    clear_cv_state,
    export_report_markdown,
    load_custom_css,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JobFinderAI.App")

# Curated Sample CV for instant 1-click evaluation
SAMPLE_CV_TEXT = """ALEX MORGAN
Email: alex.morgan.dev@example.com | Location: Seattle, WA | Portfolio: github.com/alexm-dev

PROFESSIONAL SUMMARY:
Results-driven Software Engineer with 3+ years of experience designing, developing, and scaling RESTful APIs, microservices, and modern web applications. Proven track record in Python backend systems, cloud containerization with Docker, and SQL database tuning.

CORE SKILLS:
- Technical: Python, Django, Flask, PostgreSQL, MySQL, Redis, Docker, Git, REST APIs, Linux, AWS (EC2, S3), JavaScript, React.
- Soft: Cross-functional Collaboration, Agile / Scrum Sprints, Technical Mentorship, Root-Cause Problem Solving.

WORK EXPERIENCE:
Software Engineer | Apex Cloud Systems | Jan 2022 - Present
- Architected and deployed 15+ RESTful microservices in Python handling 40,000 daily requests with 99.9% uptime.
- Optimized slow PostgreSQL queries and implemented Redis caching, reducing average response latency by 34%.
- Containerized development and staging environments using Docker, cutting team onboarding time from 3 days to 4 hours.
- Collaborated in an agile scrum team of 8 engineers delivering bi-weekly feature sprints.

Junior Backend Developer | CloudFlow Labs | Jun 2020 - Dec 2021
- Developed automated data ingestion scripts in Python processing CSV/JSON pipelines into relational databases.
- Authored comprehensive unit and integration test suites, increasing overall codebase test coverage to 88%.
- Resolved over 60 customer-reported defects and performance bottlenecks in legacy Django modules.

EDUCATION:
Bachelor of Science in Computer Science | University of Washington | 2016 - 2020
- Relevant Coursework: Data Structures & Algorithms, Distributed Systems, Database Management.

CERTIFICATIONS:
- AWS Certified Cloud Practitioner (2022)
- Docker Certified Associate (2021)

NOTABLE PROJECTS:
Distributed Task Queue (Python, Redis, Docker):
- Built an open-source task worker supporting priority queues and exponential backoff retry policies.
Live Metrics Monitor (React, Python):
- Created a real-time analytics portal monitoring system CPU and memory metrics via WebSocket streams.

LANGUAGES:
- English (Native), Spanish (Conversational)
"""


def render_sidebar(gemini_client: GeminiClient):
    """Render consistent sidebar navigation and system health status."""
    st.sidebar.markdown("### 🔍 JOBFINDER AI")
    st.sidebar.caption("AI-Powered CV & Job Matching Assistant")

    pages = [
        "Home",
        "Welcome",
        "Upload CV",
        "CV Analysis",
        "Find Jobs",
        "Job Match",
        "CV Improvement",
        "About",
    ]

    current_page = st.session_state.get("nav_page", "Home")
    try:
        selected_index = pages.index(current_page)
    except ValueError:
        selected_index = 0

    def on_nav_change(radio_key):
        target = st.session_state.get(radio_key, "Home")
        set_nav_page(target)

    radio_key = f"sidebar_nav_selection_{current_page}"

    selected = st.sidebar.radio(
        "Navigation",
        pages,
        index=selected_index,
        key=radio_key,
        on_change=on_nav_change,
        args=(radio_key,),
    )

    st.sidebar.markdown("---")

    # Status indicators
    st.sidebar.markdown("##### ⚙️ System Status")
    if gemini_client.is_configured:
        st.sidebar.success("● Gemini AI: Connected (Live)")
    else:
        st.sidebar.info("○ Gemini AI: Demo / Heuristic Mode")
        st.sidebar.caption("Provide GEMINI_API_KEY in .env or secrets to activate real-time AI calls.")

    # CV State preview
    cv = st.session_state.get("cv_profile") or st.session_state.get("cv_analysis")
    if cv:
        cv_name = cv.get("name") or "Candidate"
        st.sidebar.markdown(f"**Loaded CV:** {cv_name}")
        if st.sidebar.button("Clear CV Data", use_container_width=True, key="sidebar_clear_cv_btn"):
            clear_cv_state()
            st.rerun()
    else:
        st.sidebar.caption("No CV loaded yet.")

    # Target Job Preview
    target_title = st.session_state.get("target_job_title")
    if target_title:
        st.sidebar.markdown(f"**Target Job:** {target_title[:28]}...")

    st.sidebar.markdown("---")
    st.sidebar.caption("Built for Hackathon Demonstration • Powered by Google Gemini")


def render_video_fallback():
    """Clean visual banner fallback when intro video is missing or unplayable."""
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); 
                    border-radius: 14px; padding: 40px 28px; color: #ffffff; text-align: center; 
                    border: 1px solid #334155; margin-bottom: 24px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
            <div style="display: inline-block; background: rgba(37, 99, 235, 0.2); border: 1px solid rgba(59, 130, 246, 0.4); 
                        border-radius: 9999px; padding: 6px 16px; font-size: 0.8125rem; font-weight: 600; color: #93c5fd; margin-bottom: 14px;">
                ✦ Video Intro Ready • Multi-Format Engine Active
            </div>
            <h2 style="font-size: 1.875rem; font-weight: 800; margin-bottom: 10px; color: #f8fafc; letter-spacing: -0.02em;">
                Connecting Talent to Opportunity with Precision AI
            </h2>
            <p style="max-width: 68ch; margin: 0 auto 20px auto; color: #cbd5e1; font-size: 1rem; line-height: 1.6;">
                Upload your CV to unlock instant semantic skills extraction, multi-dimensional job matching, and targeted resume optimization.
            </p>
            <div style="display: flex; justify-content: center; gap: 12px; flex-wrap: wrap;">
                <span style="background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.15); padding: 6px 14px; border-radius: 6px; font-size: 0.8125rem;">⚡ Gemini 3.8 Flash</span>
                <span style="background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.15); padding: 6px 14px; border-radius: 6px; font-size: 0.8125rem;">🔒 Zero Data Exposure</span>
                <span style="background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.15); padding: 6px 14px; border-radius: 6px; font-size: 0.8125rem;">📊 ATS Breakdown</span>
                <span style="background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.15); padding: 6px 14px; border-radius: 6px; font-size: 0.8125rem;">🎯 Transparent Compatibility</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_home():
    """
    1. HOME Screen
    - Header: JOBFINDER AI
    - Subtitle: "Understand your CV. Discover relevant jobs. Measure your match."
    - Video: assets/intro.mp4 with graceful fallback
    - Button: "Get Started"
    """
    st.markdown(
        """
        <div class="hero-container">
            <h1 class="hero-title" style="letter-spacing: -0.03em; text-transform: uppercase;">JOBFINDER AI</h1>
            <p class="hero-subtitle" style="font-weight: 500; color: #334155; font-size: 1.25rem;">
                Understand your CV. Discover relevant jobs. Measure your match.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Background / Intro Video from assets/intro.mp4 with graceful fallback
    video_path = "assets/intro.mp4"
    video_loaded = False
    if os.path.exists(video_path):
        try:
            st.video(video_path)
            video_loaded = True
        except Exception as e:
            logger.warning("Intro video playback failed: %s; using graceful fallback.", e)
            render_video_fallback()
    else:
        render_video_fallback()

    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([2, 2, 3])
    with c1:
        if st.button("Get Started", type="primary", use_container_width=True, key="home_get_started_btn"):
            set_nav_page("Welcome")
            st.rerun()
    with c2:
        if st.button("Explore Features ➔", use_container_width=True, key="home_explore_features_btn"):
            set_nav_page("Welcome")
            st.rerun()

    st.markdown("---")
    st.markdown("### Core Capabilities")
    f1, f2, f3 = st.columns(3)

    with f1:
        st.markdown(
            """
            <div class="metric-card">
                <h4>📄 Multi-Format CV Parser</h4>
                <p style="color: #64748b; font-size: 0.9375rem; line-height: 1.5;">
                    Extract structured skills, accomplishments, education, and career milestones from PDF, DOCX, or TXT formats safely and in-memory.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with f2:
        st.markdown(
            """
            <div class="metric-card">
                <h4>🎯 Transparent Job Match Engine</h4>
                <p style="color: #64748b; font-size: 0.9375rem; line-height: 1.5;">
                    Transparent multi-factor alignment: 50% Skills, 20% Experience, 10% Education, 10% Projects, 10% Keywords. Zero fabricated claims.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with f3:
        st.markdown(
            """
            <div class="metric-card">
                <h4>✍️ Actionable CV Improvement</h4>
                <p style="color: #64748b; font-size: 0.9375rem; line-height: 1.5;">
                    Tailor your resume ethically with missing target keywords and Google XYZ formula revisions based strictly on your real background.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def page_welcome():
    """
    2. WELCOME Screen
    - Three steps:
      1. Upload your CV
      2. Find or paste a job
      3. Discover your compatibility score
    - Button: "Continue"
    """
    st.markdown("## Welcome to JobFinder AI")
    st.markdown(
        "**Understand your CV. Discover relevant jobs. Measure your match.** "
        "Follow our simple 3-step workflow to unlock actionable career intelligence."
    )

    st.markdown("---")
    st.markdown("### How It Works in 3 Simple Steps")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            """
            <div class="metric-card" style="min-height: 230px;">
                <div style="font-size: 1.75rem; font-weight: 800; color: #2563eb; margin-bottom: 8px;">1</div>
                <h4 style="margin-bottom: 8px; color: #0f172a;">Upload your CV</h4>
                <p style="color: #64748b; font-size: 0.9375rem; line-height: 1.5;">
                    Upload your resume in PDF, DOCX, or TXT format. Our secure parser extracts verified skills, work experience, projects, and education.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            """
            <div class="metric-card" style="min-height: 230px;">
                <div style="font-size: 1.75rem; font-weight: 800; color: #2563eb; margin-bottom: 8px;">2</div>
                <h4 style="margin-bottom: 8px; color: #0f172a;">Find or paste a job</h4>
                <p style="color: #64748b; font-size: 0.9375rem; line-height: 1.5;">
                    Explore curated openings with multi-factor filters, or paste any job description from LinkedIn, Indeed, or company job boards.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            """
            <div class="metric-card" style="min-height: 230px;">
                <div style="font-size: 1.75rem; font-weight: 800; color: #2563eb; margin-bottom: 8px;">3</div>
                <h4 style="margin-bottom: 8px; color: #0f172a;">Discover your compatibility score</h4>
                <p style="color: #64748b; font-size: 0.9375rem; line-height: 1.5;">
                    Get an instant AI Compatibility Score, skill-by-skill gap analysis, strengths, gaps, and targeted bullet point improvement suggestions.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Continue", type="primary", key="welcome_continue_btn"):
        set_nav_page("Upload CV")
        st.rerun()


def page_upload_cv(cv_analyzer: CVAnalyzer):
    """
    3. UPLOAD CV Screen
    - Streamlit file uploader (PDF, DOCX, TXT)
    - Shows:
      * filename
      * file size
      * file type
    - Button: "Analyze My CV"
    - Stores CVProfile in st.session_state
    """
    st.markdown("## Upload Your CV")
    st.markdown(
        "Upload your resume to begin. JobFinder AI extracts verified skills, experience, education, "
        "and projects without inventing details or exposing raw files."
    )

    tab_file, tab_sample, tab_paste = st.tabs(["📁 Upload File", "✨ Quick Demo Sample", "📝 Paste Text"])

    with tab_file:
        uploaded_file = st.file_uploader(
            "Select your CV file (Supported formats: PDF, DOCX, TXT):",
            type=["pdf", "docx", "txt"],
            key="cv_file_uploader",
            help="Files are processed in memory and never permanently stored without authorization.",
        )

        if uploaded_file is not None:
            # Show filename, file size, file type
            file_name = uploaded_file.name
            size_kb = uploaded_file.size / 1024.0
            ext = os.path.splitext(file_name)[1].lower()
            file_type_label = {
                ".pdf": "PDF Document (.pdf)",
                ".docx": "Microsoft Word Document (.docx)",
                ".txt": "Plain Text (.txt)",
            }.get(ext, f"Document ({ext})")

            st.markdown(
                f"""
                <div class="metric-card" style="margin-top: 16px;">
                    <h4 style="margin-top: 0; margin-bottom: 12px; color: #0f172a;">📄 File Details</h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px;">
                        <div>
                            <div style="font-size: 0.75rem; color: #64748b; text-transform: uppercase; font-weight: 600;">Filename</div>
                            <div style="font-weight: 700; color: #0f172a;">{file_name}</div>
                        </div>
                        <div>
                            <div style="font-size: 0.75rem; color: #64748b; text-transform: uppercase; font-weight: 600;">File Size</div>
                            <div style="font-weight: 700; color: #0f172a;">{size_kb:.1f} KB ({uploaded_file.size} bytes)</div>
                        </div>
                        <div>
                            <div style="font-size: 0.75rem; color: #64748b; text-transform: uppercase; font-weight: 600;">File Type</div>
                            <div style="font-weight: 700; color: #2563eb;">{file_type_label}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button("Analyze My CV", type="primary", use_container_width=True, key="analyze_uploaded_cv_btn"):
                with st.spinner("Parsing document and extracting structured profile with Gemini..."):
                    try:
                        text, format_name = parse_cv_file_detailed(uploaded_file)
                        analysis = cv_analyzer.analyze(text)

                        # Store in stable session_state keys
                        st.session_state["uploaded_cv"] = uploaded_file
                        st.session_state["extracted_text"] = text
                        st.session_state["cv_raw_text"] = text
                        st.session_state["cv_file_name"] = uploaded_file.name
                        st.session_state["cv_format_name"] = format_name
                        st.session_state["cv_profile"] = analysis
                        st.session_state["cv_analysis"] = analysis

                        st.success("CV analyzed successfully!")
                        st.balloons()
                    except CVParserError as pe:
                        st.error(f"❌ File Parsing Error: {pe}")
                    except CVAnalysisError as ae:
                        st.error(f"❌ CV Analysis Error: {ae}")
                    except Exception as ex:
                        logger.error("Unexpected error analyzing CV: %s", ex)
                        st.error(f"❌ Analysis encountered an issue: {ex}")

    with tab_sample:
        st.markdown("Want to test JobFinder AI immediately? Load our curated Full Stack / Backend Engineer profile:")
        if st.button("Load Sample Software Engineer CV", type="secondary", key="load_sample_cv_btn"):
            with st.spinner("Loading sample candidate profile..."):
                analysis = cv_analyzer.analyze(SAMPLE_CV_TEXT)
                st.session_state["uploaded_cv"] = None
                st.session_state["extracted_text"] = SAMPLE_CV_TEXT
                st.session_state["cv_raw_text"] = SAMPLE_CV_TEXT
                st.session_state["cv_file_name"] = "Alex_Morgan_Resume_Sample.txt"
                st.session_state["cv_format_name"] = "Sample Profile"
                st.session_state["cv_profile"] = analysis
                st.session_state["cv_analysis"] = analysis
                st.success("CV analyzed successfully!")
                st.rerun()

    with tab_paste:
        pasted_text = st.text_area(
            "Paste raw CV text here:",
            height=240,
            placeholder="Paste your resume or CV plain text...",
            key="cv_pasted_text_input",
        )
        if st.button("Analyze Pasted Text", key="analyze_pasted_cv_btn"):
            if not pasted_text.strip():
                st.warning("Please paste some text first.")
            else:
                with st.spinner("Analyzing text with Gemini..."):
                    try:
                        analysis = cv_analyzer.analyze(pasted_text)
                        st.session_state["uploaded_cv"] = None
                        st.session_state["extracted_text"] = pasted_text
                        st.session_state["cv_raw_text"] = pasted_text
                        st.session_state["cv_file_name"] = "Pasted_CV_Text.txt"
                        st.session_state["cv_format_name"] = "Plain Text Input"
                        st.session_state["cv_profile"] = analysis
                        st.session_state["cv_analysis"] = analysis
                        st.success("CV analyzed successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error analyzing pasted text: {e}")

    # Active CV Shortcut Banner
    active_profile = st.session_state.get("cv_profile") or st.session_state.get("cv_analysis")
    if active_profile:
        st.markdown("---")
        st.success(f"Active CV in session: **{active_profile.get('name', 'Candidate')}** ({st.session_state.get('cv_file_name', 'Document')})")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("View CV Analysis Dashboard ➔", type="primary", use_container_width=True, key="upload_view_analysis_btn"):
                set_nav_page("CV Analysis")
                st.rerun()
        with c2:
            if st.button("Proceed Directly to Job Match ➔", use_container_width=True, key="upload_proceed_match_btn"):
                set_nav_page("Job Match")
                st.rerun()


def page_cv_analysis():
    """
    4. CV ANALYSIS Screen
    - Display the extracted profile in attractive cards:
      * Candidate summary
      * Skills (Technical & Soft)
      * Education
      * Experience
      * Certifications
      * Projects
      * Languages
    - Clear 'CV analyzed successfully' state
    """
    cv = st.session_state.get("cv_profile") or st.session_state.get("cv_analysis")
    if not cv:
        st.warning("No CV has been analyzed yet. Please upload a CV or load a demo profile first.")
        if st.button("Go to Upload CV ➔", type="primary", key="cv_analysis_go_upload_btn"):
            set_nav_page("Upload CV")
            st.rerun()
        return

    if st.session_state.get("cv_file_name"):
        st.caption(f"Source file: `{st.session_state.get('cv_file_name')}` • Format: `{st.session_state.get('cv_format_name', 'Document')}`")

    # Render complete dashboard component from src.cv_analyzer
    render_cv_dashboard(cv, show_success_state=True)

    st.markdown("<br>", unsafe_allow_html=True)
    action1, action2 = st.columns(2)
    with action1:
        if st.button("Find Matching Jobs For This CV ➔", type="primary", use_container_width=True, key="cv_analysis_find_jobs_btn"):
            set_nav_page("Find Jobs")
            st.rerun()
    with action2:
        if st.button("Compare with Custom Job Description ➔", use_container_width=True, key="cv_analysis_job_match_btn"):
            set_nav_page("Job Match")
            st.rerun()


def page_find_jobs(job_service: JobFinderService):
    """
    5. FIND JOBS Screen
    - Display search/filter controls (title, skills, location, work type, experience level)
    - Job cards with transparent score, source label, and genuine links
    """
    cv = st.session_state.get("cv_profile") or st.session_state.get("cv_analysis")

    def handle_select_job(job):
        st.session_state["selected_job"] = job
        desc = job.get("full_description") or job.get("short_description") or ""
        st.session_state["target_job_description"] = desc
        st.session_state["job_match_jd_input"] = desc
        st.session_state["target_job_title"] = f"{job.get('title')} at {job.get('company')}"
        set_nav_page("Job Match")
        st.rerun()

    render_find_jobs_dashboard(
        job_service=job_service,
        cv_profile=cv,
        on_select_job_for_match=handle_select_job,
    )


def page_job_match(job_matcher: JobMatcher):
    """
    6. JOB MATCH Screen
    - Large job-description text area
    - Button: "Analyze Job Match"
    - Prominent compatibility score with circular progress/ring visual
    - Displays:
      * Matching Skills
      * Partial Matches
      * Missing Skills
      * Experience
      * Education
      * Strengths
      * Gaps
      * Recommendations
    """
    st.markdown("## Job Compatibility Matching")
    st.markdown(
        "Compare your analyzed CV against any target job description. "
        "The system produces an objective, transparent **AI Compatibility Score** with a multi-factor breakdown."
    )

    cv = st.session_state.get("cv_profile") or st.session_state.get("cv_analysis")
    if not cv:
        st.warning("⚠️ No CV loaded in session. Please upload a CV first before analyzing job compatibility.")
        if st.button("Upload CV Now ➔", type="primary", key="job_match_no_cv_btn"):
            set_nav_page("Upload CV")
            st.rerun()
        return

    default_jd = st.session_state.get("target_job_description", "")
    default_title = st.session_state.get("target_job_title", "Custom Job Description")

    st.markdown(f"**Target Role:** `{default_title}`")
    jd_input = st.text_area(
        "Paste the Job Description to match against:",
        value=default_jd,
        height=220,
        placeholder="Paste full job description including requirements, responsibilities, and qualifications...",
        key="job_match_jd_input",
    )

    c_match1, c_match2 = st.columns([3, 1])
    with c_match1:
        analyze_clicked = st.button("Analyze Job Match", type="primary", use_container_width=True, key="analyze_job_match_btn")
    with c_match2:
        clear_jd_clicked = st.button("Clear Description", use_container_width=True, key="clear_jd_btn")

    if clear_jd_clicked:
        st.session_state["job_match_jd_input"] = ""
        st.session_state["target_job_description"] = ""
        st.session_state["target_job_title"] = "Custom Job Description"
        st.session_state["match_result"] = None
        st.session_state["job_match_result"] = None
        st.rerun()

    if analyze_clicked:
        if not jd_input.strip():
            st.warning("Please paste or provide a job description first.")
        else:
            with st.spinner("Analyzing job requirements, skills alignment, and experience depth with Gemini..."):
                try:
                    # Extract JobProfile and compute MatchResult
                    job_profile = job_matcher.analyze_job(jd_input)
                    match_result = job_matcher.match(cv, jd_input)

                    # Store in stable session state keys
                    st.session_state["job_profile"] = job_profile
                    st.session_state["match_result"] = match_result
                    st.session_state["job_match_result"] = match_result
                    st.session_state["target_job_description"] = jd_input
                    st.success("Compatibility analysis complete!")
                except Exception as e:
                    logger.error("Error during job matching: %s", e)
                    st.error(f"Error during job matching: {e}")

    result = st.session_state.get("match_result") or st.session_state.get("job_match_result")
    if not result:
        return

    st.markdown("---")
    render_match_dashboard(result, job_title=default_title)

    st.markdown("<br>", unsafe_allow_html=True)

    # Actions: CV Improvement, Export Report & Back to Jobs
    act1, act2, act3 = st.columns([3, 3, 2])
    with act1:
        if st.button("Get Tailored CV Improvements for this Job ➔", type="primary", use_container_width=True, key="job_match_to_improvement_btn"):
            set_nav_page("CV Improvement")
            st.rerun()

    with act2:
        report_md = export_report_markdown(cv, result, default_title)
        st.download_button(
            label="Download Match Report (Markdown)",
            data=report_md,
            file_name=f"JobFinder_Match_Report.md",
            mime="text/markdown",
            key="download_match_report_btn",
            use_container_width=True,
        )

    with act3:
        if st.button("← Back to Find Jobs", use_container_width=True, key="job_match_back_to_jobs_btn"):
            set_nav_page("Find Jobs")
            st.rerun()


def page_cv_improvement(job_matcher: JobMatcher):
    """
    7. CV IMPROVEMENT Screen
    - Actionable recommendations:
      * Missing keywords
      * Skills to emphasize
      * Weak sections
      * Suggested bullet points (Google XYZ formula)
      * Strategic action steps
    """
    st.markdown("## Tailored CV Improvement Suggestions")
    st.markdown(
        "Receive actionable, ethical CV tailoring suggestions to maximize ATS keyword alignment "
        "and impact for your target role. **No experience, degrees, or skills will ever be fabricated.**"
    )

    cv_text = st.session_state.get("extracted_text") or st.session_state.get("cv_raw_text")
    jd_text = st.session_state.get("target_job_description")

    if not cv_text:
        st.warning("Please upload a CV first before generating improvement recommendations.")
        if st.button("Go to Upload CV ➔", type="primary", key="cv_improvement_go_upload_btn"):
            set_nav_page("Upload CV")
            st.rerun()
        return

    if not jd_text:
        st.warning("Please provide or select a target Job Description first.")
        if st.button("Go to Job Match ➔", type="primary", key="cv_improvement_go_match_btn"):
            set_nav_page("Job Match")
            st.rerun()
        return

    c_imp1, c_imp2 = st.columns([3, 1])
    with c_imp1:
        if st.button("Generate Tailored CV Improvements", type="primary", use_container_width=True, key="generate_cv_improvements_btn"):
            with st.spinner("Analyzing keyword density and bullet point impact with Gemini..."):
                try:
                    improvements = job_matcher.get_improvements(cv_text, jd_text)
                    st.session_state["cv_improvement_result"] = improvements
                    st.success("Improvement recommendations ready!")
                except Exception as e:
                    logger.error("Error generating improvements: %s", e)
                    st.error(f"Error generating improvements: {e}")
    with c_imp2:
        if st.button("← Back to Job Match", use_container_width=True, key="cv_improvement_back_btn"):
            set_nav_page("Job Match")
            st.rerun()

    result = st.session_state.get("cv_improvement_result")
    if not result:
        return

    st.markdown("---")
    st.info(f"🛡️ **Ethical Guidance**: {result.get('ethical_guidance', 'Suggestions are derived solely from your verified CV background.')}")

    # Keywords & Emphasis
    k_col1, k_col2 = st.columns(2)
    with k_col1:
        st.markdown("### Missing Target Keywords")
        st.caption("Keywords highlighted in the job description that may be relevant to add if you have real experience:")
        missing_kw = result.get("missing_keywords", [])
        if missing_kw:
            pills = "".join([f'<span class="pill-tag pill-rose">{k}</span>' for k in missing_kw])
            st.markdown(pills, unsafe_allow_html=True)
        else:
            st.write("No critical keywords missing.")

    with k_col2:
        st.markdown("### Skills to Emphasize More")
        st.caption("Skills already found in your background that deserve higher prominence for this role:")
        emph_kw = result.get("skills_to_emphasize", [])
        if emph_kw:
            pills = "".join([f'<span class="pill-tag pill-blue">{k}</span>' for k in emph_kw])
            st.markdown(pills, unsafe_allow_html=True)
        else:
            st.write("Core competencies already well-balanced.")

    st.markdown("---")

    # Weak Sections
    st.markdown("### Identified Weak Sections")
    weak_sec = result.get("weak_sections", [])
    if weak_sec:
        for ws in weak_sec:
            st.markdown(f"- ⚠️ {ws}")
    else:
        st.write("No structurally weak sections detected.")

    st.markdown("---")

    # Bullet Point Improvements
    st.markdown("### Suggested Bullet-Point Improvements (Google XYZ Formula)")
    st.caption("High-impact revisions of existing experience points demonstrating quantifiable outcomes (Accomplished [X] as measured by [Y], by doing [Z]):")

    bullets = result.get("suggested_bullet_point_improvements", [])
    for idx, bp in enumerate(bullets):
        with st.container():
            st.markdown(
                f"""
                <div class="metric-card">
                    <div style="font-weight: 600; color: #64748b; font-size: 0.8125rem; text-transform: uppercase;">Original / Focus Area:</div>
                    <p style="color: #64748b; font-style: italic; margin-bottom: 8px;">"{bp.get('original_or_section')}"</p>
                    <div style="font-weight: 600; color: #2563eb; font-size: 0.8125rem; text-transform: uppercase;">Suggested High-Impact Revision:</div>
                    <p style="color: #0f172a; font-weight: 600; margin-bottom: 8px;">"{bp.get('suggested_revision')}"</p>
                    <div style="font-size: 0.875rem; color: #475569;"><strong>Why:</strong> {bp.get('reason')}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.markdown("### Strategic Tailoring Action Steps")
    for step in result.get("tailoring_recommendations", []):
        st.markdown(f"- 🚀 {step}")


def page_about(gemini_client: GeminiClient):
    """
    8. ABOUT Screen
    - Project explanation
    - AI technology & architecture
    - Privacy & data protection considerations
    - Hackathon purpose
    - System diagnostics & reset
    """
    st.markdown("## About JobFinder AI")
    st.markdown(
        "JobFinder AI was created for a student hackathon to empower job seekers with intelligent, "
        "honest, and transparent career analysis tools."
    )

    st.markdown("---")
    st.markdown("### 🏆 Hackathon Purpose & Mission")
    st.markdown(
        "Traditional ATS systems often act as opaque black boxes, leaving applicants frustrated and unsure "
        "why their resume was rejected. JobFinder AI bridges this divide by providing candidate-facing career intelligence: "
        "transparent compatibility scores, clear gap analysis, and ethical resume suggestions without ever fabricating credentials."
    )

    st.markdown("---")
    st.markdown("### 🤖 AI Technology & Architecture")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            """
            - **Frontend Framework:** Streamlit (Reactive multi-page architecture)
            - **AI Engine:** Google Gemini API (`gemini-3.8-flash` via `@google/genai`)
            - **Schema Validation:** Pydantic v2 & typed dataclasses
            - **Multi-Format Document Parsing:** `pypdf` (PDF), `python-docx` (DOCX), UTF-8 text readers
            """
        )
    with col2:
        st.markdown(
            """
            - **Job Provider Interface:** Pluggable ABC with Demo Provider & live authorized API adapter
            - **Scoring Engine:** Deterministic weighted formula (50% Skills, 20% Exp, 10% Edu, 10% Proj, 10% KW)
            - **Resilience:** Fallback heuristic parser activates automatically when API keys are absent
            """
        )

    st.markdown("---")
    st.markdown("### 🛡️ Privacy & Data Protection Considerations")
    st.markdown(
        """
        - **In-Memory Processing:** Uploaded CVs are parsed entirely in memory and are not permanently saved to disk.
        - **Zero Data Exposure:** API keys and credentials reside securely on the backend and are never sent to client browsers.
        - **Strict Non-Discrimination:** Compatibility scoring evaluates purely textual qualifications, skills, and experience, explicitly ignoring age, gender, race, nationality, or other protected characteristics.
        - **Truthfulness Mandate:** The tailoring engine specifically refuses to hallucinate unverified employers, degrees, or technical capabilities.
        """
    )

    st.markdown("---")
    st.markdown("### ⚙️ System Diagnostics & Health")

    c1, c2 = st.columns(2)
    with c1:
        if gemini_client.is_configured:
            st.success("✅ Gemini API Key: Configured & Active")
            st.write(f"Active Model: `{gemini_client.model_name}`")
        else:
            st.warning("⚠️ Gemini API Key: Not Configured (Running in Demo Mode)")
            st.caption("Provide `GEMINI_API_KEY` in `.env` to activate live Gemini AI evaluations.")

    with c2:
        cv = st.session_state.get("cv_profile") or st.session_state.get("cv_analysis")
        if cv:
            st.success(f"✅ Active Session: Loaded CV for {cv.get('name', 'Candidate')}")
        else:
            st.info("ℹ️ Active Session: No CV currently active")

    st.markdown("---")
    st.markdown("### Reset Application State")
    c_rst1, c_rst2 = st.columns([2, 2])
    with c_rst1:
        if st.button("Reset All Session State & Cached Results", type="secondary", use_container_width=True, key="reset_all_state_btn"):
            clear_cv_state()
            st.session_state["target_job_description"] = ""
            st.session_state["target_job_title"] = ""
            st.session_state["job_match_jd_input"] = ""
            st.session_state["filter_title"] = ""
            st.session_state["filter_skills"] = ""
            st.session_state["filter_location"] = ""
            st.session_state["filter_work_type"] = "All"
            st.session_state["filter_exp_level"] = "All"
            st.session_state["use_cv_skills"] = False
            set_nav_page("Home")
            st.success("Session state cleared successfully.")
            st.rerun()
    with c_rst2:
        if st.button("Start New Analysis (Home) ➔", type="primary", use_container_width=True, key="about_go_home_btn"):
            set_nav_page("Home")
            st.rerun()


def main():
    """Application main entry point."""
    if st is None:
        print("Streamlit is required to run app.py. Please run via: streamlit run app.py")
        return

    st.set_page_config(
        page_title="JOBFINDER AI - Understand your CV. Discover relevant jobs. Measure your match.",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Load custom CSS
    st.markdown(load_custom_css(), unsafe_allow_html=True)

    # Initialize stable session state keys
    init_session_state()

    # Initialize service singletons
    gemini_client = GeminiClient()
    cv_analyzer = CVAnalyzer(gemini_client)
    job_matcher = JobMatcher(gemini_client)
    job_service = JobFinderService()

    # Render persistent sidebar navigation
    render_sidebar(gemini_client)

    # Multi-Page Router
    current_page = st.session_state.get("nav_page", "Home")

    if current_page == "Home":
        page_home()
    elif current_page == "Welcome":
        page_welcome()
    elif current_page == "Upload CV":
        page_upload_cv(cv_analyzer)
    elif current_page == "CV Analysis":
        page_cv_analysis()
    elif current_page == "Find Jobs":
        page_find_jobs(job_service)
    elif current_page == "Job Match":
        page_job_match(job_matcher)
    elif current_page == "CV Improvement":
        page_cv_improvement(job_matcher)
    elif current_page == "About":
        page_about(gemini_client)
    else:
        page_home()


if __name__ == "__main__":
    main()
