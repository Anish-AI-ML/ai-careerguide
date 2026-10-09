import type { Profile } from './store'
const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const TOKEN = 'cg_token'
export const getToken = () => localStorage.getItem(TOKEN)
export const setToken = (t: string | null) => (t ? localStorage.setItem(TOKEN, t) : localStorage.removeItem(TOKEN))

export type ApiUser = { name: string; email: string }
export type Match = { id: string; career: string; match_score: number; reason: string; strengths: string[]; skill_gaps: string[]; breakdown: Record<string, number>; is_goal: boolean; disclaimer: string }
export type Analysis = { top: Match; alternatives: Match[]; weights_used: Record<string, number> }
export type Course = { id: string; title: string; platform: string; provider: string; difficulty: string; duration_hours: number; rating: number | null; url: string; prerequisites: string[]; free: boolean; covers: string[]; missing_prerequisites: string[]; reason: string }
export type CourseRecs = { career: string; career_id: string; match_score: number; courses: Course[]; uncovered_skills: string[] }
export type CareerInfo = { id: string; name: string }
export type RoadmapItem = { id: string; phase: number; title: string; skills: string[]; est_weeks: number; difficulty: string; courses: { id: string; title: string; url: string; platform: string; duration_hours: number }[]; projects: string[]; completed: boolean }
export type Roadmap = { id: string; career: string; career_id: string; progress_percent: number; total_weeks: number; items: RoadmapItem[] }
export type ResumeResult = {
  id: string; name: string | null; sections_found: string[]
  extracted: { education: string[]; skills: string[]; technologies: string[]; projects: string[]; experience: string[]; certifications: string[] }
  resume_score: number; score_breakdown: Record<string, { points: number; max: number }>
  target: { career: string; career_id: string }; role_match: { skills: number; projects: number; experience: number; overall: number }
  strengths: string[]; missing_keywords: string[]; technical_skill_gaps: string[]
  recommended_courses: { id: string; title: string; url: string; platform: string; reason: string }[]
  project_suggestions: string[]; ats_suggestions: string[]; disclaimer: string
}
export type JobResult = {
  id: string; title: string; match_score: number; breakdown: { required_match: number | null; preferred_match: number | null }
  required_skills: string[]; preferred_skills: string[]; you_have: string[]; should_improve: string[]; preferred_missing: string[]
  experience_requirements: { min_years: number; context: string }[]; education_requirements: { levels: string[]; mentions: string[] }
  technologies: string[]; recommended_courses: { id: string; title: string; url: string; platform: string; reason: string }[]; disclaimer: string
}
export type JobHistoryItem = { id: string; title: string; match_score: number; created_at: string }
export type ChatMsg = { role: 'user' | 'assistant'; content: string }
export type ChatSessionItem = { id: string; title: string; created_at: string }
export type CourseStatus = 'none' | 'planned' | 'in_progress' | 'completed'
export type ProgressSummary = {
  career: string; career_id: string; readiness_score: number; readiness_breakdown: Record<string, { value: number; weight: number; points: number }>
  skills: { coverage_percent: number; core_have: string[]; core_missing: string[]; total_skills: number }
  roadmap: { exists: boolean; completed: number; total: number; progress_percent: number }
  courses: { tracked: number; completed: number; in_progress: number; planned: number; completion_percent: number; items: { course_id: string; title: string; platform: string; url: string; status: CourseStatus; completed_at: string | null }[] }
  pending_skills: string[]; portfolio: { projects: string[]; certifications: string[] }; disclaimer: string
  history: { at: string; readiness: number; skill_count: number; roadmap_percent: number; courses_completed: number }[]
}
export class ApiError extends Error { constructor(m: string, public status: number) { super(m) } }

async function req<T>(path: string, init: { method?: string; body?: unknown; form?: FormData } = {}): Promise<T> {
  const headers: Record<string, string> = init.form ? {} : { 'Content-Type': 'application/json' }
  const t = getToken(); if (t) headers.Authorization = `Bearer ${t}`
  let r: Response
  try { r = await fetch(`${BASE}${path}`, { method: init.method || 'GET', headers, body: init.form ?? (init.body ? JSON.stringify(init.body) : undefined) }) }
  catch { throw new ApiError(`Cannot reach the API at ${BASE}. Start it with: uvicorn app.main:app --reload`, 0) }
  const d = await r.json().catch(() => ({}))
  if (!r.ok) {
    const e = d?.error; const det = e?.details?.map((x: { field: string; message: string }) => `${x.field}: ${x.message}`).join('; ')
    throw new ApiError(det ? `${e.message} (${det})` : e?.message || `Request failed (${r.status})`, r.status)
  }
  return d as T
}

