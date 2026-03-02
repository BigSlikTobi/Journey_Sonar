from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "CJM_", "env_file": ".env"}

    database_url: str = "postgresql+asyncpg://journey:journey_dev@localhost:5432/journey_mapper"
    debug: bool = False
    api_prefix: str = "/api/v1"

    # Sonar default scoring weights (overridable per workspace)
    sonar_health_weight: float = 0.35
    sonar_opportunity_weight: float = 0.40
    sonar_urgency_weight: float = 0.25


settings = Settings()
