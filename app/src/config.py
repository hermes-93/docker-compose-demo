import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")
    DATABASE_URL = os.environ.get("DATABASE_URL", "")
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
