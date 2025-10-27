"""Exécuteur synchrone simple.

Ce module implémente un executor synchrone qui exécute les jobs
de manière bloquante, un après l'autre.
"""

import time
import traceback
from typing import TYPE_CHECKING

from orchestrator.core.execution import ExecutionResult, ExecutionStatus

if TYPE_CHECKING:
    from orchestrator.core.job import Job

from orchestrator.executors.base import BaseExecutor


class SyncExecutor(BaseExecutor):
    """Exécuteur synchrone simple.
    
    Exécute les jobs de manière synchrone (bloquant).
    Utilisé pour les jobs simples qui ne nécessitent pas de concurrence.
    
    Attributes:
        name: Nom de l'executor
    
    Example:
        >>> executor = SyncExecutor()
        >>> result = await executor.execute(job)
        >>> print(result.status)  # SUCCESS or FAILED
    """
    
    def __init__(self):
        """Initialise l'executor synchrone."""
        self.name = "SyncExecutor"
    
    async def execute(self, job: "Job") -> ExecutionResult:
        """Exécute un job de manière synchrone.
        
        Args:
            job: Le job à exécuter
        
        Returns:
            Le résultat de l'exécution avec statut SUCCESS ou FAILED
        """
        start_time = time.time()
        
        try:
            # Exécuter la fonction
            # Note: Pour l'instant, on suppose que function est synchrone
            # Dans le futur, on pourra ajouter le support des fonctions async
            result = job.function(*job.args, **job.kwargs)
            
            # Calculer la durée
            duration = time.time() - start_time
            
            return ExecutionResult(
                status=ExecutionStatus.SUCCESS,
                result=result,
                duration_seconds=duration
            )
            
        except Exception as e:
            # Capture l'erreur et traceback
            duration = time.time() - start_time
            error_traceback = traceback.format_exc()
            
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                error=str(e),
                traceback=error_traceback,
                duration_seconds=duration
            )
    
    def shutdown(self) -> None:
        """Arrête l'executor.
        
        Pour l'executor synchrone, il n'y a rien à faire.
        Cette méthode est définie pour respecter l'interface.
        """
        pass  # Pas de ressources à libérer pour sync executor

