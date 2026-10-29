"""Configuration unique du projet, lue depuis l'environnement (ou un fichier .env)."""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = PROJECT_ROOT / "sql"
DOCS_DIR = PROJECT_ROOT / "docs"
SAMPLE_DIR = PROJECT_ROOT / "data" / "sample"


def _load_dotenv(path: Path = PROJECT_ROOT / ".env") -> None:
    """Charge un fichier .env minimal (CLE=valeur) sans écraser l'environnement."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()


def raw_dir() -> Path:
    """Dossier contenant les 9 CSV Olist."""
    return PROJECT_ROOT / os.environ.get("RAW_DIR", "data/raw")


def database_url() -> str:
    """URL SQLAlchemy de la base PostgreSQL."""
    user = os.environ.get("POSTGRES_USER", "shoppulse")
    password = os.environ.get("POSTGRES_PASSWORD", "shoppulse")
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    name = os.environ.get("POSTGRES_DB", "shoppulse")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}"
