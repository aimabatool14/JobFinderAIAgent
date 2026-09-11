import React, { useState, useEffect } from "react";
import { PageId, CVAnalysis, Job, JobMatchResult, CVImprovementResult } from "./types";
import { Header } from "./components/Header";
import { HomeSection } from "./components/HomeSection";
import { WelcomeSection } from "./components/WelcomeSection";
import { UploadCvSection, SAMPLE_CV_TEXT } from "./components/UploadCvSection";
import { CvAnalysisSection } from "./components/CvAnalysisSection";
import { FindJobsSection } from "./components/FindJobsSection";
import { JobMatchSection } from "./components/JobMatchSection";
import { CvImprovementSection } from "./components/CvImprovementSection";
import { AboutSection } from "./components/AboutSection";

export default function App() {
  const [activePage, setActivePage] = useState<PageId>("Home");
  const [isConfigured, setIsConfigured] = useState<boolean>(false);

  // Core application state
  const [rawCvText, setRawCvText] = useState<string>("");
  const [cvFileName, setCvFileName] = useState<string>("");
  const [cvAnalysis, setCvAnalysis] = useState<CVAnalysis | null>(null);

  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [jobDescription, setJobDescription] = useState<string>("");
  const [jobTitle, setJobTitle] = useState<string>("");
  const [matchResult, setMatchResult] = useState<JobMatchResult | null>(null);
  const [improvementResult, setImprovementResult] = useState<CVImprovementResult | null>(null);

  // Fetch server status on mount
  useEffect(() => {
    fetch("/api/status")
      .then((res) => res.json())
      .then((data) => {
        setIsConfigured(data.configured);
      })
      .catch((err) => {
        console.warn("Could not fetch server status:", err);
      });
  }, []);

  const handleCvParsed = (text: string, fileName: string, analysis: CVAnalysis) => {
    setRawCvText(text);
    setCvFileName(fileName);
    setCvAnalysis(analysis);
    setMatchResult(null);
    setImprovementResult(null);
    setActivePage("CV Analysis");
  };

  const handleLoadSample = async () => {
    try {
      const res = await fetch("/api/analyze-cv", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cvText: SAMPLE_CV_TEXT }),
      });
      if (res.ok) {
        const analysis: CVAnalysis = await res.json();
        handleCvParsed(SAMPLE_CV_TEXT, "Alex_Morgan_Resume_Sample.txt", analysis);
      }
    } catch (e) {
      console.error("Failed to load sample CV:", e);
    }
  };

  const handleSelectJobForMatch = (job: Job) => {
    setSelectedJob(job);
    setJobTitle(`${job.title} at ${job.company}`);
    setJobDescription(job.full_description);
    setActivePage("Job Match");
  };

  const handleMatchComplete = (result: JobMatchResult, jd: string, title: string) => {
    setMatchResult(result);
    setJobDescription(jd);
    setJobTitle(title);
    setImprovementResult(null); // Reset downstream improvements
  };

  const handleResetCv = () => {
    setRawCvText("");
    setCvFileName("");
    setCvAnalysis(null);
    setMatchResult(null);
    setImprovementResult(null);
  };

  const handleResetAll = () => {
    handleResetCv();
    setSelectedJob(null);
    setJobDescription("");
    setJobTitle("");
    setActivePage("Home");
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
      <Header
        activePage={activePage}
        onSelectPage={setActivePage}
        hasCv={!!cvAnalysis}
        cvName={cvAnalysis?.name}
        isConfigured={isConfigured}
        onReset={handleResetCv}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activePage === "Home" && (
          <HomeSection
            onNavigate={setActivePage}
            onLoadSample={handleLoadSample}
          />
        )}

        {activePage === "Welcome" && (
          <WelcomeSection
            onContinue={() => setActivePage("Upload CV")}
          />
        )}

        {activePage === "Upload CV" && (
          <UploadCvSection
            onCvParsed={handleCvParsed}
            onNavigateToAnalysis={() => setActivePage("CV Analysis")}
            hasCv={!!cvAnalysis}
            currentCvName={cvFileName}
          />
        )}

        {activePage === "CV Analysis" && (
          <CvAnalysisSection
            cv={cvAnalysis}
            fileName={cvFileName}
            onNavigate={setActivePage}
          />
        )}

        {activePage === "Find Jobs" && (
          <FindJobsSection
            cv={cvAnalysis}
            onSelectJobForMatch={handleSelectJobForMatch}
            onNavigate={setActivePage}
          />
        )}

        {activePage === "Job Match" && (
          <JobMatchSection
            cv={cvAnalysis}
            rawCvText={rawCvText}
            initialJobDescription={jobDescription}
            initialJobTitle={jobTitle}
            matchResult={matchResult}
            onMatchComplete={handleMatchComplete}
            onNavigate={setActivePage}
          />
        )}

        {activePage === "CV Improvement" && (
          <CvImprovementSection
            rawCvText={rawCvText}
            jobDescription={jobDescription}
            improvementResult={improvementResult}
            onImprovementsGenerated={setImprovementResult}
            onNavigate={setActivePage}
          />
        )}

        {activePage === "About" && (
          <AboutSection
            isConfigured={isConfigured}
            hasCv={!!cvAnalysis}
            cvName={cvAnalysis?.name}
            onResetAll={handleResetAll}
          />
        )}
      </main>

      <footer className="border-t border-slate-200 bg-white py-6 mt-12">
        <div className="max-w-7xl mx-auto px-4 text-center text-xs text-slate-500">
          <p>
            JobFinder AI • Developed for Hackathon Evaluation • Powered by Google Gemini 3.8 Flash
          </p>
          <p className="mt-1 text-slate-400">
            Strict Zero-Leakage Architecture: API keys stored server-side. Resume data processed in-memory.
          </p>
        </div>
      </footer>
    </div>
  );
}
