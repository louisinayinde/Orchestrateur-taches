"""Gestionnaire d'executors.

Ce module implémente un gestionnaire qui sélectionne et gère
les différents types d'executors selon le type de job.
"""

from typing import TYPE_CHECKING

from orchestrator.core.config import Config
from orchestrator.core.job import JobType

if TYPE_CHECKING:
    from orchestrator.executors.base import BaseExecutor

from orchestrator.executors.async_executor import AsyncExecutor
from orchestrator.executors.process_executor import ProcessExecutor
from orchestrator.executors.sync_executor import SyncExecutor
from orchestrator.executors.thread_executor import ThreadExecutor


class ExecutorManager:
    """Gestionnaire d'executors.
    
    Cette classe est responsable de la création et de la gestion
    des différents types d'executors (Sync, Async, Thread, Process).
    Elle sélectionne automatiquement le bon executor selon le type
    de job à exécuter.
    
    Attributes:
        config: Configuration de l'orchestrateur
        sync_executor: Executor synchrone
        async_executor: Executor asynchrone
        _executors: Cache des executors par type
    
    Example:
        >>> manager = ExecutorManager(config)
        >>> executor = manager.get_executor(JobType.ASYNC)
        >>> result = await executor.execute(job)
    """
    
    def __init__(self, config: Config):
        """Initialise le gestionnaire d'executors.
        
        Args:
            config: Configuration de l'orchestrateur
        """
        self.config = config
        
        # Initialiser les executors
        self.sync_executor = SyncExecutor()
        self.async_executor = AsyncExecutor(max_concurrent=config.max_async_concurrent)
        self.thread_executor = ThreadExecutor(pool_size=config.thread_pool_size)
        self.process_executor = ProcessExecutor(pool_size=config.process_pool_size)
        
        # Cache pour les executors
        self._executors: dict[JobType, "BaseExecutor"] = {
            JobType.SYNC: self.sync_executor,
            JobType.ASYNC: self.async_executor,
            JobType.THREAD: self.thread_executor,
            JobType.PROCESS: self.process_executor,
        }
    
    def get_executor(self, job_type: JobType) -> "BaseExecutor":
        """Retourne l'executor approprié pour un type de job.
        
        Args:
            job_type: Le type de job (SYNC, ASYNC, THREAD, PROCESS)
        
        Returns:
            L'executor approprié
        
        Raises:
            ValueError: Si le type de job n'est pas supporté
        
        Example:
            >>> executor = manager.get_executor(JobType.ASYNC)
            >>> result = await executor.execute(job)
        """
        if job_type in self._executors:
            return self._executors[job_type]
        
        raise ValueError(f"Unknown job type: {job_type}")
    
    def shutdown_all(self) -> None:
        """Arrête tous les executors proprement.
        
        Cette méthode doit être appelée à la fermeture de l'application
        pour libérer toutes les ressources.
        """
        for executor in self._executors.values():
            executor.shutdown()

