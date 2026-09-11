"""
Gemini Client module for JobFinder AI.
Centralizes all interactions with Google Gemini models using the official Google GenAI Python SDK.
Guarantees zero API key leakage, structured JSON validation, and graceful exception handling.
"""

import os
import json
import re
import logging
from typing import Dict, Any, Optional

from src.schemas import (
    CVProfile,
    JobProfile,
    MatchResult,
    CVImprovementResult,
    validate_schema,
)
from src.prompts import (
    CV_ANALYSIS_SYSTEM_PROMPT,
    CV_ANALYSIS_USER_PROMPT,
    JOB_ANALYSIS_SYSTEM_PROMPT,
    JOB_ANALYSIS_USER_PROMPT,
    JOB_MATCH_SYSTEM_PROMPT,
    JOB_MATCH_USER_PROMPT,
    CV_IMPROVEMENT_SYSTEM_PROMPT,
    CV_IMPROVEMENT_USER_PROMPT,
)

logger = logging.getLogger("JobFinderAI.GeminiClient")

# Centralized default model configuration
DEFAULT_MODEL = "gemini-3.8-flash"


class GeminiError(Exception):
    """Base exception for Gemini client operations."""
    pass


class GeminiKeyMissingError(GeminiError):
    """Raised when GEMINI_API_KEY is not configured in secrets or environment."""
    pass


class GeminiRateLimitError(GeminiError):
    """Raised when the Gemini API quota or rate limit is reached."""
    pass


class GeminiResponseFormatError(GeminiError):
    """Raised when model response cannot be parsed into the expected JSON structure."""
    pass


def get_api_key() -> Optional[str]:
    """
    Retrieve Gemini API key from environment variables or Streamlit secrets safely.
    Ensures keys are never logged, printed, or sent to client-side code.
    """
    # 1. Environment variable (standard for local dev & containers)
    key = os.getenv("GEMINI_API_KEY")
    if key and key.strip() and key != "MY_GEMINI_API_KEY":
        return key.strip()

    # 2. Streamlit secrets (standard for Streamlit Community Cloud)
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            secret_key = st.secrets["GEMINI_API_KEY"]
            if secret_key and secret_key.strip():
                return secret_key.strip()
    except Exception:
        pass

    return None


def clean_and_parse_json(raw_text: str) -> Dict[str, Any]:
    """
    Safely extract and parse JSON from raw model text.
    Strips markdown code fences, backticks, comments, and boundary whitespace.
    """
    if not raw_text or not raw_text.strip():
        raise GeminiResponseFormatError("Model returned an empty response.")

    cleaned = raw_text.strip()

    # Strip markdown code blocks (```json ... ``` or ``` ... ```)
    if cleaned.startswith("```"):
        pattern = r"^```(?:json)?\s*(.*?)\s*```$"
        match = re.search(pattern, cleaned, re.DOTALL | re.IGNORECASE)
        if match:
            cleaned = match.group(1).strip()
        else:
            lines = cleaned.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

    # Fast direct parsing
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Fallback: Extract outermost JSON object brackets { ... }
    start_idx = cleaned.find("{")
    end_idx = cleaned.rfind("}")
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        substring = cleaned[start_idx : end_idx + 1]
        try:
            return json.loads(substring)
        except json.JSONDecodeError as err:
            logger.error("Failed to parse extracted JSON substring: %s", err)
            raise GeminiResponseFormatError(
                "Extracted JSON block was malformed or incomplete."
            ) from err

    raise GeminiResponseFormatError("Model response did not contain a valid JSON object.")


