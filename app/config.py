from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "CJM_", "env_file": ".env"}

    database_url: str = "sqlite+aiosqlite:////data/journey_mapper.db"
    debug: bool = False
    api_prefix: str = "/api/v1"
    api_key: str = ""  # Set CJM_API_KEY in .env to require authentication
    allowed_origins: str = "http://localhost:5173"  # Comma-separated list

    # Sonar default scoring weights (overridable per workspace)
    sonar_health_weight: float = 0.35
    sonar_opportunity_weight: float = 0.40
    sonar_urgency_weight: float = 0.25


settings = Settings()
