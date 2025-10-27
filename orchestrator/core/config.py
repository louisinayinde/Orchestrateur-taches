"""Configuration pour l'orchestrateur.

Ce module définit la configuration par défaut du système.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    """Configuration de l'orchestrateur.
    
    Attributes:
        database_url: Chemin vers la base de données
        max_async_concurrent: Nombre maximum de jobs async simultanés
        thread_pool_size: Taille du pool de threads
        process_pool_size: Taille du pool de processus
        scheduler_tick_seconds: Intervalle du scheduler en secondes
        default_max_retries: Nombre de retries par défaut
        retry_backoff_base: Base pour l'exponential backoff
        metrics_port: Port pour les métriques Prometheus
        metrics_enabled: Activer les métriques
        log_level: Niveau de logging
        log_format: Format des logs (json ou text)
        retention_days: Nombre de jours de rétention des exécutions
    """
    
    database_url: str = "sqlite:///jobs.db"
    max_async_concurrent: int = 10
    thread_pool_size: int = 5
    process_pool_size: int = 4
    scheduler_tick_seconds: int = 1
    default_max_retries: int = 3
    retry_backoff_base: float = 2.0
    metrics_port: int = 9090
    metrics_enabled: bool = True
    log_level: str = "INFO"
    log_format: str = "json"
    retention_days: int = 30

