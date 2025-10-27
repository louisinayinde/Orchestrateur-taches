"""File d'attente pour les jobs.

Ce module implémente une file d'attente FIFO thread-safe pour les jobs.
"""

from queue import Queue
from typing import Optional

from orchestrator.core.job import Job


class TaskQueue:
    """File d'attente thread-safe pour les jobs.
    
    Utilise la classe Queue de Python qui est thread-safe par défaut.
    Les jobs sont ajoutés en fin (FIFO - First In First Out).
    
    Attributes:
        _queue: Queue interne thread-safe
    
    Example:
        >>> queue = TaskQueue()
        >>> queue.push(job1)
        >>> queue.push(job2)
        >>> job = queue.pop()  # Récupère job1 (FIFO)
        >>> queue.size()  # 1
    """
    
    def __init__(self, maxsize: int = 0):
        """Initialise la queue.
        
        Args:
            maxsize: Taille maximale (0 = illimité)
        """
        self._queue: Queue = Queue(maxsize=maxsize)
    
    def push(self, job: Job) -> None:
        """Ajouter un job à la queue.
        
        La queue est thread-safe, donc cette méthode est sûre
        même si plusieurs threads l'utilisent simultanément.
        
        Args:
            job: Job à ajouter
        """
        self._queue.put(job)
    
    def pop(self, timeout: Optional[float] = None) -> Optional[Job]:
        """Récupérer le prochain job (bloquant).
        
        Args:
            timeout: Temps d'attente maximum en secondes (None = bloquant)
        
        Returns:
            Le prochain job ou None si timeout
        """
        try:
            return self._queue.get(timeout=timeout)
        except:
            return None
    
    def size(self) -> int:
        """Retourne la taille actuelle de la queue.
        
        Returns:
            Nombre de jobs dans la queue
        """
        return self._queue.qsize()
    
    def is_empty(self) -> bool:
        """Vérifie si la queue est vide.
        
        Returns:
            True si la queue est vide, False sinon
        """
        return self._queue.empty()

