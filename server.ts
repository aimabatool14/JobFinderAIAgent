import express from "express";
import path from "path";
import dotenv from "dotenv";
import { GoogleGenAI } from "@google/genai";
import { createServer as createViteServer } from "vite";

dotenv.config();

const app = express();
const PORT = 3000;

app.use(express.json({ limit: "10mb" }));

// Initialize Google GenAI client lazily
function getGeminiClient(): GoogleGenAI | null {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey || apiKey === "MY_GEMINI_API_KEY") {
    return null;
  }
  return new GoogleGenAI({
    apiKey,
    httpOptions: {
      headers: {
        "User-Agent": "aistudio-build",
      },
    },
  });
}

// Health check endpoint
app.get("/api/health", (_req, res) => {
  res.json({ status: "ok", service: "JobFinder AI" });
});

// Status check (never exposes secret key)
app.get("/api/status", (_req, res) => {
  const configured = !!(process.env.GEMINI_API_KEY && process.env.GEMINI_API_KEY !== "MY_GEMINI_API_KEY");
  res.json({ configured, model: "gemini-3.8-flash" });
});

// Demo Jobs data
const DEMO_JOBS = [
  {
    id: "job-demo-01",
    title: "Backend Software Engineer (Python / FastAPI)",
    company: "Kinetix Cloud Technologies",
    location: "Remote (US/Europe)",
    job_type: "Full-time",
    salary_range: "$115,000 - $145,000",
    required_skills: ["Python", "FastAPI", "Docker", "PostgreSQL", "REST APIs", "Redis"],
    nice_to_have_skills: ["Kubernetes", "AWS", "Kafka", "GraphQL"],
    short_description: "Join our distributed infrastructure team building high-throughput event processing and scalable microservice APIs.",
    full_description: `Role Overview:
We are seeking a Backend Software Engineer with deep Python expertise to build resilient microservice APIs. You will partner with front-end engineers and DevOps specialists to design high-performance data systems.

Key Responsibilities:
- Design, implement, and maintain low-latency REST and async APIs using Python and FastAPI.
- Model and optimize queries for PostgreSQL and caching layers with Redis.
- Package services in Docker containers and automate CI/CD pipeline deployments.
- Participate in architectural reviews, automated testing, and sprint planning.

Requirements:
- 3+ years of professional backend development with Python.
- Proven experience with FastAPI, Flask, or Django in production.
- Solid understanding of relational databases (PostgreSQL) and schema migrations.
- Working knowledge of Docker containerization and Git workflows.
- Bachelor's in Computer Science, related technical field, or equivalent practical experience.`,
    source: "Demo Dataset (Hackathon Prototype)",
    url: "https://example.com/careers/kinetix-backend-engineer",
    is_demo: true,
  },
  {
    id: "job-demo-02",
    title: "Full Stack Engineer (React & Node.js)",
    company: "NovaWave Interactive",
    location: "San Francisco, CA (Hybrid)",
    job_type: "Full-time",
    salary_range: "$125,000 - $160,000",
    required_skills: ["React", "TypeScript", "Node.js", "Tailwind CSS", "REST APIs", "Git"],
    nice_to_have_skills: ["Next.js", "PostgreSQL", "Docker", "Testing Library"],
    short_description: "Build user-centric collaborative web applications with modern React, TypeScript, and Node.js microservices.",
    full_description: `Role Overview:
NovaWave is designing the future of digital workplace collaboration tools. We are looking for an experienced Full Stack Engineer who loves crafting responsive interfaces and reliable server logic.

Key Responsibilities:
- Build state-of-the-art interactive front-ends using React 18+, TypeScript, and Tailwind CSS.
- Develop secure, well-tested Node.js backend routes and real-time WebSocket services.
- Optimize client-side render cycles and bundle sizes.
- Work closely with UI/UX designers to translate Figma specifications into fluid components.

Requirements:
- 3+ years full-stack web application engineering experience.
- Deep expertise in modern JavaScript/TypeScript, React hooks, and component lifecycle.
- Practical experience designing RESTful APIs in Node.js / Express.
- Passion for accessibility, performance profiling, and responsive layouts.`,
    source: "Demo Dataset (Hackathon Prototype)",
    url: "https://example.com/careers/novawave-fullstack-dev",
    is_demo: true,
  },
  {
    id: "job-demo-03",
    title: "Junior Machine Learning Engineer",
    company: "Synthetica AI Labs",
    location: "Boston, MA / Remote",
    job_type: "Full-time",
    salary_range: "$95,000 - $120,000",
    required_skills: ["Python", "PyTorch", "NumPy", "Pandas", "Scikit-Learn", "Git"],
    nice_to_have_skills: ["Hugging Face", "LLMs", "FastAPI", "Docker", "MLflow"],
    short_description: "Assist in training, fine-tuning, and evaluating cutting-edge foundation models and natural language processing pipelines.",
    full_description: `Role Overview:
Synthetica AI Labs is accelerating enterprise adoption of generative AI. We are hiring a Junior ML Engineer to support our model fine-tuning, retrieval evaluation, and data preparation pipelines.

Key Responsibilities:
- Clean, curate, and preprocess large unstructured text and multimodal datasets.
- Implement evaluation benchmarks for LLMs and domain-specific embeddings.
- Collaborate with senior scientists to deploy model inference wrappers using FastAPI and Docker.
- Monitor model drift and output safety metrics.

Requirements:
- Strong programming fundamentals in Python, Pandas, and NumPy.
- Familiarity with PyTorch or TensorFlow, and transformer architectures.
- Demonstrated portfolio or GitHub repository with ML coursework or projects.
- Bachelor's degree in Computer Science, Data Science, Math, or relevant field.`,
    source: "Demo Dataset (Hackathon Prototype)",
    url: "https://example.com/careers/synthetica-ml-engineer",
    is_demo: true,
  },
  {
    id: "job-demo-04",
    title: "Cloud DevOps & Platform Engineer",
    company: "Aether Infrastructures",
    location: "London, UK / Remote",
    job_type: "Full-time",
    salary_range: "£75,000 - £95,000",
    required_skills: ["Docker", "Kubernetes", "AWS", "Terraform", "CI/CD", "Linux"],
    nice_to_have_skills: ["Python", "Go", "Prometheus", "Grafana", "Security Hardening"],
    short_description: "Scale our multi-region Kubernetes clusters, infrastructure as code, and automated zero-downtime deployment pipelines.",
    full_description: `Role Overview:
Help us maintain 99.99% reliability across critical multi-cloud deployments. You will architect infrastructure templates, build observability dashboards, and automate deployment workflows.

Key Responsibilities:
- Manage Amazon Web Services (AWS) infrastructure using Terraform.
- Oversee Kubernetes (EKS) workload autoscaling and container security policies.
- Build resilient GitHub Actions and GitLab CI/CD pipelines.
- Establish automated alerting with Prometheus and Grafana.

Requirements:
- 3+ years managing production Linux infrastructure in public cloud environments (AWS/GCP).
- Hands-on Kubernetes deployment and Helm packaging experience.
- Proficient in Terraform, bash scripting, or Python automation.`,
    source: "Demo Dataset (Hackathon Prototype)",
    url: "https://example.com/careers/aether-devops-engineer",
    is_demo: true,
  },
  {
    id: "job-demo-05",
    title: "Data Analyst / Analytics Engineer",
    company: "Horizon Consumer Goods",
    location: "Chicago, IL (Hybrid)",
    job_type: "Full-time",
    salary_range: "$85,000 - $110,000",
    required_skills: ["SQL", "Python", "Tableau", "Data Modeling", "Excel"],
    nice_to_have_skills: ["dbt", "Snowflake", "BigQuery", "Statistical Analysis"],
    short_description: "Translate complex transactional data into actionable business intelligence, KPI dashboards, and predictive insights.",
    full_description: `Role Overview:
Join our Commercial Intelligence unit to empower product managers and executives with trusted analytics dashboards and strategic growth insights.

Key Responsibilities:
- Write complex SQL queries, views, and data transformation scripts.
- Build executive KPI dashboards in Tableau and Power BI.
- Perform exploratory statistical analysis in Python (Jupyter, Pandas).
- Partner with marketing and finance leaders to analyze customer retention funnels.

Requirements:
- Advanced SQL proficiency (window functions, query optimization, CTEs).
- Proven experience creating insightful visualizations in Tableau or PowerBI.
- Working knowledge of Python for data manipulation.`,
    source: "Demo Dataset (Hackathon Prototype)",
    url: "https://example.com/careers/horizon-data-analyst",
    is_demo: true,
  },
  {
    id: "job-demo-06",
    title: "Frontend Developer (UI/UX & Web Performance)",
    company: "Pulse Creative Studio",
    location: "Berlin, Germany / Remote",
    job_type: "Full-time",
    salary_range: "€65,000 - €85,000",
    required_skills: ["React", "TypeScript", "CSS3", "HTML5", "Responsive Design", "Git"],
    nice_to_have_skills: ["Three.js", "Framer Motion", "Next.js", "Tailwind CSS"],
    short_description: "Craft high-polish, accessible user interfaces with micro-interactions and rigorous mobile responsiveness.",
    full_description: `Role Overview:
Pulse Creative Studio is searching for a detail-oriented Frontend Developer who bridges the gap between design vision and high-performance web implementation.

Key Responsibilities:
- Implement responsive, pixel-perfect web interfaces using modern React and CSS frameworks.
- Optimize Core Web Vitals (LCP, FID, CLS) and asset delivery.
- Ensure strict WCAG 2.1 AA accessibility compliance across all components.
- Collaborate with designers in Figma to refine animations and transitions.

Requirements:
- 2+ years professional frontend web development.
- Strong command of modern CSS (flexbox, grid, animations, custom properties).
- Solid proficiency in React and TypeScript.`,
    source: "Demo Dataset (Hackathon Prototype)",
    url: "https://example.com/careers/pulse-frontend-developer",
    is_demo: true,
  }
];

