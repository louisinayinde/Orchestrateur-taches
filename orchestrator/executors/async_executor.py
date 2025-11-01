"""Exécuteur asynchrone avec asyncio.

Ce module implémente un executor asynchrone qui utilise asyncio
pour exécuter les jobs de manière non-bloquante, idéal pour les
tâches I/O-bound comme les appels HTTP, lecture/écriture de fichiers, etc.
"""

import asyncio
import inspect
import time
import traceback
from typing import TYPE_CHECKING

from orchestrator.core.execution import ExecutionResult, ExecutionStatus

if TYPE_CHECKING:
    from orchestrator.core.job import Job

from orchestrator.executors.base import BaseExecutor


class AsyncExecutor(BaseExecutor):
    """Exécuteur asynchrone avec asyncio.
    
    Exécute les jobs de manière asynchrone en utilisant asyncio.
    Supporte :
    - Les fonctions async (avec await)
    - Les fonctions sync (exécutées dans l'event loop)
    
    Utilise un semaphore pour limiter le nombre de jobs concurrents.
    
    Attributes:
        name: Nom de l'executor
        max_concurrent: Nombre maximum de jobs exécutés simultanément
        semaphore: Semaphore pour contrôler la concurrence
        _running_count: Nombre de jobs actuellement en cours
    
    Example:
        >>> executor = AsyncExecutor(max_concurrent=10)
        >>> result = await executor.execute(job)
        >>> print(result.status)  # SUCCESS or FAILED
    """
    
    def __init__(self, max_concurrent: int = 10):
        """Initialise l'executor asynchrone.
        
        Args:
            max_concurrent: Nombre maximum de jobs concurrents (défaut: 10)
        """
        self.name = "AsyncExecutor"
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self._running_count = 0
    
    async def execute(self, job: "Job") -> ExecutionResult:
        """Exécute un job de manière asynchrone.
        
        La méthode attend qu'un slot soit disponible dans le semaphore,
        puis exécute le job. Supporte les fonctions async et sync.
        
        Args:
            job: Le job à exécuter
        
        Returns:
            Le résultat de l'exécution avec statut SUCCESS ou FAILED
        
        Example:
            >>> async def my_async_func(url):
            ...     async with aiohttp.ClientSession() as session:
            ...         async with session.get(url) as resp:
            ...             return await resp.text()
            >>> 
            >>> job = Job(name="fetch", function=my_async_func, args=("https://example.com",))
            >>> result = await executor.execute(job)
        """
        start_time = time.time()
        
        # Acquérir un slot dans le semaphore (limite la concurrence)
        async with self.semaphore:
            self._running_count += 1
            
            try:
                # Vérifier si la fonction est async
                is_async = inspect.iscoroutinefunction(job.function)
                
                if is_async:
                    # Fonction async : l'exécuter directement
                    result_value = await job.function(*job.args, **job.kwargs)
                else:
                    # Fonction sync : l'exécuter dans l'event loop
                    # On utilise asyncio.to_thread() (Python 3.9+)
                    # ou run_in_executor pour les versions antérieures
                    try:
                        result_value = await asyncio.to_thread(
                            job.function,
                            *job.args,
                            **job.kwargs
                        )
                    except AttributeError:
                        # Fallback pour Python < 3.9
                        loop = asyncio.get_event_loop()
                        result_value = await loop.run_in_executor(
                            None,
                            lambda: job.function(*job.args, **job.kwargs)
                        )
                
                # Calculer la durée
                duration = time.time() - start_time
                
                return ExecutionResult(
                    status=ExecutionStatus.SUCCESS,
                    result=result_value,
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
            
            finally:
                self._running_count -= 1
    
    def shutdown(self) -> None:
        """Arrête l'executor.
        
        Pour l'executor asynchrone, on attend que tous les jobs
        en cours se terminent (pas de force-kill ici pour respecter
        la propriété).
        """
        # Attendre que tous les jobs en cours se terminent
        # Note: Cette méthode est sync, donc on ne peut pas await
        # L'utilisateur devra gérer le shutdown proprement depuis
        # une fonction async si nécessaire
        pass
    
    async def wait_for_completion(self, timeout: float = 30.0) -> None:
        """Attend que tous les jobs en cours se terminent.
        
        Cette méthode peut être appelée pour s'assurer que tous
        les jobs sont complétés avant de fermer l'application.
        
        Args:
            timeout: Timeout en secondes (défaut: 30)
        
        Raises:
            asyncio.TimeoutError: Si le timeout est atteint
        """
        start_time = time.time()
        while self._running_count > 0:
            if time.time() - start_time > timeout:
                raise asyncio.TimeoutError(
                    f"Timeout waiting for {self._running_count} jobs to complete"
                )
            await asyncio.sleep(0.1)
    
    @property
    def running_count(self) -> int:
        """Retourne le nombre de jobs actuellement en cours.
        
        Returns:
            Le nombre de jobs en cours
        """
        return self._running_count

