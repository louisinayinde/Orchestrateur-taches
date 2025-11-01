"""Parser pour expressions cron simplifiées.

Ce module implémente un parser pour des expressions cron simplifiées.
Support des formats courants pour la planification de jobs.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class CronSchedule:
    """Représentation d'une expression cron.
    
    Attributes:
        minute: Minute (0-59) ou '*' pour toutes
        hour: Heure (0-23) ou '*' pour toutes
        day_of_month: Jour du mois (1-31) ou '*' pour tous
        month: Mois (1-12) ou '*' pour tous
        day_of_week: Jour de la semaine (0-6, 0=dimanche) ou '*' pour tous
    """
    
    minute: str = "*"
    hour: str = "*"
    day_of_month: str = "*"
    month: str = "*"
    day_of_week: str = "*"
    
    def __repr__(self) -> str:
        """Retourne l'expression cron complète."""
        return f"{self.minute} {self.hour} {self.day_of_month} {self.month} {self.day_of_week}"


class CronParser:
    """Parser pour expressions cron simplifiées.
    
    Supporte les formats suivants :
    - Format standard : "minute hour day month dayofweek"
    - Toutes les minutes : "*/5 * * * *" (toutes les 5 minutes)
    - Chaque heure : "0 * * * *" (à chaque heure)
    - Format simplifié : "*/10" → "*/10 * * * *"
    
    Example:
        >>> parser = CronParser()
        >>> schedule = parser.parse("*/5 * * * *")
        >>> print(schedule.minute)  # "*/5"
    """
    
    # Expressions régulières pour différents formats
    PATTERN_CRON_FULL = re.compile(
        r"^\s*(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*$"
    )
    
    PATTERN_EVERY_N = re.compile(r"^\*/(\d+)$")
    PATTERN_SPECIFIC = re.compile(r"^(\d+)$")
    PATTERN_RANGE = re.compile(r"^(\d+)-(\d+)$")
    PATTERN_LIST = re.compile(r"^(\d+)(?:,(\d+))*$")
    
    @staticmethod
    def parse(cron_expr: str) -> CronSchedule:
        """Parse une expression cron simplifiée.
        
        Args:
            cron_expr: Expression cron à parser
        
        Returns:
            Un CronSchedule
        
        Raises:
            ValueError: Si l'expression est invalide
        
        Example:
            >>> schedule = CronParser.parse("*/5 * * * *")
            >>> print(schedule.minute)  # "*/5"
            
            >>> schedule = CronParser.parse("0 12 * * *")
            >>> print(schedule.hour)  # "12"
        """
        cron_expr = cron_expr.strip()
        
        # Format simplifié : */N → */N * * * *
        if cron_expr.startswith("*/"):
            return CronSchedule(minute=cron_expr)
        
        # Format complet : "minute hour day month dayofweek"
        match = CronParser.PATTERN_CRON_FULL.match(cron_expr)
        if match:
            return CronSchedule(
                minute=match.group(1),
                hour=match.group(2),
                day_of_month=match.group(3),
                month=match.group(4),
                day_of_week=match.group(5)
            )
        
        # Format invalide
        raise ValueError(f"Invalid cron expression: {cron_expr}")
    
    @staticmethod
    def should_run_now(schedule: CronSchedule, now: datetime) -> bool:
        """Vérifie si un schedule doit s'exécuter maintenant.
        
        Args:
            schedule: Le schedule à vérifier
            now: Le moment actuel
        
        Returns:
            True si le job doit s'exécuter, False sinon
        
        Example:
            >>> schedule = CronParser.parse("*/5 * * * *")
            >>> now = datetime(2024, 1, 1, 12, 5, 0)
            >>> CronParser.should_run_now(schedule, now)
            True
        """
        return (
            CronParser._match_field(schedule.minute, now.minute)
            and CronParser._match_field(schedule.hour, now.hour)
            and CronParser._match_field(schedule.day_of_month, now.day)
            and CronParser._match_field(schedule.month, now.month)
            and CronParser._match_field(schedule.day_of_week, now.weekday())
        )
    
    @staticmethod
    def _match_field(field: str, value: int) -> bool:
        """Vérifie si un champ cron correspond à une valeur.
        
        Args:
            field: Le champ cron (ex: "*/5", "12", "*")
            value: La valeur à vérifier (ex: 5)
        
        Returns:
            True si ça correspond, False sinon
        """
        # Tous les valeurs
        if field == "*":
            return True
        
        # Toutes les N unités : */5
        match = CronParser.PATTERN_EVERY_N.match(field)
        if match:
            n = int(match.group(1))
            return value % n == 0
        
        # Valeur spécifique : 12
        match = CronParser.PATTERN_SPECIFIC.match(field)
        if match:
            return value == int(match.group(1))
        
        # Plage : 10-20
        match = CronParser.PATTERN_RANGE.match(field)
        if match:
            start = int(match.group(1))
            end = int(match.group(2))
            return start <= value <= end
        
        # Liste : 5,10,15
        if "," in field:
            values = [int(x) for x in field.split(",")]
            return value in values
        
        # Format invalide, par défaut ne matche pas
        return False
    
    @staticmethod
    def is_valid(cron_expr: str) -> bool:
        """Vérifie si une expression cron est valide.
        
        Args:
            cron_expr: Expression cron à vérifier
        
        Returns:
            True si valide, False sinon
        
        Example:
            >>> CronParser.is_valid("*/5 * * * *")
            True
            >>> CronParser.is_valid("invalid")
            False
        """
        try:
            CronParser.parse(cron_expr)
            return True
        except ValueError:
            return False


# Expressions courantes prédéfinies

COMMON_SCHEDULES = {
    "every_minute": "* * * * *",
    "every_5_minutes": "*/5 * * * *",
    "every_10_minutes": "*/10 * * * *",
    "every_15_minutes": "*/15 * * * *",
    "every_30_minutes": "*/30 * * * *",
    "hourly": "0 * * * *",
    "daily": "0 0 * * *",
    "weekly": "0 0 * * 0",
    "monthly": "0 0 1 * *",
}

