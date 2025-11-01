"""Builder pattern pour l'API fluente de l'orchestrateur.

Ce module fournit une API fluente pour configurer et exécuter des jobs.
"""

from typing import Any, Callable, Dict, Optional

from orchestrator.core.job import Job, JobType
from orchestrator.core.orchestrator import Orchestrator


class JobBuilder:
    """Builder pour créer et configurer un job avec une API fluente.
    
    Cette classe permet de construire des jobs de manière déclarative
    avec des méthodes chaînées (fluent interface).
    
    Attributes:
        _orchestrator: Orchestrateur à utiliser
        _func: Fonction à exécuter
        _name: Nom du job
        _args: Arguments positionnels
        _kwargs: Arguments nommés
        _job_type: Type de job
        _max_retries: Nombre de retries
        _timeout_seconds: Timeout en secondes
        _idempotency_key: Clé d'idempotence
    
    Example:
        >>> orch = Orchestrator()
        >>> job = (JobBuilder(orch)
        ...     .with_function(my_func)
        ...     .named("my_job")
        ...     .with_args(1, 2, 3)
        ...     .with_kwargs(key="value")
        ...     .as_async()
        ...     .retries(5)
        ...     .timeout(30)
        ...     .build())
        >>> execution = await orch.execute_job(job)
    """
    
    def __init__(self, orchestrator: Orchestrator):
        """Initialise le builder.
        
        Args:
            orchestrator: Orchestrateur à utiliser
        """
        self._orchestrator = orchestrator
        self._func: Optional[Callable] = None
        self._name: Optional[str] = None
        self._args: tuple = ()
        self._kwargs: Dict[str, Any] = {}
        self._job_type: JobType = JobType.SYNC
        self._max_retries: int = 3
        self._timeout_seconds: Optional[int] = None
        self._idempotency_key: Optional[str] = None
    
    def with_function(self, func: Callable) -> "JobBuilder":
        """Spécifie la fonction à exécuter.
        
        Args:
            func: Fonction à exécuter
            
        Returns:
            Le builder (pour chaînage)
        """
        self._func = func
        return self
    
    def named(self, name: str) -> "JobBuilder":
        """Spécifie le nom du job.
        
        Args:
            name: Nom du job
            
        Returns:
            Le builder (pour chaînage)
        """
        self._name = name
        return self
    
    def with_args(self, *args: Any) -> "JobBuilder":
        """Spécifie les arguments positionnels.
        
        Args:
            *args: Arguments positionnels
            
        Returns:
            Le builder (pour chaînage)
        """
        self._args = args
        return self
    
    def with_kwargs(self, **kwargs: Any) -> "JobBuilder":
        """Spécifie les arguments nommés.
        
        Args:
            **kwargs: Arguments nommés
            
        Returns:
            Le builder (pour chaînage)
        """
        self._kwargs.update(kwargs)
        return self
    
    def as_sync(self) -> "JobBuilder":
        """Configure le job comme SYNC.
        
        Returns:
            Le builder (pour chaînage)
        """
        self._job_type = JobType.SYNC
        return self
    
    def as_async(self) -> "JobBuilder":
        """Configure le job comme ASYNC.
        
        Returns:
            Le builder (pour chaînage)
        """
        self._job_type = JobType.ASYNC
        return self
    
    def as_thread(self) -> "JobBuilder":
        """Configure le job comme THREAD.
        
        Returns:
            Le builder (pour chaînage)
        """
        self._job_type = JobType.THREAD
        return self
    
    def as_process(self) -> "JobBuilder":
        """Configure le job comme PROCESS.
        
        Returns:
            Le builder (pour chaînage)
        """
        self._job_type = JobType.PROCESS
        return self
    
    def with_job_type(self, job_type: JobType) -> "JobBuilder":
        """Spécifie le type de job explicitement.
        
        Args:
            job_type: Type de job
            
        Returns:
            Le builder (pour chaînage)
        """
        self._job_type = job_type
        return self
    
    def retries(self, count: int) -> "JobBuilder":
        """Spécifie le nombre de retries.
        
        Args:
            count: Nombre de retries
            
        Returns:
            Le builder (pour chaînage)
        """
        self._max_retries = count
        return self
    
    def timeout(self, seconds: int) -> "JobBuilder":
        """Spécifie le timeout.
        
        Args:
            seconds: Timeout en secondes
            
        Returns:
            Le builder (pour chaînage)
        """
        self._timeout_seconds = seconds
        return self
    
    def idempotent(self, key: str) -> "JobBuilder":
        """Active l'idempotence avec une clé.
        
        Args:
            key: Clé d'idempotence
            
        Returns:
            Le builder (pour chaînage)
        """
        self._idempotency_key = key
        return self
    
    def build(self) -> Job:
        """Construit et enregistre le job.
        
        Returns:
            Le job créé
            
        Raises:
            ValueError: Si la fonction ou le nom ne sont pas spécifiés
        """
        if self._func is None:
            raise ValueError("Function must be specified with with_function()")
        if self._name is None:
            raise ValueError("Name must be specified with named()")
        
        return self._orchestrator.add_job(
            func=self._func,
            name=self._name,
            args=self._args,
            kwargs=self._kwargs,
            job_type=self._job_type,
            max_retries=self._max_retries,
            timeout_seconds=self._timeout_seconds,
            idempotency_key=self._idempotency_key
        )


def job(orchestrator: Orchestrator) -> JobBuilder:
    """Factory function pour créer un JobBuilder.
    
    Args:
        orchestrator: Orchestrateur à utiliser
        
    Returns:
        Un nouveau JobBuilder
        
    Example:
        >>> orch = Orchestrator()
        >>> job = job(orch).with_function(my_func).named("my_job").as_async().build()
    """
    return JobBuilder(orchestrator)