// Jobs endpoint with query and CV skills match calculation
app.get("/api/jobs", (req, res) => {
  const query = ((req.query.query as string) || "").toLowerCase().trim();
  const location = ((req.query.location as string) || "").toLowerCase().trim();
  const jobType = ((req.query.job_type as string) || "All").toLowerCase().trim();
  const skillsHeader = (req.query.skills as string) || "";
  const candidateSkills = skillsHeader ? skillsHeader.split(",").map(s => s.trim().toLowerCase()) : [];

  let filtered = DEMO_JOBS.filter(job => {
    if (query) {
      const matchQ = job.title.toLowerCase().includes(query) ||
        job.company.toLowerCase().includes(query) ||
        job.required_skills.some(s => s.toLowerCase().includes(query)) ||
        job.short_description.toLowerCase().includes(query);
      if (!matchQ) return false;
    }
    if (location && !job.location.toLowerCase().includes(location)) {
      return false;
    }
    if (jobType && jobType !== "all" && !job.job_type.toLowerCase().includes(jobType)) {
      return false;
    }
    return true;
  });

  const enriched = filtered.map(job => {
    let matchScore = null;
    if (candidateSkills.length > 0) {
      const reqSkills = job.required_skills.map(s => s.toLowerCase());
      const matchedCount = reqSkills.filter(r => candidateSkills.some(c => c.includes(r) || r.includes(c))).length;
      matchScore = Math.min(Math.max(Math.round((matchedCount / reqSkills.length) * 100), 25), 98);
    }
    return { ...job, match_score: matchScore };
  });

  res.json({ jobs: enriched, source: "Demo Dataset (Hackathon Prototype)" });
});

