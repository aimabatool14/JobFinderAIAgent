import React, { useState, useEffect } from "react";
import { Job, CVAnalysis, PageId } from "../types";
import { Search, MapPin, Briefcase, ExternalLink, ArrowRight, Sparkles, Filter } from "lucide-react";

interface FindJobsSectionProps {
  cv: CVAnalysis | null;
  onSelectJobForMatch: (job: Job) => void;
  onNavigate: (page: PageId) => void;
}

export const FindJobsSection: React.FC<FindJobsSectionProps> = ({
  cv,
  onSelectJobForMatch,
  onNavigate,
}) => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [location, setLocation] = useState("");
  const [jobType, setJobType] = useState("All");

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (query) params.append("query", query);
      if (location) params.append("location", location);
      if (jobType && jobType !== "All") params.append("job_type", jobType);

      if (cv && cv.technical_skills) {
        params.append("skills", cv.technical_skills.join(","));
      }

      const res = await fetch(`/api/jobs?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setJobs(data.jobs || []);
      }
    } catch (e) {
      console.error("Failed to load jobs", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, [cv]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchJobs();
  };

  return (
    <div className="max-w-5xl mx-auto py-6 space-y-6">
      <div>
        <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">
          Find Jobs
        </h2>
        <p className="text-sm text-slate-600">
          Search open engineering opportunities or test with curated role specifications. 
          {cv ? " Estimated CV match scores are computed using your extracted skills." : " Upload a CV to unlock instant match estimations."}
        </p>
      </div>

      {/* Search Bar */}
      <form onSubmit={handleSearch} className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs grid grid-cols-1 sm:grid-cols-12 gap-3">
        <div className="sm:col-span-5 relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3.5" />
          <input
            type="text"
            placeholder="Title, technology, or keywords (e.g. Python, React)..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-hidden"
          />
        </div>

        <div className="sm:col-span-3 relative">
          <MapPin className="w-4 h-4 text-slate-400 absolute left-3 top-3.5" />
          <input
            type="text"
            placeholder="Location (e.g. Remote)..."
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-hidden"
          />
        </div>

        <div className="sm:col-span-2">
          <select
            value={jobType}
            onChange={(e) => setJobType(e.target.value)}
            className="w-full py-2 px-3 text-sm rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-hidden bg-white text-slate-700"
          >
            <option value="All">All Types</option>
            <option value="Full-time">Full-time</option>
            <option value="Hybrid">Hybrid</option>
            <option value="Contract">Contract</option>
          </select>
        </div>

        <div className="sm:col-span-2">
          <button
            type="submit"
            className="w-full py-2 px-4 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm transition"
          >
            Search
          </button>
        </div>
      </form>

      {/* Results Header */}
      <div className="flex items-center justify-between text-xs text-slate-500 px-1">
        <span>Showing {jobs.length} open position{jobs.length === 1 ? "" : "s"}</span>
        <span className="bg-slate-100 px-2 py-0.5 rounded text-slate-600 font-medium">
          Source: Demo Dataset (Hackathon Prototype)
        </span>
      </div>

      {/* Jobs List */}
      <div className="space-y-4">
        {loading ? (
          <div className="text-center py-12 text-slate-500 text-sm">
            Searching job postings...
          </div>
        ) : jobs.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-xl border border-slate-200">
            <Briefcase className="w-8 h-8 text-slate-400 mx-auto mb-2" />
            <div className="font-semibold text-slate-800">No jobs found</div>
            <div className="text-xs text-slate-500 mt-1">Try adjusting your search terms or filters.</div>
          </div>
        ) : (
          jobs.map((job) => (
            <div
              key={job.id}
              className="p-5 rounded-xl bg-white border border-slate-200 shadow-xs hover:border-slate-300 transition space-y-3"
            >
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2">
                <div>
                  <h3 className="text-base font-bold text-slate-900">{job.title}</h3>
                  <div className="text-xs font-semibold text-blue-600 mt-0.5">
                    {job.company} • <span className="text-slate-500 font-normal">{job.location} ({job.job_type})</span>
                    {job.salary_range && (
                      <span className="text-slate-700 font-medium ml-2">💰 {job.salary_range}</span>
                    )}
                  </div>
                </div>

                {job.match_score !== undefined && job.match_score !== null && (
                  <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-800 border border-emerald-200 shrink-0">
                    <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
                    Estimated Match: ~{job.match_score}%
                  </div>
                )}
              </div>

              <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                {job.short_description}
              </p>

              {/* Skills */}
              <div className="flex flex-wrap gap-1.5 pt-1">
                {job.required_skills.map((skill, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200"
                  >
                    {skill}
                  </span>
                ))}
              </div>

              {/* Actions */}
              <div className="pt-2 flex flex-wrap items-center justify-between gap-2 border-t border-slate-100">
                <button
                  id={`match-btn-${job.id}`}
                  onClick={() => onSelectJobForMatch(job)}
                  className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs transition inline-flex items-center gap-1.5"
                >
                  Match My CV with This Job ➔
                </button>

                {job.url && (
                  <a
                    href={job.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-xs text-slate-500 hover:text-slate-800 inline-flex items-center gap-1"
                  >
                    Original Posting
                    <ExternalLink className="w-3 h-3" />
                  </a>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
