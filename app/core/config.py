import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    KAFKA_TOPIC: str = os.getenv("KAFKA_TOPIC", "telemetry-events")
    OPENF1_BASE_URL: str = os.getenv("OPENF1_BASE_URL", "https://api.openf1.org/v1")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")


settings = Settings()