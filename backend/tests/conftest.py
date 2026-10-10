import os

os.environ.setdefault("JWT_SECRET", "test-only-secret-not-for-deployment")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
