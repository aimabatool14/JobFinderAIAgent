import React, { useState } from "react";
import { CVImprovementResult, PageId } from "../types";
import { ShieldCheck, Sparkles, Check, ArrowRight, Loader2, Key, Target, AlertCircle } from "lucide-react";

interface CvImprovementSectionProps {
  rawCvText?: string;
  jobDescription?: string;
  improvementResult: CVImprovementResult | null;
  onImprovementsGenerated: (result: CVImprovementResult) => void;
  onNavigate: (page: PageId) => void;
}

export const CvImprovementSection: React.FC<CvImprovementSectionProps> = ({
  rawCvText,
  jobDescription,
  improvementResult,
  onImprovementsGenerated,
  onNavigate,
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!rawCvText) {
      setErrorMsg("Please upload your CV first before generating recommendations.");
      return;
    }
    if (!jobDescription) {
      setErrorMsg("Please select or paste a Job Description first in the 'Job Match' tab.");
      return;
    }

    setIsLoading(true);
    setErrorMsg(null);

    try {
      const response = await fetch("/api/improve-cv", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cvText: rawCvText, jobDescription }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.error || "Failed to generate CV improvements.");
      }

      const result: CVImprovementResult = await response.json();
      onImprovementsGenerated(result);
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.message || "Failed to generate suggestions.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-6 space-y-8">
      <div>
        <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">
          Tailored CV Improvement Suggestions
        </h2>
        <p className="text-sm text-slate-600">
          Optimize your resume specifically for your target role. Enhance keyword density, surface quantifiable impacts using Google's XYZ accomplishment formula, and strengthen weak narrative sections.
        </p>
      </div>

      {/* Ethical Guidance Callout */}
      <div className="p-4 rounded-xl bg-blue-50 border border-blue-200 text-blue-950 flex items-start gap-3">
        <ShieldCheck className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
        <div className="text-xs sm:text-sm leading-relaxed">
          <span className="font-bold">Ethical Resume Optimization Principle:</span> We strictly generate suggestions based on the actual skills and chronology present in your CV. We will never invent fake employers, fabricated degree credentials, or counterfeit technical certifications.
        </div>
      </div>

      {/* Prerequisites warning if missing */}
      {(!rawCvText || !jobDescription) && (
        <div className="p-5 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 space-y-3">
          <div className="flex items-center gap-2 font-bold text-sm">
            <AlertCircle className="w-4 h-4 text-amber-600" />
            Prerequisites Required:
          </div>
          <ul className="text-xs space-y-1 list-disc list-inside text-amber-800">
            {!rawCvText && <li>Active CV must be uploaded in the "Upload CV" tab.</li>}
            {!jobDescription && <li>Target Job Description must be provided in the "Job Match" tab.</li>}
          </ul>
          <div className="flex gap-2 pt-1">
            {!rawCvText && (
              <button
                onClick={() => onNavigate("Upload CV")}
                className="px-4 py-1.5 rounded-lg bg-amber-700 text-white font-semibold text-xs hover:bg-amber-800 transition"
              >
                Go to Upload CV
              </button>
            )}
            {!jobDescription && (
              <button
                onClick={() => onNavigate("Job Match")}
                className="px-4 py-1.5 rounded-lg bg-blue-600 text-white font-semibold text-xs hover:bg-blue-700 transition"
              >
                Go to Job Match
              </button>
            )}
          </div>
        </div>
      )}

      {/* Generate Action Button */}
      {rawCvText && jobDescription && !improvementResult && (
        <div className="p-8 rounded-2xl bg-white border border-slate-200 text-center space-y-4 shadow-xs">
          <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mx-auto">
            <Sparkles className="w-6 h-6" />
          </div>
          <div className="max-w-md mx-auto">
            <h3 className="text-base font-bold text-slate-900">Ready to Generate Tailoring Insights</h3>
            <p className="text-xs sm:text-sm text-slate-500 mt-1">
              Gemini will analyze your resume against the target role requirements and construct high-impact bullet revisions.
            </p>
          </div>

          {errorMsg && (
            <div className="text-xs text-rose-600 bg-rose-50 border border-rose-200 p-2.5 rounded-lg max-w-md mx-auto">
              {errorMsg}
            </div>
          )}

          <button
            id="generate-cv-improvements-btn"
            onClick={handleGenerate}
            disabled={isLoading}
            className="px-6 py-3 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm transition inline-flex items-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Analyzing Keyword Density & Impacts...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Generate Tailored Improvements
              </>
            )}
          </button>
        </div>
      )}

      {/* Improvement Results */}
      {improvementResult && (
        <div className="space-y-6">
          {/* Keywords & Skills Emphases */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-5 rounded-xl bg-white border border-rose-200 shadow-xs space-y-2.5">
              <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-rose-700">
                <Key className="w-4 h-4 text-rose-600" />
                Missing Target Keywords
              </div>
              <p className="text-xs text-slate-500">
                High-frequency keywords from the job description not explicitly present in your CV:
              </p>
              <div className="flex flex-wrap gap-1.5 pt-1">
                {improvementResult.missing_keywords.map((kw, idx) => (
                  <span
                    key={idx}
                    className="px-2.5 py-1 rounded-md text-xs font-medium bg-rose-50 text-rose-800 border border-rose-200"
                  >
                    {kw}
                  </span>
                ))}
              </div>
            </div>

            <div className="p-5 rounded-xl bg-white border border-blue-200 shadow-xs space-y-2.5">
              <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-blue-700">
                <Target className="w-4 h-4 text-blue-600" />
                Skills to Emphasize More
              </div>
              <p className="text-xs text-slate-500">
                Competencies found in your background that deserve higher prominence for this role:
              </p>
              <div className="flex flex-wrap gap-1.5 pt-1">
                {improvementResult.skills_to_emphasize.map((skill, idx) => (
                  <span
                    key={idx}
                    className="px-2.5 py-1 rounded-md text-xs font-medium bg-blue-50 text-blue-800 border border-blue-200"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Weak Sections */}
          <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-xs space-y-2">
            <h4 className="text-sm font-bold text-slate-900">Identified Weak or Vague Sections</h4>
            <div className="space-y-1.5 text-xs sm:text-sm text-slate-600">
              {improvementResult.weak_sections.map((ws, idx) => (
                <div key={idx} className="flex items-start gap-2">
                  <span className="text-amber-500 font-bold">⚠️</span>
                  <span>{ws}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Bullet Point Improvements (XYZ formula) */}
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-bold text-slate-900">
                Suggested Bullet-Point Improvements (Google XYZ Formula)
              </h3>
              <p className="text-xs text-slate-500">
                Formula: Accomplished [X], as measured by [Y], by doing [Z].
              </p>
            </div>

            <div className="space-y-3">
              {improvementResult.suggested_bullet_point_improvements.map((bp, idx) => (
                <div
                  key={idx}
                  className="p-5 rounded-xl bg-white border border-slate-200 shadow-xs space-y-3"
                >
                  <div>
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                      Original or Target Section:
                    </span>
                    <p className="text-xs sm:text-sm text-slate-500 italic mt-0.5">
                      "{bp.original_or_section}"
                    </p>
                  </div>

                  <div className="p-3 rounded-lg bg-emerald-50/70 border border-emerald-200">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-800 block mb-0.5">
                      Suggested High-Impact Revision:
                    </span>
                    <p className="text-xs sm:text-sm font-semibold text-emerald-950">
                      "{bp.suggested_revision}"
                    </p>
                  </div>

                  <div className="text-xs text-slate-600">
                    <span className="font-semibold text-slate-800">Why this improves the CV: </span>
                    {bp.reason}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Strategic Tailoring Action Steps */}
          <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-xs space-y-2">
            <h4 className="text-sm font-bold text-slate-900">Strategic Tailoring Action Checklist</h4>
            <div className="space-y-2 text-xs sm:text-sm text-slate-600">
              {improvementResult.tailoring_recommendations.map((step, idx) => (
                <div key={idx} className="flex items-start gap-2">
                  <div className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">
                    {idx + 1}
                  </div>
                  <span className="pt-0.5">{step}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Re-generate button */}
          <div className="text-center pt-2">
            <button
              onClick={handleGenerate}
              disabled={isLoading}
              className="px-5 py-2 rounded-lg bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 font-semibold text-xs transition"
            >
              Re-analyze CV Improvements
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
