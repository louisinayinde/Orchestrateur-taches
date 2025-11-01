"""Système de récupération après crash.

Ce module implémente la logique de récupération pour marquer les jobs
RUNNING comme FAILED au démarrage, permettant la reprise propre après un crash.
"""

from orchestrator.core.execution import ExecutionStatus
from orchestrator.db.repository import JobRepository


class RecoveryManager:
    """Gestionnaire de récupération après crash.
    
    Au démarrage de l'orchestrateur, ce gestionnaire parcourt la base
    de données pour trouver les jobs qui étaient RUNNING lors d'un crash
    précédent et les marque comme FAILED.
    
    Cela permet d'éviter que ces jobs restent bloqués en état RUNNING
    indéfiniment, ce qui empêcherait leur ré-exécution.
    
    Attributes:
        repository: Repository pour accéder aux exécutions
    
    Example:
        >>> manager = RecoveryManager(repository)
        >>> manager.recover()  # Marque tous les RUNNING comme FAILED
    """
    
    def __init__(self, repository: JobRepository):
        """Initialise le gestionnaire de récupération.
        
        Args:
            repository: Repository pour accéder aux exécutions
        """
        self.repository = repository
    
    def recover(self) -> int:
        """Récupère les jobs RUNNING et les marque comme FAILED.
        
        Cette méthode doit être appelée au démarrage de l'orchestrateur
        pour nettoyer les exécutions qui étaient en cours lors d'un
        crash précédent.
        
        Returns:
            Nombre de jobs récupérés
        
        Example:
            >>> manager = RecoveryManager(repository)
            >>> count = manager.recover()
            >>> print(f"Recovered {count} orphaned jobs")
        """
        conn = self.repository.db_path
        from orchestrator.db.connection import get_connection
        
        conn = get_connection(conn)
        cursor = conn.cursor()
        
        try:
            # Chercher toutes les exécutions en RUNNING
            cursor.execute("SELECT id FROM executions WHERE status = ?", (ExecutionStatus.RUNNING.value,))
            rows = cursor.fetchall()
            
            if not rows:
                return 0
            
            # Marquer toutes comme FAILED
            execution_ids = [row[0] for row in rows]
            placeholders = ','.join('?' * len(execution_ids))
            
            cursor.execute(
                f"UPDATE executions SET status = ? WHERE id IN ({placeholders})",
                (ExecutionStatus.FAILED.value, *execution_ids)
            )
            
            conn.commit()
            return len(execution_ids)
        finally:
            cursor.close()
            conn.close()

