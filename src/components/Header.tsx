import React from "react";
import { PageId } from "../types";
import { Sparkles, Briefcase, FileText, CheckCircle2, RotateCcw } from "lucide-react";

interface HeaderProps {
  activePage: PageId;
  onSelectPage: (page: PageId) => void;
  hasCv: boolean;
  cvName?: string;
  isConfigured: boolean;
  onReset: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  activePage,
  onSelectPage,
  hasCv,
  cvName,
  isConfigured,
  onReset,
}) => {
  const navItems: { id: PageId; label: string }[] = [
    { id: "Home", label: "Home" },
    { id: "Welcome", label: "How It Works" },
    { id: "Upload CV", label: "Upload CV" },
    { id: "CV Analysis", label: "CV Analysis" },
    { id: "Find Jobs", label: "Find Jobs" },
    { id: "Job Match", label: "Job Match" },
    { id: "CV Improvement", label: "Tailor CV" },
    { id: "About", label: "About" },
  ];

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand */}
          <div
            id="header-brand-logo"
            onClick={() => onSelectPage("Home")}
            className="flex items-center gap-2 cursor-pointer select-none group"
          >
            <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-sm group-hover:bg-blue-700 transition">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <span className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-1.5">
                JobFinder AI
                <span className="text-[10px] uppercase font-semibold tracking-wider px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                  Hackathon
                </span>
              </span>
            </div>
          </div>

          {/* Nav pills */}
          <nav className="hidden md:flex items-center gap-1 overflow-x-auto py-1">
            {navItems.map((item) => {
              const isActive = activePage === item.id;
              return (
                <button
                  key={item.id}
                  id={`nav-btn-${item.id.toLowerCase().replace(/\s+/g, "-")}`}
                  onClick={() => onSelectPage(item.id)}
                  className={`px-3 py-1.5 rounded-md text-sm font-medium transition whitespace-nowrap ${
                    isActive
                      ? "bg-blue-600 text-white shadow-xs"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                  }`}
                >
                  {item.label}
                </button>
              );
            })}
          </nav>

          {/* Status & Actions */}
          <div className="flex items-center gap-2">
            {hasCv && (
              <div className="hidden sm:flex items-center gap-1.5 text-xs bg-slate-100 border border-slate-200 text-slate-700 px-2.5 py-1 rounded-full">
                <FileText className="w-3.5 h-3.5 text-blue-600" />
                <span className="font-medium max-w-[120px] truncate">{cvName || "CV Loaded"}</span>
              </div>
            )}

            <span
              className={`hidden sm:inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium border ${
                isConfigured
                  ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                  : "bg-amber-50 text-amber-800 border-amber-200"
              }`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  isConfigured ? "bg-emerald-500" : "bg-amber-500"
                }`}
              />
              {isConfigured ? "Gemini Live" : "Demo Mode"}
            </span>

            {hasCv && (
              <button
                id="reset-cv-header-btn"
                onClick={onReset}
                title="Reset active CV"
                className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-md transition"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Mobile Nav */}
        <div className="flex md:hidden overflow-x-auto py-2 gap-1 border-t border-slate-100">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => onSelectPage(item.id)}
              className={`px-2.5 py-1 rounded-md text-xs font-medium whitespace-nowrap ${
                activePage === item.id
                  ? "bg-blue-600 text-white"
                  : "text-slate-600 bg-slate-50"
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>
    </header>
  );
};
