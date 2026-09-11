import React from "react";
import { PageId } from "../types";
import { UploadCloud, Search, CheckCircle2, ArrowRight } from "lucide-react";

interface WelcomeSectionProps {
  onContinue: () => void;
}

export const WelcomeSection: React.FC<WelcomeSectionProps> = ({ onContinue }) => {
  return (
    <div className="max-w-3xl mx-auto py-8 space-y-8">
      {/* Title */}
      <div className="text-center space-y-3">
        <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">
          Welcome to JobFinder AI
        </h2>
        <p className="text-lg text-slate-700 font-medium max-w-2xl mx-auto leading-relaxed">
          Upload your CV and let AI understand your skills, experience and education. Then compare your CV with a job description and discover how well you match.
        </p>
      </div>

      {/* 3 Step Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs relative">
          <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 font-bold text-sm flex items-center justify-center mb-4">
            1
          </div>
          <div className="w-10 h-10 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center mb-3">
            <UploadCloud className="w-5 h-5" />
          </div>
          <h3 className="text-base font-bold text-slate-900 mb-1">Upload your CV</h3>
          <p className="text-sm text-slate-600 leading-relaxed">
            Drag and drop your PDF, DOCX, or text file. Gemini extracts your key capabilities and career chronology.
          </p>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs relative">
          <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 font-bold text-sm flex items-center justify-center mb-4">
            2
          </div>
          <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center mb-3">
            <Search className="w-5 h-5" />
          </div>
          <h3 className="text-base font-bold text-slate-900 mb-1">Find or paste a job</h3>
          <p className="text-sm text-slate-600 leading-relaxed">
            Select from verified demo job openings or paste any target job description directly from external career portals.
          </p>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs relative">
          <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 font-bold text-sm flex items-center justify-center mb-4">
            3
          </div>
          <div className="w-10 h-10 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center mb-3">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <h3 className="text-base font-bold text-slate-900 mb-1">Discover your match</h3>
          <p className="text-sm text-slate-600 leading-relaxed">
            Review your AI Compatibility Score, view matched versus missing skills, and receive actionable suggestions.
          </p>
        </div>
      </div>

      {/* Continue Action */}
      <div className="pt-4 text-center">
        <button
          id="welcome-continue-btn"
          onClick={onContinue}
          className="px-8 py-3.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold shadow-sm transition inline-flex items-center gap-2 text-base"
        >
          Continue to Upload CV
          <ArrowRight className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
};
