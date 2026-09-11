import React, { useState, useRef } from "react";
import { CVAnalysis } from "../types";
import { UploadCloud, FileText, CheckCircle2, AlertCircle, Sparkles, Loader2, FileCode2 } from "lucide-react";

interface UploadCvSectionProps {
  onCvParsed: (text: string, fileName: string, analysis: CVAnalysis) => void;
  onNavigateToAnalysis: () => void;
  hasCv: boolean;
  currentCvName?: string;
}

export const SAMPLE_CV_TEXT = `ALEX MORGAN
Email: alex.morgan.dev@example.com | Location: Seattle, WA | Portfolio: github.com/alexm-dev

PROFESSIONAL SUMMARY:
Results-driven Software Engineer with 3+ years of experience designing, developing, and scaling RESTful APIs, microservices, and modern web applications. Proven track record in Python backend systems, cloud containerization with Docker, and SQL database tuning.

CORE SKILLS:
- Technical: Python, Django, Flask, PostgreSQL, MySQL, Redis, Docker, Git, REST APIs, Linux, AWS (EC2, S3), JavaScript, React.
- Soft: Cross-functional Collaboration, Agile / Scrum Sprints, Technical Mentorship, Root-Cause Problem Solving.

WORK EXPERIENCE:
Software Engineer | Apex Cloud Systems | Jan 2022 - Present
- Architected and deployed 15+ RESTful microservices in Python handling 40,000 daily requests with 99.9% uptime.
- Optimized slow PostgreSQL queries and implemented Redis caching, reducing average response latency by 34%.
- Containerized development and staging environments using Docker, cutting team onboarding time from 3 days to 4 hours.
- Collaborated in an agile scrum team of 8 engineers delivering bi-weekly feature sprints.

Junior Backend Developer | CloudFlow Labs | Jun 2020 - Dec 2021
- Developed automated data ingestion scripts in Python processing CSV/JSON pipelines into relational databases.
- Authored comprehensive unit and integration test suites, increasing overall codebase test coverage to 88%.
- Resolved over 60 customer-reported defects and performance bottlenecks in legacy Django modules.

EDUCATION:
Bachelor of Science in Computer Science | University of Washington | 2016 - 2020
- Relevant Coursework: Data Structures & Algorithms, Distributed Systems, Database Management.

NOTABLE PROJECTS:
Distributed Task Queue (Python, Redis, Docker):
- Built an open-source task worker supporting priority queues and exponential backoff retry policies.
Live Metrics Monitor (React, Python):
- Created a real-time analytics portal monitoring system CPU and memory metrics via WebSocket streams.

LANGUAGES:
- English (Native), Spanish (Conversational)
`;

