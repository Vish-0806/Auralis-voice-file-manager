"""Database configuration module for Auralis.

Loads database connection details from environment variables or custom env file,
validating settings using Pydantic.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field, model_validator
from dotenv import load_dotenv

# Explicitly load environment variables from the .env file in backend/
load_dotenv()


class DBConfig(BaseModel):
    """Configuration class for the PostgreSQL database connection parameters.

    Attributes:
        host: Hostname of the PostgreSQL instance.
        port: Port number for the PostgreSQL instance.
        name: Database name.
        user: Username for database login.
        password: Password for database login.
        url: Direct/pre-configured connection URL (optional).
    """

    host: str = Field(default="localhost", alias="DATABASE_HOST")
    port: int = Field(default=5432, alias="DATABASE_PORT")
    name: str = Field(default="auralis", alias="DATABASE_NAME")
    user: str = Field(default="postgres", alias="DATABASE_USER")
    password: str = Field(default="postgres", alias="DATABASE_PASSWORD")
    url: Optional[str] = Field(default=None, alias="DATABASE_URL")

    model_config = {
        "populate_by_name": True,
    }

    @model_validator(mode="after")
    def construct_database_url(self) -> "DBConfig":
        """Builds a database connection string if one is not explicitly defined.

        Returns:
            The DBConfig instance with initialized connection url.
        """
        if not self.url:
            # We use the postgresql+psycopg dialect for compatibility with psycopg (v3)
            self.url = f"postgresql+psycopg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        return self


# Resolve port with safety against empty or unset environment values
port_env = os.getenv("DATABASE_PORT")
resolved_port = int(port_env) if port_env and port_env.strip() else 5432

# Global singleton instance of database configuration
db_config = DBConfig(
    host=os.getenv("DATABASE_HOST", "localhost"),
    port=resolved_port,
    name=os.getenv("DATABASE_NAME", "auralis"),
    user=os.getenv("DATABASE_USER", "postgres"),
    password=os.getenv("DATABASE_PASSWORD", "postgres"),
    url=os.getenv("DATABASE_URL", None),
)
