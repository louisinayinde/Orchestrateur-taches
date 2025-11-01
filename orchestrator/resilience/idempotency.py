"""Système d'idempotence pour éviter les exécutions en double.

Ce module implémente la logique d'idempotence basée sur des clés uniques,
permettant d'éviter les exécutions en double du même job.
"""

from typing import Optional

from orchestrator.core.execution import ExecutionResult, ExecutionStatus
from orchestrator.db.repository import JobRepository


class IdempotencyManager:
    """Gestionnaire d'idempotence.
    
    Ce gestionnaire vérifie si un job avec une idempotency_key donnée
    a déjà été exécuté avec succès. Si c'est le cas, il retourne le
    résultat précédent au lieu de ré-exécuter le job.
    
    Cela permet de garantir qu'une opération ne sera exécutée qu'une
    seule fois, même si plusieurs requêtes sont faites.
    
    Attributes:
        repository: Repository pour accéder aux exécutions
    
    Example:
        >>> manager = IdempotencyManager(repository)
        >>> result = await manager.check_idempotency(key="unique_key")
        >>> if result:
        ...     print("Job déjà exécuté avec succès")
        ... else:
        ...     # Exécuter le job
    """
    
    def __init__(self, repository: JobRepository):
        """Initialise le gestionnaire d'idempotence.
        
        Args:
            repository: Repository pour accéder aux exécutions
        """
        self.repository = repository
    
    async def check_idempotency(
        self,
        idempotency_key: str
    ) -> Optional[ExecutionResult]:
        """Vérifie si un job avec cette clé a déjà été exécuté avec succès.
        
        Args:
            idempotency_key: La clé d'idempotence
        
        Returns:
            L'ExecutionResult du job précédent si trouvé, None sinon
        
        Example:
            >>> result = await manager.check_idempotency("my_key")
            >>> if result:
            ...     # Job déjà exécuté
            ...     return result
            >>> # Exécuter le job normalement
        """
        if not idempotency_key:
            return None
        
        # Chercher une exécution réussie avec cette clé
        execution = self.repository.find_idempotent_execution(idempotency_key)
        
        if execution:
            return ExecutionResult(
                status=ExecutionStatus.SUCCESS,
                result=execution.result,
                duration_seconds=execution.duration_seconds
            )
        
        return None

