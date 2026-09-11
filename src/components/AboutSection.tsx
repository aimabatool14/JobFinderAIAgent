import React from "react";
import { ShieldCheck, Cpu, Database, CheckCircle2, RotateCcw, AlertTriangle } from "lucide-react";

interface AboutSectionProps {
  isConfigured: boolean;
  hasCv: boolean;
  cvName?: string;
  onResetAll: () => void;
}

export const AboutSection: React.FC<AboutSectionProps> = ({
  isConfigured,
  hasCv,
  cvName,
  onResetAll,
}) => {
  return (
    <div className="max-w-4xl mx-auto py-6 space-y-8">
      <div>
        <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">
          About JobFinder AI
        </h2>
        <p className="text-sm text-slate-600">
          JobFinder AI is a hackathon-grade career intelligence assistant combining Google Gemini's advanced semantic understanding with transparent, multi-factor job compatibility algorithms.
        </p>
      </div>

      {/* Tech Stack Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-xs space-y-3">
          <div className="flex items-center gap-2 text-blue-600 font-bold text-sm">
            <Cpu className="w-5 h-5" />
            Artificial Intelligence & Architecture
          </div>
          <ul className="text-xs sm:text-sm text-slate-600 space-y-1.5 list-disc list-inside">
            <li><strong>AI Foundation:</strong> Google Gemini 3.8 Flash</li>
            <li><strong>Backend Server:</strong> Node.js / Express proxy layer</li>
            <li><strong>Client Framework:</strong> React 19 + TypeScript + Tailwind CSS</li>
            <li><strong>Python Standalone Engine:</strong> Streamlit (multi-page state)</li>
            <li><strong>Document Parsing:</strong> In-memory PDF, DOCX, and TXT extractors</li>
          </ul>
        </div>

        <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-xs space-y-3">
          <div className="flex items-center gap-2 text-emerald-600 font-bold text-sm">
            <ShieldCheck className="w-5 h-5" />
            Security & Privacy Standards
          </div>
          <ul className="text-xs sm:text-sm text-slate-600 space-y-1.5 list-disc list-inside">
            <li><strong>Zero Key Exposure:</strong> API keys remain strictly on the backend</li>
            <li><strong>No Git Leakage:</strong> Secrets protected by gitignore & env.example</li>
            <li><strong>In-Memory Processing:</strong> CVs parsed ephemerally in active sessions</li>
            <li><strong>No Fabrications:</strong> Strictly truthful bullet point suggestions</li>
          </ul>
        </div>
      </div>

      {/* System Diagnostics */}
      <div className="p-6 rounded-xl bg-white border border-slate-200 shadow-xs space-y-4">
        <h3 className="text-base font-bold text-slate-900">System Diagnostics & Environment</h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs sm:text-sm">
          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
            <div className="font-semibold text-slate-700">Gemini API Service</div>
            {isConfigured ? (
              <div className="text-emerald-700 font-medium flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                Active (Live API Calls Enabled)
              </div>
            ) : (
              <div className="text-amber-800 font-medium flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                Running in Demo / Heuristic Fallback Mode
              </div>
            )}
            <div className="text-[11px] text-slate-500">
              Configure <code className="bg-slate-200 px-1 py-0.5 rounded">GEMINI_API_KEY</code> in environment to switch modes.
            </div>
          </div>

          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
            <div className="font-semibold text-slate-700">Active Session State</div>
            {hasCv ? (
              <div className="text-blue-700 font-medium flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-blue-600" />
                CV Loaded: {cvName || "Active"}
              </div>
            ) : (
              <div className="text-slate-500">No CV loaded into session</div>
            )}
            <div className="text-[11px] text-slate-500">
              Session state persists in browser memory during navigation.
            </div>
          </div>
        </div>

        {/* Reset State */}
        <div className="pt-2 border-t border-slate-100 flex justify-end">
          <button
            id="about-reset-all-btn"
            onClick={onResetAll}
            className="px-4 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs transition inline-flex items-center gap-1.5"
          >
            <RotateCcw className="w-4 h-4 text-slate-500" />
            Reset All Application Data
          </button>
        </div>
      </div>
    </div>
  );
};
