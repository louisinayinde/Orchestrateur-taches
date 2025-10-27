"""Gestion des connexions SQLite.

Ce module fournit un gestionnaire de connexion à la base de données.
"""

import sqlite3
from pathlib import Path
from typing import Generator

# Chemin par défaut de la base de données
DEFAULT_DB_PATH = Path.cwd() / "jobs.db"


def get_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Crée une connexion SQLite.
    
    Args:
        db_path: Chemin vers le fichier de base de données
    
    Returns:
        Une connexion SQLite
    """
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    # Activer les clés étrangères
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_cursor() -> Generator[sqlite3.Cursor, None, None]:
    """Context manager pour obtenir un curseur SQLite.
    
    Le curseur est automatiquement commit et fermé.
    
    Yields:
        Un curseur SQLite
    
    Example:
        with get_cursor() as cursor:
            cursor.execute("SELECT * FROM jobs")
            results = cursor.fetchall()
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    finally:
        cursor.close()
        conn.close()

