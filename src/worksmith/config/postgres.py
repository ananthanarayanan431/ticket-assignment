from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "worksmith"
    postgres_password: str = "worksmith"
    postgres_db: str = "worksmith"

    @property
    def sqlalchemy_url(self) -> str:
        """SQLAlchemy async URL (asyncpg driver) — used by both the app's engine and Alembic."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def psycopg_dsn(self) -> str:
        """Plain postgres DSN (psycopg driver) — used by the LangGraph checkpointer."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


postgres_settings = PostgresSettings()
