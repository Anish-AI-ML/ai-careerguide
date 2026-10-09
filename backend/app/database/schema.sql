-- AI CareerGuide schema (PostgreSQL 13+; works on Supabase). No secrets stored here.
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT NOT NULL UNIQUE,
  full_name TEXT NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE profiles (
  user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  degree TEXT NOT NULL DEFAULT '', branch TEXT NOT NULL DEFAULT '', institution TEXT NOT NULL DEFAULT '',
  current_year INT, cgpa DOUBLE PRECISION CHECK (cgpa BETWEEN 0 AND 10),
  interests JSONB NOT NULL DEFAULT '[]', projects JSONB NOT NULL DEFAULT '[]',
  certifications JSONB NOT NULL DEFAULT '[]', experience JSONB NOT NULL DEFAULT '[]',
  career_goal TEXT NOT NULL DEFAULT '',   -- '' = "I'm not sure yet"
  onboarding_done BOOLEAN NOT NULL DEFAULT true,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE skills (
  id SERIAL PRIMARY KEY, name_key TEXT NOT NULL UNIQUE, name TEXT NOT NULL, category TEXT
);
CREATE TABLE user_skills (
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  skill_id INT REFERENCES skills(id) ON DELETE CASCADE,
  level SMALLINT NOT NULL DEFAULT 1 CHECK (level BETWEEN 1 AND 5),
  PRIMARY KEY (user_id, skill_id)
);
CREATE TABLE careers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug TEXT NOT NULL UNIQUE, name TEXT NOT NULL, description TEXT
);
CREATE TABLE career_skills (
  career_id UUID REFERENCES careers(id) ON DELETE CASCADE,
  skill_id INT REFERENCES skills(id) ON DELETE CASCADE,
  is_core BOOLEAN NOT NULL DEFAULT true,
  PRIMARY KEY (career_id, skill_id)
);
CREATE TABLE courses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL, platform TEXT NOT NULL, provider TEXT,
  skill_id INT REFERENCES skills(id), difficulty TEXT CHECK (difficulty IN ('beginner','intermediate','advanced')),
  duration_hours NUMERIC(6,1), rating NUMERIC(2,1), url TEXT, prerequisites TEXT[] NOT NULL DEFAULT '{}'
);
CREATE TABLE career_courses (
  career_id UUID REFERENCES careers(id) ON DELETE CASCADE,
  course_id UUID REFERENCES courses(id) ON DELETE CASCADE,
  PRIMARY KEY (career_id, course_id)
);
CREATE TABLE user_courses (
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  course_id TEXT NOT NULL,          -- id from data/courses.json
  status TEXT NOT NULL CHECK (status IN ('planned','in_progress','completed')),
  completed_at TIMESTAMPTZ,
  PRIMARY KEY (user_id, course_id)
);
CREATE TABLE progress_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  readiness SMALLINT NOT NULL, skill_count INT NOT NULL, roadmap_percent SMALLINT NOT NULL, courses_completed INT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_snapshots_user ON progress_snapshots(user_id, created_at DESC);
CREATE TABLE projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title TEXT NOT NULL, description TEXT, technologies TEXT[] NOT NULL DEFAULT '{}'
);
CREATE TABLE certifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL, issuer TEXT, issued_on DATE
);
CREATE TABLE roadmaps (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  career_id TEXT NOT NULL, career_name TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE roadmap_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  roadmap_id UUID NOT NULL REFERENCES roadmaps(id) ON DELETE CASCADE,
  phase SMALLINT NOT NULL, title TEXT NOT NULL, skills JSONB NOT NULL DEFAULT '[]',
  est_weeks SMALLINT NOT NULL, difficulty TEXT NOT NULL,
  courses JSONB NOT NULL DEFAULT '[]', projects JSONB NOT NULL DEFAULT '[]',
  completed BOOLEAN NOT NULL DEFAULT false, completed_at TIMESTAMPTZ
);
CREATE TABLE resume_analysis (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  career_id TEXT NOT NULL, score SMALLINT NOT NULL CHECK (score BETWEEN 0 AND 100),
  result JSONB NOT NULL,            -- analysis only; the PDF and raw text are never stored
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE job_analysis (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title TEXT NOT NULL DEFAULT '',
  match_score SMALLINT CHECK (match_score BETWEEN 0 AND 100),
  result JSONB NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE chat_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE chat_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user','assistant')),
  content TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_user_skills_user ON user_skills(user_id);
CREATE INDEX idx_career_skills_skill ON career_skills(skill_id);
CREATE INDEX idx_courses_skill ON courses(skill_id);
CREATE INDEX idx_projects_user ON projects(user_id);
CREATE INDEX idx_certs_user ON certifications(user_id);
CREATE INDEX idx_roadmap_items_rm ON roadmap_items(roadmap_id, phase);
CREATE INDEX idx_resume_user ON resume_analysis(user_id, created_at DESC);
CREATE INDEX idx_job_user ON job_analysis(user_id, created_at DESC);
CREATE INDEX idx_chat_sessions_user ON chat_sessions(user_id, created_at DESC);
CREATE INDEX idx_chat_messages_session ON chat_messages(session_id, created_at);
