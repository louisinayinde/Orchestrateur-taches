"""Module de logging structuré.

Ce module configure le logging avec support JSON pour l'orchestrateur.
"""

import json
import logging
import sys
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """Formatter JSON pour les logs structurés.
    
    Convertit les logs en JSON avec les champs : timestamp, level, logger, message, extra.
    
    Example:
        >>> logger = configure_logger()
        >>> logger.info("Job started", extra={"job_id": 123, "job_name": "test"})
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Formate un log en JSON.
        
        Args:
            record: Le record de log
            
        Returns:
            Chaine JSON formatée
        """
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Ajouter les champs extra
        if hasattr(record, 'extra') and record.extra:
            log_data.update(record.extra)
        else:
            # Ajouter tous les attributs qui ne sont pas standard
            for key, value in record.__dict__.items():
                if key not in [
                    'name', 'msg', 'args', 'created', 'filename', 'funcName',
                    'levelname', 'levelno', 'lineno', 'module', 'msecs',
                    'message', 'pathname', 'process', 'processName',
                    'relativeCreated', 'thread', 'threadName', 'exc_info',
                    'exc_text', 'stack_info', 'asctime', 'args'
                ]:
                    log_data[key] = value
        
        # Ajouter l'exception si présente
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """Formatter texte classique.
    
    Ajoute les champs extra à la fin du message.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Formate un log en texte."""
        # Formater le message de base
        msg = super().format(record)
        
        # Ajouter les champs extra
        if hasattr(record, 'extra') and record.extra:
            extra_str = " | ".join([f"{k}={v}" for k, v in record.extra.items()])
            return f"{msg} | {extra_str}"
        
        return msg


def configure_logger(
    name: str = "orchestrator",
    level: str = "INFO",
    format_type: str = "json",
    extra_context: Dict[str, Any] = None
) -> logging.Logger:
    """Configure le logger pour l'orchestrateur.
    
    Args:
        name: Nom du logger
        level: Niveau de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Type de format (json ou text)
        extra_context: Contexte additionnel à ajouter à tous les logs
    
    Returns:
        Logger configuré
    
    Example:
        >>> logger = configure_logger(level="INFO", format_type="json")
        >>> logger.info("System started")
        # {"timestamp": "2024-01-01 12:00:00", "level": "INFO", "logger": "orchestrator", "message": "System started"}
        
        >>> logger = configure_logger(level="DEBUG", format_type="text")
        >>> logger.info("Job completed", extra={"job_id": 123, "duration": 1.5})
        # 2024-01-01 12:00:00 - orchestrator - INFO - Job completed | job_id=123 | duration=1.5
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Supprimer les handlers existants
    logger.handlers.clear()
    
    # Créer le handler pour stdout
    handler = logging.StreamHandler(sys.stdout)
    
    # Sélectionner le formatter
    if format_type == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Ajouter le contexte extra si fourni
    if extra_context:
        adapter = logging.LoggerAdapter(logger, extra_context)
        return adapter
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """Récupère un logger par son nom.
    
    Args:
        name: Nom du logger (None = logger root)
        
    Returns:
        Logger
    """
    if name:
        return logging.getLogger(name)
    return logging.getLogger()

