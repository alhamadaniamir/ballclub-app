from pydantic_settings import BaseSettings, SettingsConfigDict

INSECURE_JWT_SECRET = "change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "Ballclub API"
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "ballclub"

    JWT_SECRET: str = INSECURE_JWT_SECRET
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 7

    OWNER_USERNAME: str = "owner"
    OWNER_PASSWORD_HASH: str = ""


settings = Settings()


def validate_settings() -> None:
    if settings.JWT_SECRET == INSECURE_JWT_SECRET:
        raise RuntimeError(
            "JWT_SECRET is left at its insecure default. Set a random 32+ character "
            "value in the environment before starting the server."
        )
