"""Configuration pour l'orchestrateur.

Ce module définit la configuration du système avec support pour YAML et variables d'environnement.
"""

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Configuration de l'orchestrateur.
    
    Supporte le chargement depuis :
    - Fichier YAML (config.yaml)
    - Variables d'environnement (préfixe ORCH_)
    - Valeurs par défaut
    
    Les variables d'environnement ont la priorité sur le fichier YAML.
    
    Attributes:
        database_url: Chemin vers la base de données
        max_async_concurrent: Nombre maximum de jobs async simultanés
        thread_pool_size: Taille du pool de threads
        process_pool_size: Taille du pool de processus (None = os.cpu_count())
        scheduler_tick_seconds: Intervalle du scheduler en secondes
        default_max_retries: Nombre de retries par défaut
        retry_backoff_base: Base pour l'exponential backoff
        metrics_port: Port pour les métriques Prometheus
        metrics_enabled: Activer les métriques
        log_level: Niveau de logging
        log_format: Format des logs (json ou text)
        retention_days: Nombre de jours de rétention des exécutions
    """
    
    model_config = SettingsConfigDict(
        env_prefix="ORCH_",
        case_sensitive=False,
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # Database
    database_url: str = Field(default="sqlite:///jobs.db", description="URL de la base de données")
    pool_size: int = Field(default=5, ge=1, description="Taille du pool de connexions DB")
    
    # Executors
    max_async_concurrent: int = Field(default=10, ge=1, description="Nombre max de jobs async simultanés")
    thread_pool_size: int = Field(default=5, ge=1, description="Taille du pool de threads")
    process_pool_size: Optional[int] = Field(default=None, description="Taille du pool de processus (None = cpu_count)")
    
    # Scheduler
    scheduler_tick_seconds: int = Field(default=1, ge=1, description="Intervalle de tick du scheduler")
    scheduler_max_instances: int = Field(default=3, ge=1, description="Nombre max d'instances d'un job")
    
    # Resilience
    default_max_retries: int = Field(default=3, ge=0, description="Nombre de retries par défaut")
    retry_backoff_base: float = Field(default=2.0, gt=1.0, description="Base pour exponential backoff")
    retry_backoff_max: int = Field(default=300, ge=1, description="Temps max entre retries (secondes)")
    default_timeout: int = Field(default=3600, ge=1, description="Timeout par défaut (secondes)")
    
    # Monitoring
    metrics_port: int = Field(default=9090, ge=1024, le=65535, description="Port des métriques Prometheus")
    metrics_host: str = Field(default="0.0.0.0", description="Host des métriques")
    metrics_enabled: bool = Field(default=True, description="Activer les métriques")
    
    # Logging
    log_level: str = Field(default="INFO", description="Niveau de logging")
    log_format: str = Field(default="json", description="Format des logs (json/text)")
    log_file: Optional[str] = Field(default=None, description="Fichier de logs (None = stdout)")
    
    # Queue
    queue_max_size: int = Field(default=1000, ge=1, description="Taille max de la queue")
    
    # Maintenance
    retention_days: int = Field(default=30, ge=1, description="Jours de rétention")
    cleanup_enabled: bool = Field(default=True, description="Activer le nettoyage automatique")
    cleanup_schedule: str = Field(default="0 2 * * *", description="Schedule de cleanup (cron)")
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Valider le niveau de logging."""
        valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level doit être un de : {valid_levels}")
        return v.upper()
    
    @field_validator('log_format')
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Valider le format des logs."""
        if v.lower() not in {'json', 'text'}:
            raise ValueError("log_format doit être 'json' ou 'text'")
        return v.lower()
    
    @classmethod
    def load_from_yaml(cls, config_path: Optional[Path] = None) -> 'Config':
        """Charger la configuration depuis un fichier YAML.
        
        Args:
            config_path: Chemin vers le fichier config.yaml (None = chercher dans CWD)
            
        Returns:
            Configuration chargée
            
        Raises:
            FileNotFoundError: Si le fichier n'existe pas
            yaml.YAMLError: Si le fichier est invalide
        """
        if config_path is None:
            config_path = Path.cwd() / "config.yaml"
        
        if not config_path.exists():
            # Retourner les valeurs par défaut si pas de fichier
            return cls()
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f)
        
        # Aplatir la structure YAML pour la compatibilité avec BaseSettings
        flat_dict = _flatten_config(config_dict)
        
        # Charger avec les valeurs YAML
        config = cls(**flat_dict)
        return config
    
    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> 'Config':
        """Charger la configuration depuis YAML et variables d'environnement.
        
        Les variables d'environnement ont la priorité sur le fichier YAML.
        
        Args:
            config_path: Chemin vers le fichier config.yaml
            
        Returns:
            Configuration chargée
        """
        # Charger depuis YAML si possible
        try:
            config = cls.load_from_yaml(config_path)
        except Exception:
            config = cls()
        
        # Les variables d'environnement seront appliquées automatiquement par Pydantic
        return config
    
    def save_to_yaml(self, config_path: Optional[Path] = None) -> None:
        """Sauvegarder la configuration dans un fichier YAML.
        
        Args:
            config_path: Chemin vers le fichier config.yaml
        """
        if config_path is None:
            config_path = Path.cwd() / "config.yaml"
        
        # Convertir en dictionnaire structuré
        config_dict = _unflatten_config(self.model_dump())
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config_dict, f, default_flow_style=False, sort_keys=False)


def _flatten_config(config_dict: dict, parent_key: str = '', sep: str = '_') -> dict:
    """Aplatir une configuration YAML imbriquée.
    
    Args:
        config_dict: Dictionnaire de configuration
        parent_key: Clé parente pour la récursion
        sep: Séparateur entre les clés
        
    Returns:
        Dictionnaire aplati
    """
    items = []
    for k, v in config_dict.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_config(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    
    # Mappings spéciaux pour la compatibilité avec la structure YAML
    result = dict(items)
    
    # Mapping database
    if 'database' in config_dict:
        result['database_url'] = config_dict.get('database', {}).get('url', 'sqlite:///jobs.db')
        result['pool_size'] = config_dict.get('database', {}).get('pool_size', 5)
    
    # Mapping executors
    if 'executors' in config_dict:
        result['max_async_concurrent'] = config_dict.get('executors', {}).get('async', {}).get('max_concurrent', 10)
        result['thread_pool_size'] = config_dict.get('executors', {}).get('thread', {}).get('pool_size', 5)
        process_size = config_dict.get('executors', {}).get('process', {}).get('pool_size')
        if process_size is not None:
            result['process_pool_size'] = process_size
    
    # Mapping scheduler
    if 'scheduler' in config_dict:
        result['scheduler_tick_seconds'] = config_dict.get('scheduler', {}).get('tick_seconds', 1)
        result['scheduler_max_instances'] = config_dict.get('scheduler', {}).get('max_instances', 3)
    
    # Mapping resilience
    if 'resilience' in config_dict:
        result['default_max_retries'] = config_dict.get('resilience', {}).get('default_max_retries', 3)
        result['retry_backoff_base'] = config_dict.get('resilience', {}).get('retry_backoff_base', 2.0)
        result['retry_backoff_max'] = config_dict.get('resilience', {}).get('retry_backoff_max', 300)
        result['default_timeout'] = config_dict.get('resilience', {}).get('default_timeout', 3600)
    
    # Mapping monitoring
    if 'monitoring' in config_dict:
        result['metrics_enabled'] = config_dict.get('monitoring', {}).get('metrics', {}).get('enabled', True)
        result['metrics_port'] = config_dict.get('monitoring', {}).get('metrics', {}).get('port', 9090)
        result['metrics_host'] = config_dict.get('monitoring', {}).get('metrics', {}).get('host', '0.0.0.0')
        result['log_level'] = config_dict.get('monitoring', {}).get('logging', {}).get('level', 'INFO')
        result['log_format'] = config_dict.get('monitoring', {}).get('logging', {}).get('format', 'json')
        result['log_file'] = config_dict.get('monitoring', {}).get('logging', {}).get('file')
    
    # Mapping queue
    if 'queue' in config_dict:
        result['queue_max_size'] = config_dict.get('queue', {}).get('max_size', 1000)
    
    # Mapping maintenance
    if 'maintenance' in config_dict:
        result['retention_days'] = config_dict.get('maintenance', {}).get('retention_days', 30)
        result['cleanup_enabled'] = config_dict.get('maintenance', {}).get('cleanup_enabled', True)
        result['cleanup_schedule'] = config_dict.get('maintenance', {}).get('cleanup_schedule', '0 2 * * *')
    
    return result


def _unflatten_config(config_dict: dict, sep: str = '_') -> dict:
    """Reconstruire une configuration structurée depuis un dict aplati.
    
    Reconstitue la structure YAML depuis les champs Pydantic aplatis.
    
    Args:
        config_dict: Dictionnaire aplati
        sep: Séparateur entre les clés (non utilisé, mapping manuel)
        
    Returns:
        Dictionnaire structuré compatible avec config.yaml.example
    """
    result = {
        'database': {
            'url': config_dict.get('database_url', 'sqlite:///jobs.db'),
            'pool_size': config_dict.get('pool_size', 5),
            'echo': False
        },
        'executors': {
            'async': {
                'max_concurrent': config_dict.get('max_async_concurrent', 10),
                'enabled': True
            },
            'thread': {
                'pool_size': config_dict.get('thread_pool_size', 5),
                'enabled': True
            },
            'process': {
                'pool_size': config_dict.get('process_pool_size'),
                'enabled': True
            }
        },
        'scheduler': {
            'enabled': True,
            'tick_seconds': config_dict.get('scheduler_tick_seconds', 1),
            'max_instances': config_dict.get('scheduler_max_instances', 3)
        },
        'resilience': {
            'default_max_retries': config_dict.get('default_max_retries', 3),
            'retry_backoff_base': config_dict.get('retry_backoff_base', 2.0),
            'retry_backoff_max': config_dict.get('retry_backoff_max', 300),
            'default_timeout': config_dict.get('default_timeout', 3600)
        },
        'monitoring': {
            'metrics': {
                'enabled': config_dict.get('metrics_enabled', True),
                'port': config_dict.get('metrics_port', 9090),
                'host': config_dict.get('metrics_host', '0.0.0.0')
            },
            'logging': {
                'level': config_dict.get('log_level', 'INFO'),
                'format': config_dict.get('log_format', 'json'),
                'file': config_dict.get('log_file')
            }
        },
        'queue': {
            'max_size': config_dict.get('queue_max_size', 1000),
            'priority_enabled': False
        },
        'maintenance': {
            'retention_days': config_dict.get('retention_days', 30),
            'cleanup_enabled': config_dict.get('cleanup_enabled', True),
            'cleanup_schedule': config_dict.get('cleanup_schedule', '0 2 * * *')
        }
    }
    return result

