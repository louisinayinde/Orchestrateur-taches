"""Base classes pour les executors.

Ce module définit l'interface commune pour tous les executors.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from orchestrator.core.job import Job
    from orchestrator.core.execution import ExecutionResult


class BaseExecutor(ABC):
    """Interface commune pour tous les executors.
    
    Un executor est responsable de l'exécution d'un job.
    Chaque type d'executor (sync, async, thread, process) hérite
    de cette classe et implémente la méthode execute().
    
    Example:
        class SyncExecutor(BaseExecutor):
            async def execute(self, job: Job) -> ExecutionResult:
                # Implémentation...
                pass
    """
    
    @abstractmethod
    async def execute(self, job: "Job") -> "ExecutionResult":
        """Exécute un job.
        
        Args:
            job: Le job à exécuter
        
        Returns:
            Le résultat de l'exécution
        
        Raises:
            NotImplementedError: Si non implémenté
        """
        raise NotImplementedError("Subclass must implement execute()")
    
    @abstractmethod
    def shutdown(self) -> None:
        """Arrête l'executor proprement.
        
        Cette méthode doit libérer les ressources (pools, connexions, etc.).
        """
        raise NotImplementedError("Subclass must implement shutdown()")

