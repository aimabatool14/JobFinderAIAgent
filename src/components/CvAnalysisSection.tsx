import React from "react";
import { CVAnalysis, PageId } from "../types";
import { User, Briefcase, GraduationCap, Code2, Award, ArrowRight, Layers, Globe } from "lucide-react";

interface CvAnalysisSectionProps {
  cv: CVAnalysis | null;
  fileName?: string;
  onNavigate: (page: PageId) => void;
}

export const CvAnalysisSection: React.FC<CvAnalysisSectionProps> = ({
  cv,
  fileName,
  onNavigate,
}) => {
  if (!cv) {
    return (
      <div className="max-w-2xl mx-auto py-16 text-center space-y-4">
        <div className="w-12 h-12 rounded-full bg-amber-50 text-amber-600 flex items-center justify-center mx-auto">
          <User className="w-6 h-6" />
        </div>
        <h3 className="text-xl font-bold text-slate-900">No CV Loaded Yet</h3>
        <p className="text-slate-600 text-sm max-w-md mx-auto">
          Upload your CV or load our sample candidate profile to see the structured breakdown.
        </p>
        <button
          onClick={() => onNavigate("Upload CV")}
          className="px-6 py-2.5 rounded-lg bg-blue-600 text-white font-semibold text-sm hover:bg-blue-700 transition"
        >
          Go to Upload CV ➔
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-6 space-y-8">
      {/* Header Info */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-6">
        <div>
          <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">
            {cv.name || "Candidate Profile"}
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Source: <span className="font-medium text-slate-700">{fileName || "Uploaded Resume"}</span>
            {cv._demoMode && (
              <span className="ml-2 px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200 text-xs">
                Demo Analysis Mode
              </span>
            )}
          </p>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => onNavigate("Find Jobs")}
            className="px-4 py-2 rounded-lg bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 font-semibold text-xs sm:text-sm transition flex items-center gap-1.5"
          >
            Browse Jobs
          </button>
          <button
            onClick={() => onNavigate("Job Match")}
            className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs sm:text-sm transition flex items-center gap-1.5"
          >
            Match With Job ➔
          </button>
        </div>
      </div>

      {/* Professional Summary */}
      <div className="p-6 rounded-xl bg-white border border-slate-200 shadow-xs">
        <h4 className="text-xs uppercase font-bold text-slate-400 tracking-wider mb-2">
          Professional Summary
        </h4>
        <p className="text-slate-700 text-sm sm:text-base leading-relaxed">
          {cv.professional_summary || "No professional summary detected."}
        </p>
      </div>

      {/* High-level metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-white border border-slate-200 text-center">
          <div className="text-2xl font-black text-blue-600">
            {cv.years_of_experience ? `${cv.years_of_experience} yrs` : "2-4 yrs"}
          </div>
          <div className="text-xs font-medium text-slate-500 mt-1">Experience</div>
        </div>
        <div className="p-4 rounded-xl bg-white border border-slate-200 text-center">
          <div className="text-2xl font-black text-slate-900">
            {cv.technical_skills?.length || 0}
          </div>
          <div className="text-xs font-medium text-slate-500 mt-1">Technical Skills</div>
        </div>
        <div className="p-4 rounded-xl bg-white border border-slate-200 text-center">
          <div className="text-2xl font-black text-slate-900">
            {cv.work_experience?.length || 0}
          </div>
          <div className="text-xs font-medium text-slate-500 mt-1">Work Positions</div>
        </div>
        <div className="p-4 rounded-xl bg-white border border-slate-200 text-center">
          <div className="text-2xl font-black text-slate-900">
            {cv.education?.length || 0}
          </div>
          <div className="text-xs font-medium text-slate-500 mt-1">Degrees / Studies</div>
        </div>
      </div>

      {/* Skills Section */}
      <div className="space-y-4">
        <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
          <Code2 className="w-5 h-5 text-blue-600" />
          Extracted Competencies
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-5 rounded-xl bg-white border border-slate-200">
            <h4 className="text-xs uppercase font-bold text-blue-600 tracking-wider mb-3">
              Technical Skills ({cv.technical_skills?.length || 0})
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {cv.technical_skills?.map((skill, idx) => (
                <span
                  key={idx}
                  className="px-2.5 py-1 rounded-md text-xs font-medium bg-blue-50 text-blue-800 border border-blue-200"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>

          <div className="p-5 rounded-xl bg-white border border-slate-200">
            <h4 className="text-xs uppercase font-bold text-emerald-600 tracking-wider mb-3">
              Soft Skills & Methodologies ({cv.soft_skills?.length || 0})
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {cv.soft_skills?.map((skill, idx) => (
                <span
                  key={idx}
                  className="px-2.5 py-1 rounded-md text-xs font-medium bg-emerald-50 text-emerald-800 border border-emerald-200"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Work Experience */}
      <div className="space-y-4">
        <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
          <Briefcase className="w-5 h-5 text-blue-600" />
          Work Experience
        </h3>

        <div className="space-y-3">
          {cv.work_experience?.map((exp, idx) => (
            <div key={idx} className="p-5 rounded-xl bg-white border border-slate-200 space-y-2">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                <div className="font-bold text-slate-900 text-base">{exp.role}</div>
                <div className="text-xs text-slate-500 font-medium">
                  {exp.duration || "Duration not specified"}
                </div>
              </div>
              <div className="text-xs font-semibold text-blue-600">{exp.company}</div>
              <ul className="list-disc list-inside text-xs sm:text-sm text-slate-600 space-y-1 pt-1">
                {exp.bullet_points?.map((bp, bIdx) => (
                  <li key={bIdx} className="leading-relaxed">
                    {bp}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* Education & Projects Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Education */}
        <div className="space-y-3">
          <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <GraduationCap className="w-5 h-5 text-blue-600" />
            Education
          </h3>
          <div className="space-y-3">
            {cv.education?.map((edu, idx) => (
              <div key={idx} className="p-4 rounded-xl bg-white border border-slate-200">
                <div className="font-bold text-sm text-slate-900">{edu.degree}</div>
                <div className="text-xs text-slate-600 mt-0.5">
                  {edu.institution} {edu.year ? `• ${edu.year}` : ""}
                </div>
                {edu.details && (
                  <p className="text-xs text-slate-500 mt-2">{edu.details}</p>
                )}
              </div>
            ))}
          </div>

          {cv.certifications && cv.certifications.length > 0 && (
            <div className="pt-2">
              <div className="text-xs font-bold uppercase text-slate-400 mb-2">
                Certifications
              </div>
              <div className="space-y-1">
                {cv.certifications.map((c, idx) => (
                  <div key={idx} className="text-xs text-slate-700 flex items-center gap-1.5">
                    <Award className="w-3.5 h-3.5 text-amber-500" />
                    {c}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Projects */}
        <div className="space-y-3">
          <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <Layers className="w-5 h-5 text-blue-600" />
            Featured Projects
          </h3>
          <div className="space-y-3">
            {cv.projects?.map((proj, idx) => (
              <div key={idx} className="p-4 rounded-xl bg-white border border-slate-200 space-y-1.5">
                <div className="font-bold text-sm text-slate-900">{proj.name}</div>
                <p className="text-xs text-slate-600 leading-relaxed">{proj.description}</p>
                {proj.technologies && proj.technologies.length > 0 && (
                  <div className="flex flex-wrap gap-1 pt-1">
                    {proj.technologies.map((t, tIdx) => (
                      <span
                        key={tIdx}
                        className="px-2 py-0.5 rounded bg-slate-100 text-[11px] text-slate-600 font-medium"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom CTA */}
      <div className="pt-4 border-t border-slate-200 flex flex-wrap justify-end gap-3">
        <button
          onClick={() => onNavigate("Find Jobs")}
          className="px-5 py-2.5 rounded-lg bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 font-semibold text-sm transition"
        >
          Browse Open Positions
        </button>
        <button
          id="proceed-to-job-match-btn"
          onClick={() => onNavigate("Job Match")}
          className="px-6 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm transition flex items-center gap-2"
        >
          Compare With Job Description
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
