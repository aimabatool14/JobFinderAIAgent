"""
AI Client for JobFinder AI.

NOTE: This module is still named `gemini_client.py` and the class is still
called `GeminiClient` on purpose — every other file in the project
(app.py, src/job_matcher.py, and presumably src/cv_analyzer.py) imports
these exact names. Renaming them would require touching every file that
imports this module. Internally, this now calls the xAI Grok API via its
OpenAI-compatible endpoint instead of Google Gemini.

Required environment variable: XAI_API_KEY
Optional environment variable: GROK_MODEL (defaults to "grok-4.6")

If you'd rather rename this module/class to something Grok-specific,
say so and I'll give you the exact import-line changes needed in
app.py, src/job_matcher.py, and src/cv_analyzer.py.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("JobFinderAI.GeminiClient")

DEFAULT_MODEL = os.environ.get("GROK_MODEL", "grok-4.6")
XAI_BASE_URL = "https://api.x.ai/v1"

try:
    from openai import OpenAI, APIError, RateLimitError as _OpenAIRateLimitError
    HAS_OPENAI_SDK = True
except ImportError:
    HAS_OPENAI_SDK = False
    APIError = Exception
    _OpenAIRateLimitError = Exception


# ---------------------------------------------------------------------------
# Exceptions (names preserved so job_matcher.py's except clauses keep working)
# ---------------------------------------------------------------------------
class GeminiError(Exception):
    """Generic error talking to the AI backend (now Grok/xAI)."""
    pass


class GeminiKeyMissingError(GeminiError):
    """Raised when XAI_API_KEY is not configured."""
    pass


class GeminiRateLimitError(GeminiError):
    """Raised when the xAI API returns a rate-limit response."""
    pass


def get_api_key() -> Optional[str]:
    """Read the xAI API key from the environment."""
    return os.environ.get("XAI_API_KEY") or None


def _extract_json(text: str) -> Dict[str, Any]:
    """
    Grok's chat completion returns plain text; extract the JSON object from it,
    tolerating markdown code fences if the model wraps its answer in ```json ... ```.
    """
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(cleaned[start:end + 1])
        raise


class GeminiClient:
    """
    Thin wrapper around the xAI Grok API (OpenAI-compatible Chat Completions
    endpoint). Public interface kept identical to the original Gemini-backed
    client so app.py / job_matcher.py / cv_analyzer.py do not need to change:

      - is_configured (bool property)
      - model_name (str property)
      - analyze_job(job_description) -> dict
      - match_cv_to_job(cv_data, job_description) -> dict
      - get_cv_improvement_suggestions(cv_text, job_description) -> dict
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or get_api_key()
        self.model_name = model_name or DEFAULT_MODEL
        self._client = None

        if self.api_key and HAS_OPENAI_SDK:
            try:
                self._client = OpenAI(api_key=self.api_key, base_url=XAI_BASE_URL)
            except Exception as exc:
                logger.warning("Failed to initialize xAI client: %s", exc)
                self._client = None

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and HAS_OPENAI_SDK and self._client is not None)

    # ------------------------------------------------------------------
    # Internal helper
    # ------------------------------------------------------------------
    def _chat_json(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> Dict[str, Any]:
        if not self.is_configured:
            raise GeminiKeyMissingError(
                "XAI_API_KEY is not set (or the 'openai' package is not installed). "
                "Set the XAI_API_KEY environment variable to enable live Grok calls."
            )

        try:
            response = self._client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                response_format={"type": "json_object"},
            )
        except _OpenAIRateLimitError as exc:
            raise GeminiRateLimitError(f"xAI rate limit hit: {exc}") from exc
        except APIError as exc:
            raise GeminiError(f"xAI API error: {exc}") from exc
        except Exception as exc:
            raise GeminiError(f"Unexpected error calling xAI API: {exc}") from exc

        content = response.choices[0].message.content
        try:
            return _extract_json(content)
        except (json.JSONDecodeError, ValueError) as exc:
            raise GeminiError(f"xAI response was not valid JSON: {exc}") from exc

    # ------------------------------------------------------------------
    # Public methods expected by the rest of the app
    # ------------------------------------------------------------------
    def analyze_job(self, job_description: str) -> Dict[str, Any]:
        """Extract a structured JobProfile from a raw job description via Grok."""
        system_prompt = (
            "You are an expert technical recruiter. Extract a structured job profile "
            "from the job description as a single JSON object with keys: "
            "title (string), required_skills (array of strings), preferred_skills "
            "(array of strings), responsibilities (array of strings), "
            "experience_requirements (string), education_requirements (string), "
            "certifications (array of strings), keywords (array of strings). "
            "Respond with ONLY the JSON object, no commentary."
        )
        return self._chat_json(system_prompt, job_description)

    def match_cv_to_job(self, cv_data: Dict[str, Any], job_description: str) -> Dict[str, Any]:
        """Produce a MatchResult-shaped dict comparing a CV profile to a job description."""
        system_prompt = (
            "You are an objective, non-discriminatory CV-to-job matching engine. "
            "Given a candidate's CV profile (JSON) and a job description, evaluate ONLY "
            "verified textual evidence in the CV. NEVER factor in protected "
            "characteristics (name, gender, age, photo, nationality, religion, "
            "ethnicity, etc.). Never invent skills, experience, or credentials. "
            "Respond with a single JSON object containing: overall_score (0-100 int), "
            "compatibility_label (string), matching_skills (array), "
            "partially_matching_skills (array), missing_skills (array), "
            "experience_match (string), education_match (string), "
            "project_relevance (string), strengths (array of strings), "
            "weaknesses_and_gaps (array of strings), recommendations (array of strings), "
            "why_matched (string), biggest_gaps (string), "
            "score_calculation_explanation (string). "
            "Respond with ONLY the JSON object, no commentary."
        )
        user_prompt = (
            f"CANDIDATE CV PROFILE (JSON):\n{json.dumps(cv_data, default=str)}\n\n"
            f"JOB DESCRIPTION:\n{job_description}"
        )
        return self._chat_json(system_prompt, user_prompt)

    def get_cv_improvement_suggestions(self, cv_text: str, job_description: str) -> Dict[str, Any]:
        """Produce truthful, ethical CV tailoring suggestions for a target job."""
        system_prompt = (
            "You are an ethical resume coach. Suggest CV improvements strictly "
            "derived from the candidate's real, provided experience. NEVER fabricate "
            "roles, employers, degrees, or metrics. Respond with a single JSON object "
            "containing: missing_keywords (array of strings), skills_to_emphasize "
            "(array of strings), weak_sections (array of strings), "
            "suggested_bullet_point_improvements (array of objects, each with "
            "original_or_section, suggested_revision, reason), "
            "tailoring_recommendations (array of strings), ethical_guidance (string). "
            "Respond with ONLY the JSON object, no commentary."
        )
        user_prompt = f"CANDIDATE CV TEXT:\n{cv_text}\n\nTARGET JOB DESCRIPTION:\n{job_description}"
        return self._chat_json(system_prompt, user_prompt)
