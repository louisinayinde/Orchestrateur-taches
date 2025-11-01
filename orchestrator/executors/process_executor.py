"""Exécuteur avec multiprocessing.

Ce module implémente un executor qui utilise ProcessPoolExecutor
pour exécuter les jobs dans des processus séparés, idéal pour les
tâches CPU-bound qui nécessitent un parallélisme réel.
"""

import asyncio
import os
import time
import traceback
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from typing import TYPE_CHECKING

from orchestrator.core.execution import ExecutionResult, ExecutionStatus

if TYPE_CHECKING:
    from orchestrator.core.job import Job

from orchestrator.executors.base import BaseExecutor


class ProcessExecutor(BaseExecutor):
    """Exécuteur avec ProcessPoolExecutor.
    
    Exécute les jobs dans un pool de processus en utilisant ProcessPoolExecutor.
    Chaque process a son propre GIL, permettant un vrai parallélisme CPU.
    
    Idéal pour :
    - CPU-bound tasks (calculs intensifs, traitement d'images)
    - Tâches qui nécessitent tous les CPU cores
    - Contournement du GIL pour du code Python pur
    
    Limitations :
    - Les fonctions doivent être picklable
    - Overhead plus élevé que threads (IPC)
    - Pas de partage de mémoire (communication via pickle)
    
    Attributes:
        name: Nom de l'executor
        pool_size: Taille du pool de processus
        executor: ProcessPoolExecutor instance
        _running_count: Nombre de jobs actuellement en cours
    
    Example:
        >>> executor = ProcessExecutor(pool_size=4)
        >>> result = await executor.execute(job)
        >>> print(result.status)  # SUCCESS or FAILED
    """
    
    def __init__(self, pool_size: int | None = None):
        """Initialise l'executor multiprocessing.
        
        Args:
            pool_size: Nombre de processus dans le pool
                      (None = os.cpu_count(), défaut: None)
        """
        self.name = "ProcessExecutor"
        self.pool_size = pool_size or os.cpu_count() or 4
        self.executor = ProcessPoolExecutor(max_workers=self.pool_size)
        self._running_count = 0
    
    async def execute(self, job: "Job") -> ExecutionResult:
        """Exécute un job dans un process du pool.
        
        La méthode soumet le job au ProcessPoolExecutor et attend
        le résultat. Les fonctions doivent être picklable.
        
        Args:
            job: Le job à exécuter
        
        Returns:
            Le résultat de l'exécution avec statut SUCCESS ou FAILED
        
        Raises:
            TypeError: Si la fonction n'est pas picklable
        
        Example:
            >>> def cpu_intensive_task(n: int):
            ...     total = 0
            ...     for i in range(n):
            ...         total += i * i
            ...     return total
            >>> 
            >>> job = Job(name="compute", function=cpu_intensive_task, args=(1_000_000,))
            >>> result = await executor.execute(job)
        """
        start_time = time.time()
        
        self._running_count += 1
        
        try:
            # Soumettre le job au process pool et attendre le résultat
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

