"""Modèles de données pour les Jobs.

Ce module définit les classes Job et les types associés.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class JobType(Enum):
    """Type d'exécution pour un job."""
    
    SYNC = "sync"       # Exécution synchrone simple
    ASYNC = "async"     # Exécution asynchrone (asyncio)
    THREAD = "thread"   # Exécution dans un thread
    PROCESS = "process" # Exécution dans un process (multiprocessing)


@dataclass
class Job:
    """Définition d'un job à exécuter.
    
    Attributes:
        id: Identifiant unique du job (None si pas encore persisté)
        name: Nom unique du job
        function: Fonction à exécuter
        args: Arguments positionnels de la fonction
        kwargs: Arguments nommés de la fonction
        job_type: Type d'exécution (SYNC, ASYNC, THREAD, PROCESS)
        max_retries: Nombre maximum de tentatives en cas d'échec
        timeout_seconds: Timeout en secondes (None = pas de timeout)
        idempotency_key: Clé d'idempotence pour éviter les doublons
    """
    
    name: str
    function: Callable
    id: Optional[int] = None
    args: tuple = ()
    kwargs: dict = field(default_factory=dict)
    job_type: JobType = JobType.SYNC
    max_retries: int = 3
    timeout_seconds: Optional[int] = None
    idempotency_key: Optional[str] = None
    
    def get_function_path(self) -> str:
        """Retourne le chemin complet de la fonction (module.function)."""
        return f"{self.function.__module__}.{self.function.__name__}"