// Helper to clean JSON string from LLM response
function parseModelJson(raw: string) {
  let text = raw.trim();
  if (text.startsWith("```")) {
    const match = text.match(/^```(?:json)?\s*([\s\S]*?)\s*```$/);
    if (match) text = match[1].trim();
    else {
      const lines = text.split("\n");
      text = lines.slice(1, -1).join("\n").trim();
    }
  }
  return JSON.parse(text);
}

// 1. Analyze CV Endpoint
app.post("/api/analyze-cv", async (req, res) => {
  try {
    const { cvText } = req.body;
    if (!cvText || typeof cvText !== "string" || cvText.trim().length < 15) {
      return res.status(400).json({ error: "Please provide valid CV text (at least 15 characters)." });
    }

    const ai = getGeminiClient();
    if (!ai) {
      // Fallback heuristic analyzer for demo mode
      const lines = cvText.split("\n").map(l => l.trim()).filter(Boolean);
      const name = lines[0] && lines[0].length < 40 ? lines[0] : "Alex Morgan";
      const techKeywords = ["Python", "JavaScript", "TypeScript", "React", "Docker", "SQL", "PostgreSQL", "REST APIs", "Git", "Node.js", "FastAPI", "AWS", "Linux"];
      const softKeywords = ["Problem Solving", "Collaboration", "Agile", "Communication", "Leadership"];

      const techFound = techKeywords.filter(k => cvText.toLowerCase().includes(k.toLowerCase()));
      const softFound = softKeywords.filter(k => cvText.toLowerCase().includes(k.toLowerCase()));

      return res.json({
        name,
        professional_summary: "Software Engineer with practical experience in full-stack web application development, microservices architecture, and agile software delivery.",
        skills: [...(techFound.length ? techFound : ["Python", "Docker", "SQL"]), ...(softFound.length ? softFound : ["Problem Solving", "Agile"])],
        technical_skills: techFound.length ? techFound : ["Python", "Docker", "PostgreSQL", "REST APIs", "Git"],
        soft_skills: softFound.length ? softFound : ["Problem Solving", "Cross-functional Collaboration", "Agile"],
        education: [
          { degree: "B.S. in Computer Science", institution: "University of Technology", year: "2022", details: "Major in Software Systems" }
        ],
        certifications: ["AWS Certified Cloud Practitioner"],
        work_experience: [
          {
            role: "Software Developer",
            company: "Apex Innovations",
            duration: "2022 - Present",
            years: 2.0,
            bullet_points: [
              "Engineered modular REST microservices handling 25,000 daily requests.",
              "Containerized core application components using Docker to accelerate CI/CD workflows."
            ]
          }
        ],
        projects: [
          { name: "Task Automation Pipeline", description: "Automated queue service built with Python and Redis.", technologies: ["Python", "Redis", "Docker"] }
        ],
        years_of_experience: 2.5,
        languages: ["English (Fluent)", "Spanish (Conversational)"],
        _demoMode: true,
      });
    }

    const systemInstruction = `You are an expert HR analyst, technical recruiter, and CV parsing specialist.
Analyze the CV text and extract structured information into strictly valid JSON.
Fields required:
- name: string (or 'Candidate')
- professional_summary: string
- skills: array of strings
- technical_skills: array of strings
- soft_skills: array of strings
- education: array of objects {degree, institution, year, details}
- certifications: array of strings
- work_experience: array of objects {role, company, duration, years, bullet_points}
- projects: array of objects {name, description, technologies, url}
- years_of_experience: number or null
- languages: array of strings
Return ONLY JSON. Do not fabricate facts not in the CV.`;

    const response = await ai.models.generateContent({
      model: "gemini-3.8-flash",
      contents: `Parse this CV:\n\n${cvText}`,
      config: {
        systemInstruction,
        responseMimeType: "application/json",
        temperature: 0.1,
      },
    });

    const parsed = parseModelJson(response.text || "{}");
    res.json(parsed);
  } catch (error: any) {
    console.error("Error in /api/analyze-cv:", error);
    res.status(500).json({ error: error.message || "Failed to analyze CV." });
  }
});

