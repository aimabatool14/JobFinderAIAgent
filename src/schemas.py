"""
Structured data models and schemas for JobFinder AI.
Defines contracts for CV parsing, Job Description analysis, and Matching evaluations.
Supports Pydantic v2 with dataclass fallback for maximum portability.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field, asdict

try:
    from pydantic import BaseModel, Field, model_validator
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False


if HAS_PYDANTIC:
    class EducationEntry(BaseModel):
        degree: str = Field(default="Degree/Diploma", description="Name of degree, diploma or coursework")
        institution: str = Field(default="Institution", description="School, university or college name")
        year: Optional[str] = Field(default=None, description="Graduation year or date range")
        details: Optional[str] = Field(default=None, description="Honors, GPA, major, or coursework details")

    class ExperienceEntry(BaseModel):
        role: str = Field(default="Professional Role", description="Job title or role name")
        company: str = Field(default="Company/Organization", description="Company or organization name")
        duration: Optional[str] = Field(default=None, description="Employment dates e.g. Jan 2021 - Present")
        years: Optional[float] = Field(default=None, description="Estimated duration in years")
        bullet_points: List[str] = Field(default_factory=list, description="Key accomplishments and duties")

    class ProjectEntry(BaseModel):
        name: str = Field(default="Project Name", description="Name of project")
        description: str = Field(default="", description="Summary of project goals and scope")
        technologies: List[str] = Field(default_factory=list, description="Tools and libraries utilized")
        url: Optional[str] = Field(default=None, description="Live link or repository URL")

    class CVProfile(BaseModel):
        """
        Normalized schema for candidate CV profile extracted from raw document.
        """
        name: str = Field(default="Candidate", description="Full name of candidate")
        summary: str = Field(default="", description="Professional career summary")
        skills: List[str] = Field(default_factory=list, description="Unified list of all identified skills")
        technical_skills: List[str] = Field(default_factory=list, description="Technical competencies, tools, languages")
        soft_skills: List[str] = Field(default_factory=list, description="Soft competencies, leadership, collaboration")
        education: List[EducationEntry] = Field(default_factory=list, description="Educational degrees and coursework")
        certifications: List[str] = Field(default_factory=list, description="Professional certifications and licenses")
        experience: List[ExperienceEntry] = Field(default_factory=list, description="Chronological work history")
        projects: List[ProjectEntry] = Field(default_factory=list, description="Notable personal or work projects")
        languages: List[str] = Field(default_factory=list, description="Spoken/written languages")
        total_experience_years: Optional[float] = Field(default=None, description="Estimated total years of experience")

        # Compatibility aliases for downstream components
        @model_validator(mode="before")
        @classmethod
        def populate_aliases(cls, data: Any) -> Any:
            if not isinstance(data, dict):
                return data
            # Handle summary vs professional_summary
            if "professional_summary" in data and not data.get("summary"):
                data["summary"] = data["professional_summary"]
            elif "summary" in data and not data.get("professional_summary"):
                data["professional_summary"] = data["summary"]

            # Handle experience vs work_experience
            if "work_experience" in data and not data.get("experience"):
                data["experience"] = data["work_experience"]
            elif "experience" in data and not data.get("work_experience"):
                data["work_experience"] = data["experience"]

            # Handle total_experience_years vs years_of_experience
            if "years_of_experience" in data and data.get("total_experience_years") is None:
                data["total_experience_years"] = data["years_of_experience"]
            elif "total_experience_years" in data and data.get("years_of_experience") is None:
                data["years_of_experience"] = data["total_experience_years"]

            return data

    class JobProfile(BaseModel):
        """
        Structured profile extracted from target Job Description.
        """
        title: str = Field(default="Target Position", description="Job title")
        required_skills: List[str] = Field(default_factory=list, description="Must-have skills and qualifications")
        preferred_skills: List[str] = Field(default_factory=list, description="Nice-to-have or preferred qualifications")
        responsibilities: List[str] = Field(default_factory=list, description="Core day-to-day responsibilities")
        experience_requirements: str = Field(default="", description="Years and depth of experience requested")
        education_requirements: str = Field(default="", description="Degrees or academic background requested")
        certifications: List[str] = Field(default_factory=list, description="Required or preferred licenses/certifications")
        keywords: List[str] = Field(default_factory=list, description="ATS keywords extracted from the JD")

    class MatchResult(BaseModel):
        """
        Structured result comparing candidate CV against target Job Profile.
        """
        overall_score: int = Field(default=0, ge=0, le=100, description="Overall compatibility score out of 100")
        matching_skills: List[str] = Field(default_factory=list, description="Skills proven in CV matching JD requirements")
        partial_matches: List[str] = Field(default_factory=list, description="Adjacent or partially matching skills")
        missing_skills: List[str] = Field(default_factory=list, description="Hard requirements absent from CV")
        experience_match: str = Field(default="", description="Evaluation of candidate seniority and tenure match")
        education_match: str = Field(default="", description="Evaluation of candidate educational background match")
        project_relevance: str = Field(default="", description="Evaluation of candidate projects against job requirements")
        strengths: List[str] = Field(default_factory=list, description="Key candidate strengths for this specific role")
        gaps: List[str] = Field(default_factory=list, description="Key qualification gaps or risks for this role")
        recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations to bridge gaps")
        explanation: str = Field(default="", description="Transparent explanation of the score calculation formula")
        why_matched: str = Field(default="", description="Concise reason why CV matches this job")
        biggest_gaps: str = Field(default="", description="Concise summary of biggest gaps")
        skills_score: int = Field(default=0, description="Skills match dimension score 0-100")
        experience_score: int = Field(default=0, description="Experience match dimension score 0-100")
        education_score: int = Field(default=0, description="Education match dimension score 0-100")
        project_score: int = Field(default=0, description="Project relevance dimension score 0-100")
        keyword_score: int = Field(default=0, description="Keyword alignment dimension score 0-100")

        # Compatibility aliases for downstream UI
        @model_validator(mode="before")
        @classmethod
        def populate_aliases(cls, data: Any) -> Any:
            if not isinstance(data, dict):
                return data
            # overall_score <-> overall_match_percentage
            if "overall_match_percentage" in data and "overall_score" not in data:
                data["overall_score"] = int(data["overall_match_percentage"])
            elif "overall_score" in data and "overall_match_percentage" not in data:
                data["overall_match_percentage"] = int(data["overall_score"])

            # partial_matches <-> partially_matching_skills
            if "partially_matching_skills" in data and not data.get("partial_matches"):
                data["partial_matches"] = data["partially_matching_skills"]
            elif "partial_matches" in data and not data.get("partially_matching_skills"):
                data["partially_matching_skills"] = data["partial_matches"]

            # gaps <-> weaknesses_and_gaps
            if "weaknesses_and_gaps" in data and not data.get("gaps"):
                data["gaps"] = data["weaknesses_and_gaps"]
            elif "gaps" in data and not data.get("weaknesses_and_gaps"):
                data["weaknesses_and_gaps"] = data["gaps"]

            # explanation <-> score_calculation_explanation
            if "score_calculation_explanation" in data and not data.get("explanation"):
                data["explanation"] = data["score_calculation_explanation"]
            elif "explanation" in data and not data.get("score_calculation_explanation"):
                data["score_calculation_explanation"] = data["explanation"]

            # project_relevance aliases
            if "project_relevance_description" in data and not data.get("project_relevance"):
                data["project_relevance"] = data["project_relevance_description"]
            elif "project_relevance" in data and not data.get("project_relevance_description"):
                data["project_relevance_description"] = data["project_relevance"]

            # dimensional score aliases
            if "experience_match_score" in data and not data.get("experience_score"):
                data["experience_score"] = data["experience_match_score"]
            if "education_match_score" in data and not data.get("education_score"):
                data["education_score"] = data["education_match_score"]
            if "project_relevance_score" in data and not data.get("project_score"):
                data["project_score"] = data["project_relevance_score"]

            return data

    class BulletPointImprovement(BaseModel):
        original_or_section: str = Field(description="Original bullet point or target resume section")
        suggested_revision: str = Field(description="High-impact rewrite using Google's XYZ formula")
        reason: str = Field(description="Explanation of why this improves ATS and recruiter perception")

    class CVImprovementResult(BaseModel):
        missing_keywords: List[str] = Field(default_factory=list, description="Target keywords not in CV")
        skills_to_emphasize: List[str] = Field(default_factory=list, description="Existing skills to highlight more prominently")
        weak_sections: List[str] = Field(default_factory=list, description="Sections needing greater depth or clarity")
        suggested_bullet_point_improvements: List[BulletPointImprovement] = Field(default_factory=list)
        tailoring_recommendations: List[str] = Field(default_factory=list, description="Actionable tailoring recommendations")
        ethical_guidance: str = Field(
            default="Recommendations are suggestions strictly derived from your real CV experience. Do not fabricate roles, credentials, or metrics."
        )

    class JobPosting(BaseModel):
        id: str
        title: str
        company: str
        location: str
        work_type: str = Field(default="Remote", description="Remote, Hybrid, or On-site")
        experience_level: str = Field(default="Mid-level", description="Entry-level, Mid-level, Senior, or Lead")
        job_type: str = "Full-time"
        salary_range: Optional[str] = None
        required_skills: List[str] = Field(default_factory=list)
        nice_to_have_skills: List[str] = Field(default_factory=list)
        short_description: str = ""
        full_description: str = ""
        match_score: Optional[int] = None
        source: str = "Demo job data"
        url: Optional[str] = None
        original_application_url: Optional[str] = None
        is_demo: bool = True

        @model_validator(mode="before")
        @classmethod
        def populate_job_aliases(cls, data: Any) -> Any:
            if not isinstance(data, dict):
                return data
            # url vs original_application_url
            if data.get("original_application_url") and not data.get("url"):
                data["url"] = data["original_application_url"]
            elif data.get("url") and not data.get("original_application_url"):
                data["original_application_url"] = data["url"]

            # work_type heuristic fallback if not explicitly set
            if not data.get("work_type"):
                loc = str(data.get("location", "")).lower()
                jt = str(data.get("job_type", "")).lower()
                if "remote" in loc or "remote" in jt:
                    data["work_type"] = "Remote"
                elif "hybrid" in loc or "hybrid" in jt:
                    data["work_type"] = "Hybrid"
                else:
                    data["work_type"] = "On-site"

            return data

else:
    # Fallback to standard Python dataclasses when Pydantic is not installed
    @dataclass
    class EducationEntry:
        degree: str = "Degree/Diploma"
        institution: str = "Institution"
        year: Optional[str] = None
        details: Optional[str] = None

        def model_dump(self) -> Dict[str, Any]:
            return asdict(self)

    @dataclass
    class ExperienceEntry:
        role: str = "Professional Role"
        company: str = "Company/Organization"
        duration: Optional[str] = None
        years: Optional[float] = None
        bullet_points: List[str] = field(default_factory=list)

        def model_dump(self) -> Dict[str, Any]:
            return asdict(self)

    @dataclass
    class ProjectEntry:
        name: str = "Project Name"
        description: str = ""
        technologies: List[str] = field(default_factory=list)
        url: Optional[str] = None

        def model_dump(self) -> Dict[str, Any]:
            return asdict(self)

    @dataclass
    class CVProfile:
        name: str = "Candidate"
        summary: str = ""
        skills: List[str] = field(default_factory=list)
        technical_skills: List[str] = field(default_factory=list)
        soft_skills: List[str] = field(default_factory=list)
        education: List[EducationEntry] = field(default_factory=list)
        certifications: List[str] = field(default_factory=list)
        experience: List[ExperienceEntry] = field(default_factory=list)
        projects: List[ProjectEntry] = field(default_factory=list)
        languages: List[str] = field(default_factory=list)
        total_experience_years: Optional[float] = None

        def model_dump(self) -> Dict[str, Any]:
            data = asdict(self)
            data["professional_summary"] = self.summary
            data["work_experience"] = data.get("experience", [])
            data["years_of_experience"] = self.total_experience_years
            return data

    @dataclass
    class JobProfile:
        title: str = "Target Position"
        required_skills: List[str] = field(default_factory=list)
        preferred_skills: List[str] = field(default_factory=list)
        responsibilities: List[str] = field(default_factory=list)
        experience_requirements: str = ""
        education_requirements: str = ""
        certifications: List[str] = field(default_factory=list)
        keywords: List[str] = field(default_factory=list)

        def model_dump(self) -> Dict[str, Any]:
            return asdict(self)

    @dataclass
    class MatchResult:
        overall_score: int = 0
        matching_skills: List[str] = field(default_factory=list)
        partial_matches: List[str] = field(default_factory=list)
        missing_skills: List[str] = field(default_factory=list)
        experience_match: str = ""
        education_match: str = ""
        project_relevance: str = ""
        strengths: List[str] = field(default_factory=list)
        gaps: List[str] = field(default_factory=list)
        recommendations: List[str] = field(default_factory=list)
        explanation: str = ""
        why_matched: str = ""
        biggest_gaps: str = ""
        skills_score: int = 0
        experience_score: int = 0
        education_score: int = 0
        project_score: int = 0
        keyword_score: int = 0

        def model_dump(self) -> Dict[str, Any]:
            data = asdict(self)
            data["overall_match_percentage"] = self.overall_score
            data["partially_matching_skills"] = self.partial_matches
            data["weaknesses_and_gaps"] = self.gaps
            data["score_calculation_explanation"] = self.explanation
            data["compatibility_label"] = f"AI Compatibility Score: {self.overall_score}%"
            data["project_relevance_description"] = self.project_relevance
            data["experience_match_score"] = self.experience_score
            data["education_match_score"] = self.education_score
            data["project_relevance_score"] = self.project_score
            return data

    @dataclass
    class BulletPointImprovement:
        original_or_section: str = ""
        suggested_revision: str = ""
        reason: str = ""

        def model_dump(self) -> Dict[str, Any]:
            return asdict(self)

    @dataclass
    class CVImprovementResult:
        missing_keywords: List[str] = field(default_factory=list)
        skills_to_emphasize: List[str] = field(default_factory=list)
        weak_sections: List[str] = field(default_factory=list)
        suggested_bullet_point_improvements: List[BulletPointImprovement] = field(default_factory=list)
        tailoring_recommendations: List[str] = field(default_factory=list)
        ethical_guidance: str = "Recommendations are suggestions strictly derived from your real CV experience. Do not fabricate roles, credentials, or metrics."

        def model_dump(self) -> Dict[str, Any]:
            return asdict(self)

    @dataclass
    class JobPosting:
        id: str
        title: str
        company: str
        location: str
        work_type: str = "Remote"
        experience_level: str = "Mid-level"
        job_type: str = "Full-time"
        salary_range: Optional[str] = None
        required_skills: List[str] = field(default_factory=list)
        nice_to_have_skills: List[str] = field(default_factory=list)
        short_description: str = ""
        full_description: str = ""
        match_score: Optional[int] = None
        source: str = "Demo job data"
        url: Optional[str] = None
        original_application_url: Optional[str] = None
        is_demo: bool = True

        def model_dump(self) -> Dict[str, Any]:
            data = asdict(self)
            if self.original_application_url and not self.url:
                data["url"] = self.original_application_url
            elif self.url and not self.original_application_url:
                data["original_application_url"] = self.url
            return data


# Backward compatibility aliases
EducationItem = EducationEntry
ExperienceItem = ExperienceEntry
ProjectItem = ProjectEntry
CVAnalysisResult = CVProfile
JobMatchResult = MatchResult


def validate_schema(schema_cls: Any, raw_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Safely validate and normalize a raw dictionary against a schema class.
    Works whether Pydantic is installed or fallback dataclass is used.
    """
    if not isinstance(raw_dict, dict):
        raw_dict = {}

    if HAS_PYDANTIC and hasattr(schema_cls, "model_validate"):
        try:
            validated = schema_cls.model_validate(raw_dict)
            dumped = validated.model_dump()
            # Ensure bidirectional keys for both old and new consumers
            if isinstance(validated, CVProfile):
                dumped["professional_summary"] = dumped.get("summary", "")
                dumped["work_experience"] = dumped.get("experience", [])
                dumped["years_of_experience"] = dumped.get("total_experience_years")
            elif isinstance(validated, MatchResult):
                dumped["overall_match_percentage"] = dumped.get("overall_score", 0)
                dumped["partially_matching_skills"] = dumped.get("partial_matches", [])
                dumped["weaknesses_and_gaps"] = dumped.get("gaps", [])
                dumped["score_calculation_explanation"] = dumped.get("explanation", "")
                dumped["compatibility_label"] = f"AI Compatibility Score: {dumped.get('overall_score', 0)}%"
            return dumped
        except Exception:
            pass

    # Fallback normalization
    normalized = dict(raw_dict)
    if schema_cls in (CVProfile, CVAnalysisResult):
        normalized.setdefault("name", "Candidate")
        summary = normalized.get("summary") or normalized.get("professional_summary") or ""
        normalized["summary"] = summary
        normalized["professional_summary"] = summary
        exp = normalized.get("experience") or normalized.get("work_experience") or []
        normalized["experience"] = exp
        normalized["work_experience"] = exp
        yoe = normalized.get("total_experience_years") or normalized.get("years_of_experience")
        normalized["total_experience_years"] = yoe
        normalized["years_of_experience"] = yoe
        normalized.setdefault("skills", [])
        normalized.setdefault("technical_skills", [])
        normalized.setdefault("soft_skills", [])
        normalized.setdefault("education", [])
        normalized.setdefault("certifications", [])
        normalized.setdefault("projects", [])
        normalized.setdefault("languages", [])

    elif schema_cls in (MatchResult, JobMatchResult):
        score = normalized.get("overall_score") or normalized.get("overall_match_percentage") or 0
        try:
            score = int(score)
        except Exception:
            score = 0
        normalized["overall_score"] = score
        normalized["overall_match_percentage"] = score
        normalized["compatibility_label"] = f"AI Compatibility Score: {score}%"
        matching = normalized.get("matching_skills") or []
        normalized["matching_skills"] = matching
        partial = normalized.get("partial_matches") or normalized.get("partially_matching_skills") or []
        normalized["partial_matches"] = partial
        normalized["partially_matching_skills"] = partial
        missing = normalized.get("missing_skills") or []
        normalized["missing_skills"] = missing
        gaps = normalized.get("gaps") or normalized.get("weaknesses_and_gaps") or []
        normalized["gaps"] = gaps
        normalized["weaknesses_and_gaps"] = gaps
        expl = normalized.get("explanation") or normalized.get("score_calculation_explanation") or ""
        normalized["explanation"] = expl
        normalized["score_calculation_explanation"] = expl
        normalized.setdefault("experience_match", "Experience aligns with requirements.")
        normalized.setdefault("education_match", "Education aligns with requirements.")
        proj_rel = normalized.get("project_relevance") or normalized.get("project_relevance_description") or "Candidate technical projects align with key requirements."
        normalized["project_relevance"] = proj_rel
        normalized["project_relevance_description"] = proj_rel
        normalized.setdefault("why_matched", "Your CV demonstrates solid core alignment with the target role.")
        normalized.setdefault("biggest_gaps", "No critical blockers identified.")
        normalized.setdefault("skills_score", score)
        normalized.setdefault("experience_score", 85)
        normalized.setdefault("education_score", 85)
        normalized.setdefault("project_score", 80)
        normalized.setdefault("keyword_score", 80)
        normalized.setdefault("experience_match_score", normalized["experience_score"])
        normalized.setdefault("education_match_score", normalized["education_score"])
        normalized.setdefault("project_relevance_score", normalized["project_score"])
        normalized.setdefault("strengths", [])
        normalized.setdefault("recommendations", [])

    elif schema_cls is JobProfile:
        normalized.setdefault("title", "Target Position")
        normalized.setdefault("required_skills", [])
        normalized.setdefault("preferred_skills", [])
        normalized.setdefault("responsibilities", [])
        normalized.setdefault("experience_requirements", "")
        normalized.setdefault("education_requirements", "")
        normalized.setdefault("certifications", [])
        normalized.setdefault("keywords", [])

    return normalized
