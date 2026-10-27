// API client — fetch wrapper with Bearer auth + refresh-on-401 (BLUEPRINT §3/§4)

import type {
  TokenResponse,
  User,
  ResumeResponse,
  ResumeListResponse,
  InterviewResponse,
  InterviewListWrapper,
  GapAnalysis,
  InterviewReport,
  CreateInterviewPayload,
} from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, "") || "http://localhost:8000";
const PREFIX = "/api/v1";
const REFRESH_KEY = "aimi_refresh_token";

// ---- token store (access in memory, refresh in localStorage) ----
let accessToken: string | null = null;

export const tokenStore = {
  getAccess: () => accessToken,
  setAccess: (t: string | null) => {
    accessToken = t;
  },
  getRefresh: (): string | null => {
    if (typeof window === "undefined") return null;
    try {
      return window.localStorage.getItem(REFRESH_KEY);
    } catch {
      return null;
    }
  },
  setRefresh: (t: string | null) => {
    if (typeof window === "undefined") return;
    try {
      if (t) window.localStorage.setItem(REFRESH_KEY, t);
      else window.localStorage.removeItem(REFRESH_KEY);
    } catch {
      /* ignore */
    }
  },
  clear: () => {
    accessToken = null;
    tokenStore.setRefresh(null);
  },
};

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

function url(path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE}${PREFIX}${p}`;
}

export function wsUrl(interviewId: string): string {
  const base = API_BASE.replace(/^http/, "ws");
  const token = accessToken ?? "";
  return `${base}${PREFIX}/ws/chat/${interviewId}?token=${encodeURIComponent(token)}`;
}

async function rawFetch(path: string, init: RequestInit, auth: boolean): Promise<Response> {
  const headers = new Headers(init.headers);
  if (auth && accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  return fetch(url(path), { ...init, headers });
}

async function tryRefresh(): Promise<boolean> {
  const refresh = tokenStore.getRefresh();
  if (!refresh) return false;
  try {
    const res = await fetch(url("/auth/refresh"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refresh }),
    });
    if (!res.ok) return false;
    const data: TokenResponse = await res.json();
    tokenStore.setAccess(data.access_token);
    tokenStore.setRefresh(data.refresh_token);
    return true;
  } catch {
    return false;
  }
}

/** Ensure a usable access token is in memory, refreshing from the stored
 *  refresh token if needed. Used before opening the interview WebSocket, whose
 *  auth travels as a query param (so it can't trigger refresh-on-401/403). */
export async function ensureToken(): Promise<boolean> {
  if (accessToken) return true;
  return tryRefresh();
}

async function parseError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (typeof data?.detail === "string") return data.detail;
    if (Array.isArray(data?.detail) && data.detail[0]?.msg) return data.detail[0].msg;
    if (typeof data?.message === "string") return data.message;
  } catch {
    /* ignore */
  }
  return `Request failed (${res.status})`;
}

interface RequestOpts {
  method?: string;
  body?: unknown;
  auth?: boolean;
  isForm?: boolean;
}

export async function apiFetch<T>(path: string, opts: RequestOpts = {}): Promise<T> {
  const { method = "GET", body, auth = true, isForm = false } = opts;

  const init: RequestInit = { method };
  if (body !== undefined) {
    if (isForm) {
      init.body = body as BodyInit;
    } else {
      init.headers = { "Content-Type": "application/json" };
      init.body = JSON.stringify(body);
    }
  }

  let res = await rawFetch(path, init, auth);

  // Refresh on 401 OR 403: a request sent with no access token (e.g. right
  // after a page reload, when the access token lives only in memory) gets a
  // 403 from FastAPI's HTTPBearer, not a 401 — so we must handle both to
  // rehydrate the session instead of bouncing the user to /login.
  if ((res.status === 401 || res.status === 403) && auth && tokenStore.getRefresh()) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      res = await rawFetch(path, init, auth);
    } else {
      tokenStore.clear();
      throw new ApiError("Session expired. Please log in again.", 401);
    }
  }

  if (!res.ok) throw new ApiError(await parseError(res), res.status);

  if (res.status === 204) return undefined as T;
  const text = await res.text();
  return (text ? JSON.parse(text) : undefined) as T;
}

// ---- typed endpoints ----
export const api = {
  register: (username: string, email: string, password: string) =>
    apiFetch<TokenResponse>("/auth/register", {
      method: "POST",
      auth: false,
      body: { username, email, password },
    }),

  login: (email: string, password: string) =>
    apiFetch<TokenResponse>("/auth/login", {
      method: "POST",
      auth: false,
      body: { email, password },
    }),

  me: () => apiFetch<User>("/auth/me"),

  uploadResume: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return apiFetch<ResumeResponse>("/resumes/upload", {
      method: "POST",
      body: form,
      isForm: true,
    });
  },

  listResumes: () => apiFetch<ResumeListResponse>("/resumes/"),
  getResume: (id: string) => apiFetch<ResumeResponse>(`/resumes/${id}`),
  deleteResume: (id: string) =>
    apiFetch<{ message: string; success: boolean }>(`/resumes/${id}`, { method: "DELETE" }),

  gapAnalysis: (resume_id: string, job_description: string) =>
    apiFetch<GapAnalysis>("/analysis/gap", {
      method: "POST",
      body: { resume_id, job_description },
    }),

  createInterview: (payload: CreateInterviewPayload) =>
    apiFetch<InterviewResponse>("/interviews/", {
      method: "POST",
      body: { num_questions: 8, ...payload },
    }),

  listInterviews: () => apiFetch<InterviewListWrapper>("/interviews/"),
  getInterview: (id: string) => apiFetch<InterviewResponse>(`/interviews/${id}`),
  completeInterview: (id: string) =>
    apiFetch<InterviewResponse>(`/interviews/${id}/complete`, { method: "PUT" }),
  getReport: (id: string) => apiFetch<InterviewReport>(`/interviews/${id}/report`),
};

export { API_BASE };
