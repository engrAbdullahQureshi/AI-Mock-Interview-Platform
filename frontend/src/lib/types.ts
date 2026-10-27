// API types — mirror backend contract (BLUEPRINT §4)

export interface User {
  id: string;
  username: string;
  email: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface WorkExperience {
  company: string | null;
  position: string | null;
  duration: string | null;
  description: string | null;
}

export interface Education {
  institution: string | null;
  degree: string | null;
  field: string | null;
  year: string | null;
}

export interface ParsedResumeData {
  full_name: string | null;
  email: string | null;
  phone: string | null;
  location: string | null;
  summary: string | null;
  skills: string[];
  work_experience: WorkExperience[];
  education: Education[];
  certifications: string[];
  languages: string[];
}

export interface ResumeResponse {
  id: string;
  user_id: string;
  file_name: string;
  file_size: number;
  uploaded_at: string;
  raw_text?: string | null;
  parsed_data: ParsedResumeData | null;
}

export interface ResumeListResponse {
  resumes: ResumeResponse[];
  total: number;
}

export type InterviewStatus = "active" | "completed";

export interface InterviewResponse {
  id: string;
  user_id: string;
  resume_id: string;
  title: string;
  job_title: string;
  questions: string[];
  status: InterviewStatus;
  created_at: string;
  completed_at?: string | null;
}

export interface InterviewListResponse {
  id: string;
  title: string;
  job_title: string;
  status: InterviewStatus;
  created_at: string;
  completed_at?: string | null;
  question_count: number;
}

export interface InterviewListWrapper {
  interviews: InterviewListResponse[];
  total: number;
}

export interface GapAnalysis {
  match_score: number;
  verdict: string;
  matched_skills: string[];
  missing_skills: string[];
  summary: string;
  resume_id: string;
}

export interface Dimensions {
  relevance: number;
  technical_depth: number;
  communication: number;
  specificity: number;
  jd_alignment: number;
}

export interface PerQuestion {
  index: number;
  question: string;
  answer: string;
  scores: Dimensions;
  feedback: string;
}

export interface InterviewReport {
  interview_id: string;
  job_title: string;
  completed_at: string | null;
  overall_score: number;
  verdict: string;
  dimensions: Dimensions;
  strengths: string[];
  improvements: string[];
  jd_gap_recap: string;
  per_question: PerQuestion[];
}

export interface CreateInterviewPayload {
  resume_id: string;
  job_title: string;
  num_questions?: number;
  job_description?: string;
  focus_skills?: string[];
}

// WebSocket message shapes (server → client)
export interface WsMessage {
  type: "ai" | "complete" | "error" | "info";
  content: string;
  question_index?: number;
  total_questions?: number;
  session_id?: string;
}

export const DIMENSION_LABELS: Record<keyof Dimensions, string> = {
  relevance: "Relevance",
  technical_depth: "Technical Depth",
  communication: "Communication",
  specificity: "Specificity",
  jd_alignment: "JD Alignment",
};
