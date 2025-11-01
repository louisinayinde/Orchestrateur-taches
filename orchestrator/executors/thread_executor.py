"""Exécuteur avec threading.

Ce module implémente un executor qui utilise ThreadPoolExecutor
pour exécuter les jobs dans des threads, idéal pour les tâches
I/O-bound légères ou du code legacy non-async.
"""

import asyncio
import time
import traceback
from concurrent.futures import TimeoutError as FuturesTimeoutError
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING

from orchestrator.core.execution import ExecutionResult, ExecutionStatus

if TYPE_CHECKING:
    from orchestrator.core.job import Job

from orchestrator.executors.base import BaseExecutor


class ThreadExecutor(BaseExecutor):
    """Exécuteur avec ThreadPoolExecutor.
    
    Exécute les jobs dans un pool de threads en utilisant ThreadPoolExecutor.
    Idéal pour :
    - I/O-bound tasks légères (< 100 tâches concurrentes)
    - Code legacy non-async
    - Opérations bloquantes (file I/O, DB queries sync)
    
    Contrairement à AsyncExecutor, ThreadExecutor utilise de vrais threads
    du système d'exploitation. Chaque thread a un overhead mémoire (~1-2 MB).
    
    Attributes:
        name: Nom de l'executor
        pool_size: Taille du pool de threads
        executor: ThreadPoolExecutor instance
        _running_count: Nombre de jobs actuellement en cours
    
    Example:
        >>> executor = ThreadExecutor(pool_size=5)
        >>> result = await executor.execute(job)
        >>> print(result.status)  # SUCCESS or FAILED
    """
    
    def __init__(self, pool_size: int = 5):
        """Initialise l'executor threading.
        
        Args:
            pool_size: Nombre de threads dans le pool (défaut: 5)
        """
        self.name = "ThreadExecutor"
        self.pool_size = pool_size
        self.executor = ThreadPoolExecutor(max_workers=pool_size)
        self._running_count = 0
    
    async def execute(self, job: "Job") -> ExecutionResult:
        """Exécute un job dans un thread du pool.
        
        La méthode soumet le job au ThreadPoolExecutor et attend
        le résultat. Toutes les fonctions sont supportées (sync uniquement).
        
        Args:
            job: Le job à exécuter
        
        Returns:
            Le résultat de l'exécution avec statut SUCCESS ou FAILED
        
        Example:
            >>> def my_sync_func(n: int):
            ...     import time
            ...     time.sleep(1)  # I/O simulé
            ...     return n * 2
            >>> 
            >>> job = Job(name="my_job", function=my_sync_func, args=(10,))
            >>> result = await executor.execute(job)
        """
        start_time = time.time()
        
        self._running_count += 1
        
        try:
            # Soumettre le job au thread pool et attendre le résultat
            # Note: On utilise run_in_executor None pour attendre une future
            loop = asyncio.get_event_loop()
            
            # Soumettre dans un thread séparé pour éviter de bloquer
            def run_job():
                future = self.executor.submit(job.function, *job.args, **job.kwargs)
                # Si timeout, utiliser future.result(timeout)
                if job.timeout_seconds:
                    return future.result(timeout=job.timeout_seconds)
                return future.result()
            
            result_value = await loop.run_in_executor(None, run_job)
            
            # Calculer la durée
            duration = time.time() - start_time
            
            return ExecutionResult(
                status=ExecutionStatus.SUCCESS,
                result=result_value,
                duration_seconds=duration
            )
            
        except FuturesTimeoutError:
            # Timeout atteint
            duration = time.time() - start_time
            return ExecutionResult(
                status=ExecutionStatus.TIMEOUT,
                error=f"Job timed out after {job.timeout_seconds}s",
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
    
    def shutdown(self, wait: bool = True) -> None:
        """Arrête l'executor et libère les ressources.
        
        Args:
            wait: Attendre que les jobs en cours se terminent (défaut: True)
        """
        self.executor.shutdown(wait=wait)
    
    @property
    def running_count(self) -> int:
        """Retourne le nombre de jobs actuellement en cours.
        
        Returns:
            Le nombre de jobs en cours
        """
        return self._running_count

