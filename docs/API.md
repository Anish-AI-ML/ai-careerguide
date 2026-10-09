# API reference

Generated from the OpenAPI schema. Live interactive docs: `/docs` (Swagger UI) and `/redoc` on a running server.

Errors share one shape: `{"error": {"code": "...", "message": "...", "details": [...]}}`.

| Group | Method | Path | Auth | Summary |
|---|---|---|---|---|
|  | GET | `/api/health` | Public | Health |
| auth | POST | `/api/auth/login` | Public | Login |
| auth | GET | `/api/auth/me` | Bearer token | Me |
| auth | POST | `/api/auth/register` | Public | Register |
| careers | POST | `/api/career/analyze` | Public | Analyze |
| careers | GET | `/api/careers` | Public | List Careers |
| careers | GET | `/api/careers/{career_id}` | Public | Get Career |
| chat | POST | `/api/chat` | Bearer token | Chat |
| chat | GET | `/api/chat/history` | Bearer token | History |
| chat | GET | `/api/chat/suggestions` | Public | Suggestions |
| chat | DELETE | `/api/chat/{session_id}` | Bearer token | Clear |
| job | POST | `/api/job/analyze` | Bearer token | Analyze |
| job | GET | `/api/job/history` | Bearer token | History |
| job | GET | `/api/job/{job_id}` | Bearer token | Get One |
| profile | GET | `/api/profile` | Bearer token | Get Profile |
| profile | PUT | `/api/profile` | Bearer token | Put Profile |
| profile | GET | `/api/skills` | Public | List Skills |
| profile | POST | `/api/skills` | Bearer token | Add Skill |
| progress | GET | `/api/progress` | Bearer token | Get Progress |
| progress | POST | `/api/progress/apply-skills` | Bearer token | Apply Skills |
| progress | GET | `/api/progress/courses` | Bearer token | Course Statuses |
| progress | PUT | `/api/progress/courses/{course_id}` | Bearer token | Set Course |
| recommendations | GET | `/api/recommendations/courses` | Bearer token | Courses For Me |
| recommendations | POST | `/api/recommendations/courses` | Public | Courses For Body |
| resume | POST | `/api/resume/analyze` | Bearer token | Analyze |
| resume | GET | `/api/resume/latest` | Bearer token | Latest |
| roadmap | GET | `/api/roadmap` | Bearer token | Get Roadmap |
| roadmap | POST | `/api/roadmap/generate` | Bearer token | Regenerate |
| roadmap | PUT | `/api/roadmap/{item_id}` | Bearer token | Update Item |
