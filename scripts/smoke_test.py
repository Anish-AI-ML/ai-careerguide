"""End-to-end smoke test against a running API.

    python scripts/smoke_test.py http://localhost:8000

Walks the full user flow: register -> login -> profile -> career analysis -> courses -> roadmap ->
resume -> job match -> CareerAI -> progress. Exits non-zero on the first failure.
"""
import sys, uuid
import httpx

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/")


def make_pdf(lines):
    esc = lambda s: s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")  # noqa: E731
    body = "BT /F1 10 Tf 40 760 Td 12 TL\n" + "\n".join(f"({esc(l)}) Tj T*" for l in lines) + "\nET"
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [4 0 R] /Count 1 >>", b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 5 0 R /Resources << /Font << /F1 3 0 R >> >> >>",
            f"<< /Length {len(body)} >>\nstream\n{body}\nendstream".encode()]
    out, offs = b"%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        offs.append(len(out)); out += f"{i} 0 obj\n".encode() + o + b"\nendobj\n"
    x = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode() + b"".join(f"{o:010d} 00000 n \n".encode() for o in offs)
    return out + f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{x}\n%%EOF".encode()


RESUME = ["Jane Doe", "Education", "B.E. Computer Science (AI and ML), Example Institute", "Skills", "Python, TensorFlow, Machine Learning, SQL, Git, Docker",
          "Projects", "Traffic Flow Prediction", "- Built a machine learning model with Python and TensorFlow reaching 92% accuracy on 120,000 records",
          "- Deployed the model with Docker and reduced inference time by 40%", "Experience", "ML Intern", "- Developed data pipelines in Python and SQL for 50,000 records"]
JD = "Requirements:\n- 2+ years of experience in machine learning\n- Strong Python and SQL\n- Docker and AWS\nNice to have:\n- Kubernetes and PyTorch\n- Bachelor's degree in Computer Science"
step = 0


def check(name, cond, detail=""):
    global step
    step += 1
    print(f"{'PASS' if cond else 'FAIL'}  {step:02d} {name}")
    if not cond:
        print("      ", detail)
        sys.exit(1)


with httpx.Client(base_url=BASE, timeout=30) as c:
    check("health", c.get("/api/health").json() == {"status": "ok"})
    email = f"smoke-{uuid.uuid4().hex[:8]}@example.com"
    r = c.post("/api/auth/register", json={"full_name": "Smoke Tester", "email": email, "password": "smoke-test-pass-1"})
    check("register", r.status_code == 201, r.text)
    r = c.post("/api/auth/login", json={"email": email, "password": "smoke-test-pass-1"})
    check("login", r.status_code == 200, r.text)
    c.headers["Authorization"] = f"Bearer {r.json()['access_token']}"
    check("protected route needs profile first", c.get("/api/profile").status_code == 404)
    profile = {"degree": "B.E.", "branch": "Computer Science (AI & ML)", "institution": "Example Institute", "current_year": 3, "cgpa": 8.4,
               "skills": ["Python", "Machine Learning", "TensorFlow", "SQL", "Git"], "interests": ["Artificial Intelligence", "Machine Learning"],
               "projects": ["Traffic Flow Prediction with TensorFlow"], "certifications": ["Deep Learning Specialization"], "experience": ["ML internship"],
               "career_goal": "AI/ML Engineer"}
    check("profile setup", c.put("/api/profile", json=profile).status_code == 200)
    r = c.post("/api/career/analyze", json={"education": {"branch": profile["branch"], "cgpa": 8.4}, "skills": profile["skills"], "interests": profile["interests"],
                                            "projects": profile["projects"], "career_goal": "AI/ML Engineer"})
    check("career analysis + recommendation", r.status_code == 200 and r.json()["top"]["career"] == "AI/ML Engineer" and r.json()["top"]["skill_gaps"], r.text)
    r = c.get("/api/recommendations/courses?limit=4")
    check("skill gaps -> course recommendations", r.status_code == 200 and r.json()["courses"] and all(x["reason"] for x in r.json()["courses"]), r.text)
    rm = c.get("/api/roadmap").json()
    check("roadmap generated", rm["items"] and rm["progress_percent"] == 0)
    done = c.put(f"/api/roadmap/{rm['items'][0]['id']}", json={"completed": True}).json()
    check("roadmap item completed", done["progress_percent"] > 0)
    r = c.post("/api/resume/analyze", files={"file": ("cv.pdf", make_pdf(RESUME), "application/pdf")}, data={"career_id": "ai-ml-engineer"})
    check("resume analysis", r.status_code == 200 and r.json()["resume_score"] > 0 and r.json()["role_match"]["overall"] > 0, r.text)
    r = c.post("/api/job/analyze", json={"description": JD, "title": "ML Engineer"})
    check("job matching", r.status_code == 200 and "python" in r.json()["you_have"] and r.json()["should_improve"], r.text)
    r = c.post("/api/chat", json={"message": "Which skills am I missing?"})
    check("CareerAI answers from profile", r.status_code == 200 and "missing" in r.json()["reply"].lower(), r.text)
    check("chat history saved", len(c.get(f"/api/chat/history?session_id={r.json()['session_id']}").json()) == 2)
    check("course status tracked", c.put("/api/progress/courses/pytorch-tutorials", json={"status": "completed"}).status_code == 200)
    p = c.get("/api/progress").json()
    check("progress tracking", p["readiness_score"] > 0 and p["roadmap"]["completed"] == 1 and p["courses"]["completed"] == 1 and p["history"], str(p)[:300])
    check("unauthenticated access rejected", httpx.get(f"{BASE}/api/progress").status_code == 401)
print("\nAll steps passed.")
