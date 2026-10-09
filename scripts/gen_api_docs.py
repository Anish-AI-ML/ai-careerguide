"""Regenerates docs/API.md from the FastAPI OpenAPI schema:  JWT_SECRET=x python scripts/gen_api_docs.py"""
import os, sys
from pathlib import Path
os.environ.setdefault("JWT_SECRET", "docs-only-secret-0123456789")
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "backend"))
from app.main import app  # noqa: E402

spec, rows = app.openapi(), []
for path, ops in spec["paths"].items():
    for method, op in ops.items():
        auth = "Bearer token" if op.get("security") else "Public"
        rows.append((op["tags"][0] if op.get("tags") else "", path, method.upper(), auth, op.get("summary", "")))
rows.sort(key=lambda r: (r[0], r[1], r[2]))
out = ["# API reference", "", "Generated from the OpenAPI schema. Live interactive docs: `/docs` (Swagger UI) and `/redoc` on a running server.", "",
       "Errors share one shape: `{\"error\": {\"code\": \"...\", \"message\": \"...\", \"details\": [...]}}`.", "",
       "| Group | Method | Path | Auth | Summary |", "|---|---|---|---|---|"]
out += [f"| {t} | {m} | `{p}` | {a} | {s} |" for t, p, m, a, s in rows]
(root / "docs" / "API.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print(f"wrote {len(rows)} endpoints")
