"""Modèles de données pour les Exécutions.

Ce module définit les classes Execution et ExecutionResult.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class ExecutionStatus(Enum):
    """Statut d'une exécution de job."""
    
    PENDING = "PENDING"      # En attente d'exécution
    RUNNING = "RUNNING"       # En cours d'exécution
    SUCCESS = "SUCCESS"       # Succès
    FAILED = "FAILED"         # Échec
    TIMEOUT = "TIMEOUT"       # Timeout atteint


@dataclass
class ExecutionResult:
    """Résultat d'une exécution de job.
    
    Attributes:
        status: Statut de l'exécution
        result: Résultat du job (si succès)
        error: Message d'erreur (si échec)
        traceback: Stack trace complète (si erreur)
        duration_seconds: Durée d'exécution en secondes
    """
    
    status: ExecutionStatus
    result: Any = None
    error: Optional[str] = None
    traceback: Optional[str] = None
    duration_seconds: Optional[float] = None


@dataclass
class Execution:
    """Une exécution d'un job.
    
    Attributes:
        id: Identifiant unique de l'exécution (None si pas encore persisté)
        job_id: Identifiant du job exécuté
        status: Statut actuel de l'exécution
        attempt: Numéro de tentative (démarre à 1)
        started_at: Date/heure de début
        completed_at: Date/heure de fin (None si en cours)
        duration_seconds: Durée totale en secondes
        result: Résultat sérialisé (JSON)
        error_message: Message d'erreur
        traceback: Stack trace
    """
    
    job_id: int
    id: Optional[int] = None
    status: ExecutionStatus = ExecutionStatus.PENDING
    attempt: int = 1
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    result: Any = None
    error_message: Optional[str] = None
    traceback: Optional[str] = None

