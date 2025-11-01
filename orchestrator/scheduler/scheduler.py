"""Scheduler principal pour la planification de jobs.

Ce module implémente un scheduler qui vérifie périodiquement les jobs
planifiés et les ajoute à la queue d'exécution.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from orchestrator.scheduler.cron_parser import CronParser, CronSchedule

if TYPE_CHECKING:
    from orchestrator.core.job import Job
    from orchestrator.db.repository import JobRepository
    from orchestrator.queue.task_queue import TaskQueue


class Scheduler:
    """Scheduler pour la planification de jobs.
    
    Cette classe vérifie périodiquement les schedules en base de données
    et ajoute les jobs qui doivent s'exécuter à la queue.
    
    Le scheduler tourne dans une boucle (tick loop) et vérifie chaque
    tick_seconds s'il y a des jobs à exécuter.
    
    Attributes:
        repository: Repository pour accéder aux schedules en DB
        queue: Queue pour ajouter les jobs à exécuter
        tick_seconds: Intervalle entre chaque vérification (secondes)
        running: Indique si le scheduler tourne
        _task: Task asyncio pour le scheduler
    
    Example:
        >>> scheduler = Scheduler(repository, queue, tick_seconds=60)
        >>> await scheduler.start()
        >>> # Scheduler tourne en arrière-plan
    """
    
    def __init__(
        self,
        repository: "JobRepository",
        queue: "TaskQueue",
        tick_seconds: int = 60
    ):
        """Initialise le scheduler.
        
        Args:
            repository: Repository pour la persistance
            queue: Queue pour ajouter les jobs
            tick_seconds: Intervalle entre les vérifications (défaut: 60s)
        """
        self.repository = repository
        self.queue = queue
        self.tick_seconds = tick_seconds
        self.running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Démarre le scheduler.
        
        Le scheduler commence à vérifier les schedules périodiquement.
        Cette méthode est non-bloquante et retourne immédiatement.
        """
        if self.running:
            return
        
        self.running = True
        self._task = asyncio.create_task(self._run_loop())
    
    async def stop(self) -> None:
        """Arrête le scheduler.
        
        Le scheduler cesse de vérifier les schedules et attend
        que la dernière vérification se termine.
        """
        if not self.running:
            return
        
        self.running = False
        
        if self._task:
            await self._task
    
    async def _run_loop(self) -> None:
        """Boucle principale du scheduler.
        
        Vérifie périodiquement les schedules et ajoute les jobs
        à la queue si nécessaire.
        """
        while self.running:
            try:
                await self._tick()
            except Exception as e:
                # Logger l'erreur mais continuer
                print(f"Scheduler error: {e}")
            
            # Attendre avant le prochain tick
            await asyncio.sleep(self.tick_seconds)
    
    async def _tick(self) -> None:
        """Effectue une vérification des schedules.
        
        Récupère tous les schedules actifs et vérifie si des jobs
        doivent s'exécuter maintenant.
        """
        now = datetime.now()
        
        # Récupérer tous les schedules actifs
        schedules = self._get_active_schedules()
        
        for schedule in schedules:
            # Vérifier si le job doit s'exécuter
            if self._should_execute(schedule, now):
                # Ajouter le job à la queue
                await self._enqueue_job(schedule)
    
    def _get_active_schedules(self) -> list[dict]:
        """Récupère tous les schedules actifs depuis la DB.
        
        Returns:
            Liste des schedules (dicts)
        """
        conn = self.repository.db_path
        # Pour l'instant, utilisons get_connection depuis repository
        from orchestrator.db.connection import get_connection
        
        conn = get_connection(conn)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT s.id, s.job_id, s.cron_expression, s.run_at, s.enabled
                FROM schedules s
                WHERE s.enabled = 1
            """)
            
            rows = cursor.fetchall()
            
            # Convertir en list de dicts
            schedules = []
            for row in rows:
                schedules.append({
                    "id": row[0],
                    "job_id": row[1],
                    "cron_expression": row[2],
                    "run_at": row[3],
                    "enabled": row[4]
                })
            
            return schedules
        finally:
            cursor.close()
            conn.close()
    
    def _should_execute(self, schedule: dict, now: datetime) -> bool:
        """Vérifie si un schedule doit s'exécuter maintenant.
        
        Args:
            schedule: Le schedule à vérifier
            now: Le moment actuel
        
        Returns:
            True si le job doit s'exécuter, False sinon
        """
        # Schedule one-time (run_at)
        if schedule["run_at"]:
            run_at = datetime.fromisoformat(schedule["run_at"])
            # S'exécuter si la date est passée ou maintenant
            return now >= run_at
        
        # Schedule cron (cron_expression)
        if schedule["cron_expression"]:
            cron_schedule = CronParser.parse(schedule["cron_expression"])
            return CronParser.should_run_now(cron_schedule, now)
        
        return False
    
    async def _enqueue_job(self, schedule: dict) -> None:
        """Ajoute un job à la queue d'exécution.
        
        Args:
            schedule: Le schedule contenant le job_id
        """
        # Récupérer le job depuis la DB
        job = self.repository.get_job(schedule["job_id"])
        
        if job:
            # Ajouter à la queue
            self.queue.push(job)
            print(f"Scheduled job '{job.name}' added to queue")

