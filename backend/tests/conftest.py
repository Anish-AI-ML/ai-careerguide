import os
# Set TEST_DATABASE_URL to run the whole suite against Postgres; defaults to in-memory SQLite.
os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL", "sqlite://")
os.environ["JWT_SECRET"] = "test-secret-key-for-pytest-only-123456"
os.environ["AUTH_RATE_LIMIT_PER_MIN"] = "1000"
os.environ["AI_RATE_LIMIT_PER_MIN"] = "1000"