const lines = (s: string) => s.split('\n').map(x => x.trim()).filter(Boolean)
const GOAL_UNSURE = "I'm not sure yet"
type ApiProfile = { degree: string; branch: string; institution: string; current_year: number | null; cgpa: number | null; skills: string[]; interests: string[]; projects: string[]; certifications: string[]; experience: string[]; career_goal: string }
const toApi = (p: Profile): ApiProfile => ({ degree: p.degree, branch: p.branch, institution: p.institution, current_year: p.year ? Number(p.year) : null, cgpa: p.cgpa ? Number(p.cgpa) : null, skills: p.skills, interests: p.interests, projects: lines(p.projects), certifications: lines(p.certifications), experience: lines(p.experience), career_goal: p.goal === GOAL_UNSURE ? '' : p.goal })
const fromApi = (a: ApiProfile): Profile => ({ degree: a.degree, branch: a.branch, institution: a.institution, year: a.current_year?.toString() ?? '', cgpa: a.cgpa?.toString() ?? '', skills: a.skills, interests: a.interests, projects: a.projects.join('\n'), certifications: a.certifications.join('\n'), experience: a.experience.join('\n'), goal: a.career_goal || GOAL_UNSURE })

export const api = {
  register: (full_name: string, email: string, password: string) => req<{ access_token: string; user: ApiUser }>('/api/auth/register', { method: 'POST', body: { full_name, email, password } }),
  login: (email: string, password: string) => req<{ access_token: string; user: ApiUser }>('/api/auth/login', { method: 'POST', body: { email, password } }),
  careers: () => req<CareerInfo[]>('/api/careers'),
  courses: (careerId?: string, limit = 6) => req<CourseRecs>(`/api/recommendations/courses?limit=${limit}${careerId ? `&career_id=${encodeURIComponent(careerId)}` : ''}`),
  roadmap: () => req<Roadmap>('/api/roadmap'),
  generateRoadmap: (career_id?: string) => req<Roadmap>('/api/roadmap/generate', { method: 'POST', body: { career_id: career_id || null } }),
  setRoadmapItem: (id: string, completed: boolean) => req<Roadmap>(`/api/roadmap/${id}`, { method: 'PUT', body: { completed } }),
  analyzeResume: (file: File, careerId?: string) => { const f = new FormData(); f.append('file', file); if (careerId) f.append('career_id', careerId); return req<ResumeResult>('/api/resume/analyze', { method: 'POST', form: f }) },
  latestResume: async (): Promise<ResumeResult | null> => { try { return await req<ResumeResult>('/api/resume/latest') } catch (e) { if (e instanceof ApiError && e.status === 404) return null; throw e } },
  analyzeJob: (description: string, title: string) => req<JobResult>('/api/job/analyze', { method: 'POST', body: { description, title } }),
  jobHistory: () => req<JobHistoryItem[]>('/api/job/history'),
  jobById: (id: string) => req<JobResult>(`/api/job/${id}`),
  chatSuggestions: () => req<string[]>('/api/chat/suggestions'),
  chat: (message: string, sessionId?: string | null) => req<{ session_id: string; reply: string; mode: 'local' | 'llm' }>('/api/chat', { method: 'POST', body: { message, session_id: sessionId ?? null } }),
  chatSessions: () => req<ChatSessionItem[]>('/api/chat/history'),
  chatMessages: (id: string) => req<ChatMsg[]>(`/api/chat/history?session_id=${id}`),
  deleteChat: (id: string) => req<unknown>(`/api/chat/${id}`, { method: 'DELETE' }),
  progress: () => req<ProgressSummary>('/api/progress'),
  courseStatuses: () => req<Record<string, CourseStatus>>('/api/progress/courses'),
  setCourseStatus: (id: string, status: CourseStatus) => req<ProgressSummary>(`/api/progress/courses/${id}`, { method: 'PUT', body: { status } }),
  applySkills: (skills?: string[]) => req<ProgressSummary>('/api/progress/apply-skills', { method: 'POST', body: skills ? { skills } : {} }),
  me: () => req<ApiUser>('/api/auth/me'),
  getProfile: async (): Promise<Profile | null> => { try { return fromApi(await req<ApiProfile>('/api/profile')) } catch (e) { if (e instanceof ApiError && e.status === 404) return null; throw e } },
  saveProfile: async (p: Profile) => fromApi(await req<ApiProfile>('/api/profile', { method: 'PUT', body: toApi(p) })),
}

export const analyze = (p: Profile) => {
  const a = toApi(p)
  return req<Analysis>('/api/career/analyze', { method: 'POST', body: { education: { degree: a.degree, branch: a.branch, institution: a.institution, year: a.current_year, cgpa: a.cgpa }, skills: a.skills, interests: a.interests, projects: a.projects, certifications: a.certifications, experience: a.experience, career_goal: a.career_goal } })
}