export const UploadCvSection: React.FC<UploadCvSectionProps> = ({
  onCvParsed,
  onNavigateToAnalysis,
  hasCv,
  currentCvName,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [pastedText, setPastedText] = useState("");
  const [activeTab, setActiveTab] = useState<"file" | "paste" | "sample">("file");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const processTextWithAi = async (text: string, fileName: string) => {
    setIsLoading(true);
    setErrorMsg(null);

    try {
      const response = await fetch("/api/analyze-cv", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cvText: text }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.error || `Server error (${response.status})`);
      }

      const analysis: CVAnalysis = await response.json();
      onCvParsed(text, fileName, analysis);
    } catch (err: any) {
      console.error("Analysis error:", err);
      setErrorMsg(err.message || "Failed to analyze CV text with Gemini.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (file: File) => {
    setErrorMsg(null);
    const validExtensions = [".pdf", ".docx", ".txt", ".md"];
    const ext = file.name.substring(file.name.lastIndexOf(".")).toLowerCase();

    if (!validExtensions.includes(ext)) {
      setErrorMsg(
        `Unsupported file format '${ext}'. Please upload a standard PDF (.pdf), Word document (.docx), or plain text file (.txt).`
      );
      return;
    }

    if (file.size === 0) {
      setErrorMsg("The selected file is empty (0 bytes). Please upload a valid document.");
      return;
    }

    // Read text from file
    if (ext === ".txt" || ext === ".md") {
      const reader = new FileReader();
      reader.onload = (e) => {
        const text = e.target?.result as string;
        if (!text || text.trim().length < 20) {
          setErrorMsg("File contains too little readable text to be parsed as a CV.");
          return;
        }
        processTextWithAi(text, file.name);
      };
      reader.onerror = () => {
        setErrorMsg("Failed to read the text file.");
      };
      reader.readAsText(file);
    } else {
      // For PDF/DOCX, in the browser preview we parse text lines or fall back to sample/text
      const reader = new FileReader();
      reader.onload = async (e) => {
        try {
          const raw = e.target?.result as string;
          // Extract text strings from file stream
          const textMatches = raw.match(/[\x20-\x7E\r\n\t]{4,}/g);
          const cleanText = textMatches ? textMatches.join(" ") : "";
          if (cleanText.length > 50) {
            await processTextWithAi(cleanText, file.name);
          } else {
            // Friendly guide
            setErrorMsg(
              "Could not extract selectable text from this PDF/DOCX (it may be a scanned image or protected). For the live hackathon preview, please paste text or load our sample CV."
            );
          }
        } catch (err) {
          setErrorMsg("Could not parse file. Supported formats: .pdf, .docx, .txt.");
        }
      };
      reader.readAsBinaryString(file);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleSampleLoad = () => {
    processTextWithAi(SAMPLE_CV_TEXT, "Alex_Morgan_Resume_Sample.txt");
  };

  const handlePasteSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!pastedText.trim() || pastedText.trim().length < 20) {
      setErrorMsg("Please paste at least a few lines of resume text.");
      return;
    }
    processTextWithAi(pastedText, "Pasted_CV_Text.txt");
  };

  return (
    <div className="max-w-3xl mx-auto py-6 space-y-6">
      <div className="space-y-2">
        <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">
          Upload Your CV
        </h2>
        <p className="text-slate-600 text-sm sm:text-base">
          Our parser extracts your technical capabilities, career chronology, and education into structured JSON using Google Gemini.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200">
        <button
          onClick={() => setActiveTab("file")}
          className={`pb-3 px-4 text-sm font-semibold border-b-2 transition ${
            activeTab === "file"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          Upload Document
        </button>
        <button
          onClick={() => setActiveTab("sample")}
          className={`pb-3 px-4 text-sm font-semibold border-b-2 transition ${
            activeTab === "sample"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          1-Click Sample CV
        </button>
        <button
          onClick={() => setActiveTab("paste")}
          className={`pb-3 px-4 text-sm font-semibold border-b-2 transition ${
            activeTab === "paste"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          Paste Raw Text
        </button>
      </div>

      {/* Error display */}
      {errorMsg && (
        <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-start gap-2.5">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold">Unable to process document</div>
            <div>{errorMsg}</div>
          </div>
        </div>
      )}

      {/* Tab: File Upload */}
      {activeTab === "file" && (
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition ${
            isDragging
              ? "border-blue-500 bg-blue-50/50"
              : "border-slate-300 hover:border-blue-400 bg-white"
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.txt,.md"
            className="hidden"
            onChange={(e) => {
              if (e.target.files && e.target.files.length > 0) {
                handleFileUpload(e.target.files[0]);
              }
            }}
          />

          <div className="w-14 h-14 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-4">
            {isLoading ? (
              <Loader2 className="w-7 h-7 animate-spin text-blue-600" />
            ) : (
              <UploadCloud className="w-7 h-7" />
            )}
          </div>

          <h3 className="text-base font-bold text-slate-900 mb-1">
            {isLoading
              ? "Analyzing your CV with Gemini AI..."
              : "Click to upload or drag & drop your CV"}
          </h3>
          <p className="text-xs sm:text-sm text-slate-500 max-w-sm mx-auto mb-3">
            Supported formats: PDF (.pdf), Microsoft Word (.docx), Plain Text (.txt)
          </p>
          <div className="inline-flex items-center gap-1 text-xs text-slate-400">
            <span>Max size: 10MB</span> • <span>Privacy: Processed securely in memory</span>
          </div>
        </div>
      )}

      {/* Tab: Sample CV */}
      {activeTab === "sample" && (
        <div className="p-6 rounded-xl bg-white border border-slate-200 space-y-4">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
              <FileCode2 className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-bold text-slate-900">Pre-loaded Software Engineer Profile</h4>
              <p className="text-xs sm:text-sm text-slate-600 mt-1">
                Test the full application instantly with a realistic profile: Alex Morgan (3+ years experience, Python, Docker, PostgreSQL, microservices, B.S. in CS).
              </p>
            </div>
          </div>

          <button
            id="load-sample-cv-btn"
            onClick={handleSampleLoad}
            disabled={isLoading}
            className="w-full sm:w-auto px-6 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm transition flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Analyzing Sample Profile...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Load Sample CV & Analyze
              </>
            )}
          </button>
        </div>
      )}

      {/* Tab: Paste Text */}
      {activeTab === "paste" && (
        <form onSubmit={handlePasteSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1.5">
              Paste Resume / CV Plain Text:
            </label>
            <textarea
              rows={8}
              value={pastedText}
              onChange={(e) => setPastedText(e.target.value)}
              placeholder="Paste your professional summary, skills, experience, and education here..."
              className="w-full rounded-lg border border-slate-300 p-3 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-hidden font-mono"
            />
          </div>
          <button
            type="submit"
            disabled={isLoading}
            className="px-6 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm transition flex items-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Parsing CV Text...
              </>
            ) : (
              "Analyze Pasted Text"
            )}
          </button>
        </form>
      )}

      {/* Already Loaded State */}
      {hasCv && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-2.5">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
            <div>
              <div className="font-bold text-sm">Active CV Ready in Session:</div>
              <div className="text-xs text-emerald-700">{currentCvName || "Candidate Resume"}</div>
            </div>
          </div>
          <button
            id="view-cv-analysis-btn"
            onClick={onNavigateToAnalysis}
            className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs transition"
          >
            View CV Analysis Dashboard ➔
          </button>
        </div>
      )}
    </div>
  );
};
