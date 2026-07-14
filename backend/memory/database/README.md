# Foundational PostgreSQL Database Infrastructure

Provides connection configuration, connection pooling, session lifecycle management, and a shared declarative base model using SQLAlchemy 2.x and Pydantic.

## Connection Parameters & Configuration

Values are loaded and validated from environment variables (`.env` file) via `db_config`:

* **`DATABASE_HOST`**: PostgreSQL instance host (default: `localhost`).
* **`DATABASE_PORT`**: PostgreSQL instance port (default: `5432`).
* **`DATABASE_NAME`**: Database name (default: `auralis`).
* **`DATABASE_USER`**: PostgreSQL user (default: `postgres`).
* **`DATABASE_PASSWORD`**: PostgreSQL password (default: `postgres`).
* **`DATABASE_URL`**: Pre-configured database URL. If not provided, it is dynamically constructed using the format: `postgresql+psycopg://{user}:{password}@{host}:{port}/{name}`

## Connection Pooling Settings

The engine in `database.py` manages a singleton connection pool with the following settings:
- **`pool_size=5`**: Retains up to 5 concurrent connections.
- **`max_overflow=10`**: Permits dynamic creation of up to 10 additional connections.
- **`pool_timeout=30`**: Raises a timeout exception after 30 seconds of waiting.
- **`pool_recycle=1800`**: Recycles connections older than 30 minutes.
- **`pool_pre_ping=True`**: Enables connection validation before issuing commands.

## Usage

### Declarative Models (`base.py`)

All ORM models must inherit from `Base`:

```python
from sqlalchemy import Column, String
from memory.database import Base

class PreferenceModel(Base):
    __tablename__ = "preferences"
    
    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)
```

### FastAPI Dependency Injection (`session.py`)

Use `get_db` to inject database sessions into path operations:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from memory.database import get_db

router = APIRouter()

@router.get("/data")
def read_data(db: Session = Depends(get_db)):
    # Session is managed, transaction rollback on exceptions, close on exit
    return {"status": "ok"}
```