// 2. Match Job Endpoint
app.post("/api/match-job", async (req, res) => {
  try {
    const { cvData, jobDescription } = req.body;
    if (!jobDescription || typeof jobDescription !== "string" || !jobDescription.trim()) {
      return res.status(400).json({ error: "Job description is required." });
    }
    if (!cvData) {
      return res.status(400).json({ error: "CV data is required." });
    }

    const ai = getGeminiClient();
    if (!ai) {
      // Heuristic matching fallback for demo mode
      const jdLower = jobDescription.toLowerCase();
      const cvSkills = (cvData.technical_skills || cvData.skills || []).map((s: string) => s.toLowerCase());
      const vocab = ["python", "fastapi", "docker", "kubernetes", "sql", "postgresql", "react", "typescript", "aws", "redis", "rest apis", "ci/cd"];
      const jdFound = vocab.filter(v => jdLower.includes(v));

      const matching = jdFound.filter(j => cvSkills.some((c: string) => c.includes(j) || j.includes(c))).map(s => s.toUpperCase());
      const missing = jdFound.filter(j => !cvSkills.some((c: string) => c.includes(j) || j.includes(c))).map(s => s.toUpperCase());

      const score = Math.min(Math.max(Math.round(((matching.length + 1) / (jdFound.length || 1)) * 90), 40), 96);

      return res.json({
        overall_match_percentage: score,
        compatibility_label: `AI Compatibility Score: ${score}%`,
        matching_skills: matching.length ? matching : ["PYTHON", "SQL", "DOCKER"],
        missing_skills: missing.length ? missing : ["KUBERNETES", "FASTAPI"],
        partially_matching_skills: ["Flask/Django (Adjacent to FastAPI)"],
        experience_match_score: 85,
        experience_match_description: "Candidate demonstrates 2.5-3 years practical experience meeting the requirements.",
        education_match_score: 90,
        education_match_description: "Technical degree aligns with standard role requirements.",
        project_relevance_score: 80,
        project_relevance_description: "Project work demonstrates direct application of microservice patterns.",
        strengths: [
          `Strong proficiency in core technologies: ${matching.slice(0, 3).join(", ") || "Python, Docker"}.`,
          "Solid history of building and containerizing backend services."
        ],
        weaknesses_and_gaps: [
          `The job specifically asks for ${missing.slice(0, 2).join(", ") || "FastAPI and Kubernetes"}, which are not explicitly highlighted in your CV.`
        ],
        recommendations: [
          "Highlight any exposure to asynchronous frameworks in your personal project descriptions.",
          "Add container orchestration or deployment pipelines to your competencies."
        ],
        score_calculation_explanation: `Calculated as 45% skills alignment (${Math.round(score * 0.45)}/45) + 25% experience depth (21/25) + 15% education (14/15) + 15% project relevance (12/15) = ${score}% AI Compatibility Score. Note: This is an algorithmic semantic estimate, not an objective hiring probability.`,
        _demoMode: true,
      });
    }

    const systemInstruction = `You are a senior technical hiring evaluator.
Compare the candidate's CV data against the provided Job Description.
Calculate a multi-factor compatibility evaluation.
Requirements:
1. overall_match_percentage: integer (0 to 100)
2. compatibility_label: string e.g. "AI Compatibility Score: 82%"
3. matching_skills: array of strings
4. missing_skills: array of strings
5. partially_matching_skills: array of strings
6. experience_match_score: integer (0 to 100)
7. experience_match_description: string
8. education_match_score: integer (0 to 100)
9. education_match_description: string
10. project_relevance_score: integer (0 to 100)
11. project_relevance_description: string
12. strengths: array of strings
13. weaknesses_and_gaps: array of strings
14. recommendations: array of strings
15. score_calculation_explanation: string (transparent explanation of the percentage breakdown, stating it is an AI compatibility estimate and not a hiring guarantee)
Return strictly valid JSON.`;

    const response = await ai.models.generateContent({
      model: "gemini-3.8-flash",
      contents: `CANDIDATE CV DATA:\n${JSON.stringify(cvData, null, 2)}\n\nJOB DESCRIPTION:\n${jobDescription}`,
      config: {
        systemInstruction,
        responseMimeType: "application/json",
        temperature: 0.15,
      },
    });

    const parsed = parseModelJson(response.text || "{}");
    res.json(parsed);
  } catch (error: any) {
    console.error("Error in /api/match-job:", error);
    res.status(500).json({ error: error.message || "Failed to compare CV and Job Description." });
  }
});

