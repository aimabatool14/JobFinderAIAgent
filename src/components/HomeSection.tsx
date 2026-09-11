import React, { useState } from "react";
import { PageId } from "../types";
import { ArrowRight, BookOpen, ShieldCheck, Zap, BarChart3, CheckCircle, FileCode2, Sparkles } from "lucide-react";

interface HomeSectionProps {
  onNavigate: (page: PageId) => void;
  onLoadSample: () => void;
}

export const HomeSection: React.FC<HomeSectionProps> = ({ onNavigate, onLoadSample }) => {
  const [videoError, setVideoError] = useState(false);

  return (
    <div className="space-y-10 py-4">
      {/* Hero Header */}
      <div className="text-center max-w-3xl mx-auto space-y-4">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
          <Zap className="w-3.5 h-3.5 text-blue-600" />
          Powered by Google Gemini 3.8 Flash
        </div>
        <h1 className="text-4xl sm:text-5xl font-extrabold text-slate-900 tracking-tight">
          JobFinder AI
        </h1>
        <p className="text-lg sm:text-xl text-slate-600 leading-relaxed">
          The intelligent career copilot. Deeply parse your CV, match your true skills against real job descriptions, and unlock transparent, multi-factor compatibility scores.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
          <button
            id="home-get-started-btn"
            onClick={() => onNavigate("Upload CV")}
            className="px-6 py-3 rounded-lg bg-blue-600 text-white font-semibold shadow-sm hover:bg-blue-700 transition flex items-center gap-2"
          >
            Get Started
            <ArrowRight className="w-4 h-4" />
          </button>
          <button
            id="home-how-it-works-btn"
            onClick={() => onNavigate("Welcome")}
            className="px-6 py-3 rounded-lg bg-white border border-slate-300 text-slate-700 font-semibold shadow-xs hover:bg-slate-50 transition flex items-center gap-2"
          >
            <BookOpen className="w-4 h-4 text-slate-500" />
            How It Works
          </button>
          <button
            id="home-sample-cv-btn"
            onClick={onLoadSample}
            className="px-5 py-3 rounded-lg bg-slate-100 text-slate-700 font-medium hover:bg-slate-200 transition text-sm flex items-center gap-1.5"
          >
            <FileCode2 className="w-4 h-4 text-blue-600" />
            Quick Demo (Load Sample CV)
          </button>
        </div>
      </div>

      {/* Video Container with Fallback */}
      <div className="max-w-4xl mx-auto">
        <div className="rounded-2xl overflow-hidden border border-slate-200 shadow-md bg-slate-900 relative">
          {!videoError ? (
            <video
              className="w-full aspect-video object-cover"
              autoPlay
              muted
              loop
              playsInline
              onError={() => setVideoError(true)}
              poster="/assets/poster.jpg"
            >
              <source src="/assets/intro.mp4" type="video/mp4" />
              Your browser does not support the video tag.
            </video>
          ) : null}

          {/* Graceful Fallback Banner */}
          {videoError && (
            <div className="py-16 px-8 text-center text-white bg-linear-to-br from-slate-900 via-slate-800 to-blue-950">
              <div className="w-12 h-12 rounded-full bg-blue-600/20 border border-blue-500/40 flex items-center justify-center mx-auto mb-4 text-blue-400">
                <Sparkles className="w-6 h-6" />
              </div>
              <h2 className="text-2xl font-bold text-slate-100 mb-2">
                Intelligent CV Parsing & Objective Job Matching
              </h2>
              <p className="text-slate-300 max-w-xl mx-auto text-sm sm:text-base leading-relaxed mb-6">
                Understand exactly how hiring algorithms and recruiters evaluate your profile. Discover matching skills, identify missing requirements, and receive targeted bullet point revisions.
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                <span className="px-3 py-1 rounded-md bg-white/10 text-xs font-medium text-slate-200">
                  ✓ PDF, DOCX, TXT Support
                </span>
                <span className="px-3 py-1 rounded-md bg-white/10 text-xs font-medium text-slate-200">
                  ✓ Multi-factor Percentage Formula
                </span>
                <span className="px-3 py-1 rounded-md bg-white/10 text-xs font-medium text-slate-200">
                  ✓ Ethical Resume Rewriting
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Feature Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto pt-4">
        <div className="p-6 rounded-xl bg-white border border-slate-200 shadow-xs hover:border-slate-300 transition">
          <div className="w-10 h-10 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center mb-4">
            <Zap className="w-5 h-5" />
          </div>
          <h3 className="text-base font-bold text-slate-900 mb-1">Deep CV Parsing</h3>
          <p className="text-sm text-slate-600 leading-relaxed">
            Extract technical skills, soft competencies, employment history, education, and projects into clean structured data without formatting loss.
          </p>
        </div>

        <div className="p-6 rounded-xl bg-white border border-slate-200 shadow-xs hover:border-slate-300 transition">
          <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center mb-4">
            <BarChart3 className="w-5 h-5" />
          </div>
          <h3 className="text-base font-bold text-slate-900 mb-1">Transparent Matching</h3>
          <p className="text-sm text-slate-600 leading-relaxed">
            AI-driven compatibility scoring with complete arithmetic transparency (45% skills, 25% experience, 15% education, 15% projects).
          </p>
        </div>

        <div className="p-6 rounded-xl bg-white border border-slate-200 shadow-xs hover:border-slate-300 transition">
          <div className="w-10 h-10 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center mb-4">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <h3 className="text-base font-bold text-slate-900 mb-1">Ethical Tailoring</h3>
          <p className="text-sm text-slate-600 leading-relaxed">
            Receive actionable bullet-point revisions using Google's XYZ formula. We never invent fake degrees or non-existent work history.
          </p>
        </div>
      </div>
    </div>
  );
};
