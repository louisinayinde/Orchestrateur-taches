"""Classe principale Orchestrator.

Ce module contient la classe Orchestrator qui orchestre l'exécution des jobs.
"""

import json
from pathlib import Path
from typing import Any, Callable, Optional

from orchestrator.core.execution import Execution, ExecutionResult, ExecutionStatus
from orchestrator.core.job import Job, JobType
from orchestrator.db.repository import JobRepository
from orchestrator.executors.base import BaseExecutor
from orchestrator.executors.sync_executor import SyncExecutor
from orchestrator.queue.task_queue import TaskQueue


class Orchestrator:
    """Orchestrateur de tâches principal.
    
    Cette classe coordonne l'exécution des jobs.
    Elle utilise un TaskQueue pour gérer les jobs en attente,
    un Executor pour exécuter les jobs, et un Repository pour persister
    l'état dans la base de données.
    
    Attributes:
        queue: File d'attente des jobs
        executor: Exécuteur des jobs
        repository: Repository pour la persistance
        db_path: Chemin vers la base de données
    
    Example:
        >>> orch = Orchestrator()
        >>> job = orch.add_job(my_function, name="my_task", args=(arg1,))
        >>> execution = await orch.execute_job(job.id)
        >>> print(execution.result)
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialise l'orchestrateur.
        
        Args:
            db_path: Chemin vers la base de données (None = jobs.db dans le CWD)
        """
        self.db_path = db_path or (Path.cwd() / "jobs.db")
        self.queue = TaskQueue()
        self.executor = SyncExecutor()
        self.repository = JobRepository(self.db_path)
    
    def add_job(
        self,
        func: Callable,
        name: str,
        args: tuple = (),
        kwargs: Optional[dict] = None,
        job_type: JobType = JobType.SYNC,
        max_retries: int = 3,
        timeout_seconds: Optional[int] = None,
        idempotency_key: Optional[str] = None
    ) -> Job:
        """Ajoute un job à l'orchestrateur.
        
        Args:
            func: Fonction à exécuter
            name: Nom unique du job
            args: Arguments positionnels
            kwargs: Arguments nommés
            job_type: Type d'exécution (SYNC, ASYNC, THREAD, PROCESS)
            max_retries: Nombre maximum de tentatives
            timeout_seconds: Timeout en secondes
            idempotency_key: Clé d'idempotence
        
        Returns:
            Le job créé avec son ID
        
        Example:
            >>> job = orch.add_job(
            ...     my_function,
            ...     name="my_task",
            ...     args=(arg1, arg2),
            ...     job_type=JobType.SYNC
            ... )
        """
        if kwargs is None:
            kwargs = {}
        
        # Créer le Job
        job = Job(
            id=None,
            name=name,
            function=func,
            args=args,
            kwargs=kwargs,
            job_type=job_type,
            max_retries=max_retries,
            timeout_seconds=timeout_seconds,
            idempotency_key=idempotency_key
        )
        
        # Persister le job
        job.id = self.repository.create_job(job)
        
        return job
    
    async def execute_job(self, job: Job) -> Execution:
        """Exécute un job.
        
        Args:
            job: Le job à exécuter
        
        Returns:
            L'exécution avec le résultat
        
        Example:
            >>> execution = await orch.execute_job(job)
            >>> print(f"Status: {execution.status}")
            >>> print(f"Result: {execution.result}")
        """
        # Créer une exécution en DB
        execution_id = self.repository.create_execution(job.id)
        
        execution = Execution(
            id=execution_id,
            job_id=job.id,
            status=ExecutionStatus.RUNNING,
            started_at=None  # Sera mis à jour après exécution
        )
        
        # Exécuter le job
        result: ExecutionResult = await self.executor.execute(job)
        
        # Mettre à jour l'exécution
        execution.status = result.status
        execution.result = result.result
        execution.error_message = result.error
        
        # Persister le résultat
        self.repository.update_execution(execution)
        
        return execution
    
    def get_job(self, job_id: int) -> Optional[Job]:
        """Récupère un job par son ID.
        
        Args:
            job_id: ID du job
        
        Returns:
            Le job ou None
        """
        return self.repository.get_job(job_id)
    
    def list_executions(self, job_id: Optional[int] = None, limit: int = 100) -> list:
        """Liste les exécutions.
        
        Args:
            job_id: Filtrer par job_id
            limit: Nombre maximum de résultats
        
        Returns:
            Liste des exécutions
        """
        return self.repository.list_executions(job_id=job_id, limit=limit)

