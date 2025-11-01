"""Système de retry avec exponential backoff.

Ce module implémente la logique de retry automatique pour les jobs
qui échouent, avec exponential backoff pour éviter la surcharge.
"""

import asyncio
import time
from typing import Optional

from orchestrator.core.execution import ExecutionResult, ExecutionStatus


class RetryStrategy:
    """Stratégie de retry avec exponential backoff.
    
    Implémente une logique de retry avec backoff exponentiel :
    - Tentative 1 : attente de 1s
    - Tentative 2 : attente de 2s
    - Tentative 3 : attente de 4s
    - etc.
    
    Cette approche aide à éviter la surcharge d'un service défaillant
    tout en donnant le temps au service de récupérer.
    
    Attributes:
        max_retries: Nombre maximum de tentatives
        backoff_base: Base pour le calcul exponentiel (défaut: 2)
        initial_delay: Délai initial en secondes (défaut: 1)
        max_delay: Délai maximum en secondes (défaut: 60)
    
    Example:
        >>> strategy = RetryStrategy(max_retries=3, backoff_base=2)
        >>> for attempt in range(1, 4):
        ...     delay = strategy.get_delay(attempt)
        ...     print(f"Attempt {attempt}: wait {delay}s")
        Attempt 1: wait 1s
        Attempt 2: wait 2s
        Attempt 3: wait 4s
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        backoff_base: float = 2.0,
        initial_delay: float = 1.0,
        max_delay: float = 60.0
    ):
        """Initialise la stratégie de retry.
        
        Args:
            max_retries: Nombre maximum de tentatives
            backoff_base: Base pour le calcul exponentiel
            initial_delay: Délai initial en secondes
            max_delay: Délai maximum en secondes
        """
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.initial_delay = initial_delay
        self.max_delay = max_delay
    
    def get_delay(self, attempt: int) -> float:
        """Calcule le délai d'attente pour une tentative donnée.
        
        La formule est : initial_delay * (backoff_base ^ (attempt - 1))
        
        Args:
            attempt: Numéro de la tentative (1-based)
        
        Returns:
            Délai en secondes
        
        Example:
            >>> strategy = RetryStrategy()
            >>> strategy.get_delay(1)  # 1s
            1.0
            >>> strategy.get_delay(2)  # 2s
            2.0
            >>> strategy.get_delay(3)  # 4s
            4.0
            >>> strategy.get_delay(4)  # 8s
            8.0
        """
        if attempt <= 0:
            return 0.0
        
        # Formule : delay = initial * (base ^ (attempt - 1))
        delay = self.initial_delay * (self.backoff_base ** (attempt - 1))
        
        # Limiter au maximum
        return min(delay, self.max_delay)
    
    def should_retry(self, attempt: int, result: ExecutionResult) -> bool:
        """Détermine si on doit réessayer après un échec.
        
        Args:
            attempt: Numéro de la tentative actuelle
            result: Résultat de l'exécution
        
        Returns:
            True si on doit réessayer, False sinon
        
        Example:
            >>> strategy = RetryStrategy(max_retries=3)
            >>> strategy.should_retry(1, failed_result)  # True
            True
            >>> strategy.should_retry(4, failed_result)  # False (max atteint)
            False
        """
        # Ne pas retry si succès
        if result.status == ExecutionStatus.SUCCESS:
            return False
        
        # Ne pas retry si on a atteint le maximum
        if attempt >= self.max_retries:
            return False
        
        # Retry pour les autres cas d'échec
        return True
    
    async def execute_with_retry(
        self,
        executor_func,
        max_retries: Optional[int] = None
    ) -> ExecutionResult:
        """Exécute une fonction avec retry automatique.
        
        Args:
            executor_func: Fonction async qui retourne ExecutionResult
            max_retries: Override du max_retries (optionnel)
        
        Returns:
            Le résultat final (succès ou échec après max retries)
        
        Example:
            >>> async def my_executor():
            ...     # Simule une exécution
            ...     return ExecutionResult(status=ExecutionStatus.FAILED)
            >>> 
            >>> strategy = RetryStrategy(max_retries=3)
            >>> result = await strategy.execute_with_retry(my_executor)
        """
        max_tries = max_retries or self.max_retries
        attempt = 1
        
        while True:
            # Exécuter la fonction
            result = await executor_func()
            
            # Vérifier si on doit retry
            if not self.should_retry(attempt, result):
                return result
            
            # Calculer le délai d'attente
            delay = self.get_delay(attempt)
            
            # Attendre avant de réessayer
            await asyncio.sleep(delay)
            
            # Incrémenter le compteur
            attempt += 1