// 3. Improve CV Endpoint
app.post("/api/improve-cv", async (req, res) => {
  try {
    const { cvText, jobDescription } = req.body;
    if (!cvText || !jobDescription) {
      return res.status(400).json({ error: "Both cvText and jobDescription are required." });
    }

    const ai = getGeminiClient();
    if (!ai) {
      return res.json({
        missing_keywords: ["FastAPI", "AsyncIO", "CI/CD Pipelines", "Container Orchestration", "PostgreSQL"],
        skills_to_emphasize: ["Python backend architecture", "Docker containerization", "Database optimization", "REST APIs"],
        weak_sections: [
          "Work experience bullet points focus on responsibilities rather than quantified business outcomes.",
          "Professional summary lacks specific mention of target specialization keywords."
        ],
        suggested_bullet_point_improvements: [
          {
            original_or_section: "Built backend APIs for company web platform.",
            suggested_revision: "Architected 14+ secure RESTful API microservices using Python and Docker, serving 30,000+ daily requests with 99.9% uptime.",
            reason: "Applies Google XYZ accomplishment formula (Accomplished [X], measured by [Y], by doing [Z])."
          },
          {
            original_or_section: "Fixed bugs and improved database queries.",
            suggested_revision: "Optimized complex PostgreSQL queries and integrated Redis caching, reducing API response latency by 34%.",
            reason: "Surfaces concrete metrics and high-demand database caching skills."
          }
        ],
        tailoring_recommendations: [
          "Position your Python and API design experience in the top third of your resume.",
          "Mirror exact keywords from the job description in your core competencies list.",
          "Add a brief metrics-driven highlight to your most recent project description."
        ],
        ethical_guidance: "Recommendations are suggestions strictly derived from your real CV experience. Do not fabricate roles, credentials, or metrics.",
        _demoMode: true,
      });
    }

    const systemInstruction = `You are an executive resume coach and ATS optimization specialist.
Analyze how the candidate's CV can be ethically tailored for the target job.
CRITICAL ETHICAL RULES:
- Do NOT invent experiences, employers, degrees, certifications, or skills.
- Only suggest honest revisions, rephrasing, and keyword alignment from their existing background.
Return JSON with:
- missing_keywords: array of strings
- skills_to_emphasize: array of strings
- weak_sections: array of strings
- suggested_bullet_point_improvements: array of {original_or_section, suggested_revision, reason}
- tailoring_recommendations: array of strings
- ethical_guidance: string
Return strictly valid JSON.`;

    const response = await ai.models.generateContent({
      model: "gemini-3.8-flash",
      contents: `CV TEXT:\n${cvText}\n\nTARGET JOB DESCRIPTION:\n${jobDescription}`,
      config: {
        systemInstruction,
        responseMimeType: "application/json",
        temperature: 0.2,
      },
    });

    const parsed = parseModelJson(response.text || "{}");
    res.json(parsed);
  } catch (error: any) {
    console.error("Error in /api/improve-cv:", error);
    res.status(500).json({ error: error.message || "Failed to generate CV improvements." });
  }
});

// Vite middleware for development vs static build in production
async function startServer() {
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (_req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`JobFinder AI Server running on http://0.0.0.0:${PORT}`);
  });
}

startServer();
