export type PageId =
  | "Home"
  | "Welcome"
  | "Upload CV"
  | "CV Analysis"
  | "Find Jobs"
  | "Job Match"
  | "CV Improvement"
  | "About";

export interface EducationItem {
  degree: string;
  institution: string;
  year?: string;
  details?: string;
}

export interface WorkExperienceItem {
  role: string;
  company: string;
  duration?: string;
  years?: number;
  bullet_points: string[];
}

export interface ProjectItem {
  name: string;
  description: string;
  technologies?: string[];
  url?: string;
}

export interface CVAnalysis {
  name?: string;
  professional_summary: string;
  skills: string[];
  technical_skills: string[];
  soft_skills: string[];
  education: EducationItem[];
  certifications: string[];
  work_experience: WorkExperienceItem[];
  projects: ProjectItem[];
  years_of_experience?: number | null;
  languages: string[];
  _demoMode?: boolean;
}

export interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  job_type: string;
  salary_range?: string;
  required_skills: string[];
  nice_to_have_skills?: string[];
  short_description: string;
  full_description: string;
  source: string;
  url?: string;
  is_demo?: boolean;
  match_score?: number | null;
}

export interface JobMatchResult {
  overall_match_percentage: number;
  compatibility_label: string;
  matching_skills: string[];
  missing_skills: string[];
  partially_matching_skills: string[];
  experience_match_score: number;
  experience_match_description: string;
  education_match_score: number;
  education_match_description: string;
  project_relevance_score: number;
  project_relevance_description: string;
  strengths: string[];
  weaknesses_and_gaps: string[];
  recommendations: string[];
  score_calculation_explanation: string;
  _demoMode?: boolean;
}

export interface BulletPointImprovement {
  original_or_section: string;
  suggested_revision: string;
  reason: string;
}

export interface CVImprovementResult {
  missing_keywords: string[];
  skills_to_emphasize: string[];
  weak_sections: string[];
  suggested_bullet_point_improvements: BulletPointImprovement[];
  tailoring_recommendations: string[];
  ethical_guidance: string;
  _demoMode?: boolean;
}
