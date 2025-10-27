"""Script d'initialisation de la base de données.

Ce script crée les tables nécessaires dans la base de données SQLite.
"""

import sys
from pathlib import Path

# Ajouter le dossier parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from orchestrator.db.models import CREATE_DATABASE_SQL
from orchestrator.db.connection import get_connection, DEFAULT_DB_PATH


def init_database(db_path: Path = DEFAULT_DB_PATH) -> None:
    """Initialise la base de données.
    
    Crée les tables nécessaires si elles n'existent pas déjà.
    
    Args:
        db_path: Chemin vers le fichier de base de données
    
    Example:
        >>> init_database()
        >>> # Les tables sont maintenant créées dans jobs.db
    """
    print(f"Initialisation de la base de donnees : {db_path}")
    
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    try:
        # Exécuter toutes les commandes CREATE
        for sql in CREATE_DATABASE_SQL:
            cursor.execute(sql)
            print(f"[OK] Execute : {sql.strip()[:50]}...")
        
        conn.commit()
        print("\n[OK] Base de donnees initialisee avec succes!")
        
    except Exception as e:
        print(f"\n[ERROR] Erreur lors de l'initialisation : {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    # Permet d'exécuter : python -m orchestrator.db.init_db
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialiser la base de données")
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DEFAULT_DB_PATH,
        help="Chemin vers le fichier de base de données"
    )
    
    args = parser.parse_args()
    init_database(args.db_path)