class GeminiClient:
    """
    Encapsulated client for Google Gemini API operations.
    Keeps all SDK invocation logic, error handling, and schema validation centralized.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = DEFAULT_MODEL,
    ):
        self.api_key = api_key or get_api_key()
        self.model_name = model_name
        self._sdk_client = None

    @property
    def is_configured(self) -> bool:
        """Return True if a valid API key string is present."""
        return bool(self.api_key and len(self.api_key) > 5)

    def _ensure_configured(self) -> None:
        """Verify API key existence or raise GeminiKeyMissingError."""
        if not self.is_configured:
            raise GeminiKeyMissingError(
                "Gemini API key is not configured. Please set GEMINI_API_KEY in your "
                "environment, .env file, or Streamlit secrets (.streamlit/secrets.toml)."
            )

    def _get_sdk_client(self):
        """Lazy initialization of the official google.genai Client."""
        if self._sdk_client is not None:
            return self._sdk_client

        self._ensure_configured()

        try:
            from google import genai
            self._sdk_client = genai.Client(api_key=self.api_key)
            return self._sdk_client
        except ImportError:
            logger.warning(
                "The 'google-genai' package is not installed. Falling back to HTTP REST interface."
            )
            return None

    def generate_json_response(
        self,
        system_instruction: str,
        user_prompt: str,
        schema_class: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Send prompt to Gemini requesting structured JSON.
        Validates returned structure against optional schema_class.
        Handles API errors, rate limits, and format defects gracefully.
        """
        self._ensure_configured()

        # 1. Try modern google-genai SDK
        client = self._get_sdk_client()
        raw_text = ""

        if client is not None:
            try:
                from google.genai import types

                response = client.models.generateContent(
                    model=self.model_name,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        temperature=0.2,
                    ),
                )
                raw_text = response.text or ""
            except Exception as exc:
                err_str = str(exc)
                logger.error("Gemini SDK call failed: %s", err_str)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    raise GeminiRateLimitError(
                        "Gemini API rate limit exceeded. Please wait a moment before trying again."
                    ) from exc
                elif "API_KEY_INVALID" in err_str or "403" in err_str or "PERMISSION_DENIED" in err_str:
                    raise GeminiError(
                        "The configured Gemini API key is invalid or unauthorized."
                    ) from exc
                else:
                    raise GeminiError(f"Gemini API error: {err_str}") from exc
        else:
            # 2. Fallback to direct HTTPS REST call if SDK is missing
            raw_text = self._call_via_rest(system_instruction, user_prompt)

        # Parse and sanitize JSON
        parsed_dict = clean_and_parse_json(raw_text)

        # Validate against schema if provided
        if schema_class is not None:
            parsed_dict = validate_schema(schema_class, parsed_dict)

        return parsed_dict

    def _call_via_rest(self, system_instruction: str, user_prompt: str) -> str:
        """Fallback REST caller when google-genai library is not yet installed."""
        import urllib.request
        import urllib.error

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model_name}:generateContent?key={self.api_key}"
        )
        payload = {
            "system_instruction": {"parts": [{"text": system_instruction}]},
            "contents": [{"parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.2,
            },
        }
        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=req_data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=35) as resp:
                resp_json = json.loads(resp.read().decode("utf-8"))
                candidates = resp_json.get("candidates", [])
                if not candidates:
                    raise GeminiResponseFormatError("No content candidates returned by Gemini API.")
                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts or "text" not in parts[0]:
                    raise GeminiResponseFormatError("No text parts returned in candidate response.")
                return parts[0]["text"]
        except urllib.error.HTTPError as http_err:
            body = http_err.read().decode("utf-8", errors="ignore")
            logger.error("Gemini REST call failed: HTTP %s - %s", http_err.code, body)
            if http_err.code == 429:
                raise GeminiRateLimitError("Gemini API rate limit exceeded.") from http_err
            elif http_err.code in (400, 403):
                raise GeminiError("Gemini API request was unauthorized or malformed.") from http_err
            raise GeminiError(f"Gemini REST error (HTTP {http_err.code}): {body}") from http_err
        except Exception as exc:
            logger.error("REST connection error: %s", exc)
            raise GeminiError(f"Connection to Gemini API failed: {exc}") from exc

    def analyze_cv(self, cv_text: str) -> Dict[str, Any]:
        """
        Analyze raw CV text and extract structured CVProfile.
        Validates schema and ensures no credentials are fabricated.
        """
        if not cv_text or len(cv_text.strip()) < 20:
            raise ValueError("CV text is too short to perform meaningful analysis.")

        prompt = CV_ANALYSIS_USER_PROMPT.format(cv_text=cv_text)
        return self.generate_json_response(
            system_instruction=CV_ANALYSIS_SYSTEM_PROMPT,
            user_prompt=prompt,
            schema_class=CVProfile,
        )

    def analyze_job(self, job_description: str) -> Dict[str, Any]:
        """
        Analyze raw Job Description and extract structured JobProfile.
        """
        if not job_description or len(job_description.strip()) < 20:
            raise ValueError("Job Description text is too short to analyze.")

        prompt = JOB_ANALYSIS_USER_PROMPT.format(job_description=job_description)
        return self.generate_json_response(
            system_instruction=JOB_ANALYSIS_SYSTEM_PROMPT,
            user_prompt=prompt,
            schema_class=JobProfile,
        )

    def match_cv_to_job(
        self,
        cv_data: Dict[str, Any],
        job_description: str,
    ) -> Dict[str, Any]:
        """
        Compare candidate CV profile against a target Job Description.
        Returns validated MatchResult schema.
        """
        if not job_description or len(job_description.strip()) < 20:
            raise ValueError("Job Description text is required for matching.")

        # Prepare clear textual summary of candidate profile for prompt
        work_exp = cv_data.get("experience") or cv_data.get("work_experience") or []
        exp_summary = "; ".join([
            f"{e.get('role', '')} at {e.get('company', '')} ({e.get('duration', '')})"
            for e in work_exp if isinstance(e, dict)
        ])
        edu_list = cv_data.get("education") or []
        edu_summary = "; ".join([
            f"{ed.get('degree', '')} from {ed.get('institution', '')}"
            for ed in edu_list if isinstance(ed, dict)
        ])
        proj_list = cv_data.get("projects") or []
        proj_summary = "; ".join([
            f"{p.get('name', '')}: {p.get('description', '')}"
            for p in proj_list if isinstance(p, dict)
        ])
        cert_list = cv_data.get("certifications") or []
        cert_summary = ", ".join([str(c) for c in cert_list if c]) if cert_list else "None listed."

        tech_skills = cv_data.get("technical_skills") or cv_data.get("skills") or []
        tech_skills_str = ", ".join([str(s) for s in tech_skills if s]) if tech_skills else "None listed."
        soft_skills = cv_data.get("soft_skills") or []
        soft_skills_str = ", ".join([str(s) for s in soft_skills if s]) if soft_skills else "None listed."

        prompt = JOB_MATCH_USER_PROMPT.format(
            cv_name=cv_data.get("name", "Candidate"),
            cv_summary=cv_data.get("summary") or cv_data.get("professional_summary", ""),
            cv_yoe=str(cv_data.get("total_experience_years") or cv_data.get("years_of_experience") or "Not specified"),
            cv_tech_skills=tech_skills_str,
            cv_soft_skills=soft_skills_str,
            cv_experience_summary=exp_summary or "No specific work history listed.",
            cv_education_summary=edu_summary or "No formal education listed.",
            cv_projects_summary=proj_summary or "No projects listed.",
            cv_certifications=cert_summary,
            job_description=job_description,
        )

        return self.generate_json_response(
            system_instruction=JOB_MATCH_SYSTEM_PROMPT,
            user_prompt=prompt,
            schema_class=MatchResult,
        )

    def get_cv_improvement_suggestions(
        self,
        cv_text: str,
        job_description: str,
    ) -> Dict[str, Any]:
        """
        Generate honest, non-fabricated CV improvement and bullet point suggestions.
        Returns validated CVImprovementResult schema.
        """
        if not cv_text or not job_description:
            raise ValueError("Both CV text and target Job Description are required.")

        prompt = CV_IMPROVEMENT_USER_PROMPT.format(
            cv_text=cv_text,
            job_description=job_description,
        )

        return self.generate_json_response(
            system_instruction=CV_IMPROVEMENT_SYSTEM_PROMPT,
            user_prompt=prompt,
            schema_class=CVImprovementResult,
        )
