"""Repository pour les opérations CRUD sur la base de données.

Ce module implémente les opérations de persistance pour les jobs et executions.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from orchestrator.core.execution import Execution, ExecutionStatus
from orchestrator.core.job import Job, JobType

from orchestrator.db.connection import get_connection


class JobRepository:
    """Repository pour les jobs.
    
    Implémente les opérations CRUD pour les jobs et exécutions.
    Utilise SQLite pour la persistance.
    
    Attributes:
        db_path: Chemin vers le fichier de base de données
    
    Example:
        >>> repo = JobRepository()
        >>> job_id = repo.create_job(job)
        >>> job = repo.get_job(job_id)
        >>> repo.update_job(job)
    """
    
    def __init__(self, db_path: Path = Path.cwd() / "jobs.db"):
        """Initialise le repository.
        
        Args:
            db_path: Chemin vers la base de données SQLite
        """
        self.db_path = db_path
    
    def create_job(self, job: Job) -> int:
        """Crée un job dans la base de données.
        
        Args:
            job: Le job à créer
        
        Returns:
            L'ID du job créé
        """
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO jobs (
                    name, function_path, args_json, kwargs_json,
                    job_type, max_retries, timeout_seconds, idempotency_key
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.name,
                job.get_function_path(),
                json.dumps(job.args),
                json.dumps(job.kwargs),
                job.job_type.value,
                job.max_retries,
                job.timeout_seconds,
                job.idempotency_key
            ))
            
            job_id = cursor.lastrowid
            conn.commit()
            return job_id
        finally:
            cursor.close()
            conn.close()
    
    def get_job(self, job_id: int) -> Optional[Job]:
        """Récupère un job par son ID.
        
        Args:
            job_id: ID du job
        
        Returns:
            Le job ou None si non trouvé
        
        Note:
            Cette implémentation retourne un Job avec function=None
            car on ne peut pas désérialiser une fonction depuis la DB.
            Dans un système réel, il faudrait un système de registry des fonctions.
        """
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Reconstruire le Job
            # Note: function reste None car on ne peut pas le désérialiser
            job = Job(
                id=row[0],
                name=row[1],
                function=None,  # Ne peut pas être désérialisé
                args=json.loads(row[2] or "[]"),
                kwargs=json.loads(row[3] or "{}"),
                job_type=JobType(row[4]),
                max_retries=row[5],
                timeout_seconds=row[6],
                idempotency_key=row[7]
            )
            
            return job
        finally:
            cursor.close()
            conn.close()
    
    def delete_job(self, job_id: int) -> bool:
        """Supprime un job.
        
        Args:
            job_id: ID du job
        
        Returns:
            True si supprimé, False si non trouvé
        """
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            cursor.close()
            conn.close()
    
    def create_execution(self, job_id: int) -> int:
        """Crée une nouvelle exécution pour un job.
        
        Args:
            job_id: ID du job
        
        Returns:
            L'ID de l'exécution créée
        """
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO executions (
                    job_id, status, attempt, started_at
                ) VALUES (?, ?, ?, ?)
            """, (
                job_id,
                ExecutionStatus.PENDING.value,
                1,
                datetime.now().isoformat()
            ))
            
            execution_id = cursor.lastrowid
            conn.commit()
            return execution_id
        finally:
            cursor.close()
            conn.close()
    
    def update_execution(self, execution: Execution) -> bool:
        """Met à jour une exécution.
        
        Args:
            execution: L'exécution à mettre à jour
        
        Returns:
            True si mise à jour, False sinon
        """
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE executions 
                SET status = ?, 
                    attempt = ?,
                    completed_at = ?,
                    duration_seconds = ?,
                    result_json = ?,
                    error_message = ?,
                    traceback = ?
                WHERE id = ?
            """, (
                execution.status.value,
                execution.attempt,
                execution.completed_at.isoformat() if execution.completed_at else None,
                execution.duration_seconds,
                json.dumps(execution.result) if execution.result is not None else None,
                execution.error_message,
                execution.traceback,
                execution.id
            ))
            
            conn.commit()
            return cursor.rowcount > 0
        finally:
            cursor.close()
            conn.close()
    
    def get_execution(self, execution_id: int) -> Optional[Execution]:
        """Récupère une exécution par son ID.
        
        Args:
            execution_id: ID de l'exécution
        
        Returns:
            L'exécution ou None
        """
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM executions WHERE id = ?", (execution_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            started_at = datetime.fromisoformat(row[4]) if row[4] else None
            completed_at = datetime.fromisoformat(row[5]) if row[5] else None
            
            execution = Execution(
                id=row[0],
                job_id=row[1],
                status=ExecutionStatus(row[2]),
                attempt=row[3],
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=row[6],
                result=json.loads(row[7]) if row[7] else None,
                error_message=row[8],
                traceback=row[9]
            )
            
            return execution
        finally:
            cursor.close()
            conn.close()
    
    def list_executions(
        self,
        job_id: Optional[int] = None,
        status: Optional[ExecutionStatus] = None,
        limit: int = 100
    ) -> List[Execution]:
        """Liste les exécutions avec filtres optionnels.
        
        Args:
            job_id: Filtrer par job_id
            status: Filtrer par statut
            limit: Nombre maximum de résultats
        
        Returns:
            Liste des exécutions
        """
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        
        try:
            query = "SELECT * FROM executions WHERE 1=1"
            params = []
            
            if job_id:
                query += " AND job_id = ?"
                params.append(job_id)
            
            if status:
                query += " AND status = ?"
                params.append(status.value)
            
            query += " ORDER BY started_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            
            executions = []
            for row in rows:
                started_at = datetime.fromisoformat(row[4]) if row[4] else None
                completed_at = datetime.fromisoformat(row[5]) if row[5] else None
                
                execution = Execution(
                    id=row[0],
                    job_id=row[1],
                    status=ExecutionStatus(row[2]),
                    attempt=row[3],
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_seconds=row[6],
                    result=json.loads(row[7]) if row[7] else None,
                    error_message=row[8],
                    traceback=row[9]
                )
                executions.append(execution)
            
            return executions
        finally:
            cursor.close()
            conn.close()
    
    # ========================================================================
    # CRUD pour les Schedules
    # ========================================================================
    
    def create_schedule(
        self,
        job_id: int,
        cron_expression: Optional[str] = None,
        run_at: Optional[datetime] = None,
        enabled: bool = True
    ) -> int:
        """Crée un schedule pour un job.
        
        Args:
            job_id: ID du job à planifier
            cron_expression: Expression cron (ex: "*/5 * * * *")
            run_at: Date/heure d'exécution unique
            enabled: Si le schedule est actif (défaut: True)
        
        Returns:
            L'ID du schedule créé
        
        Raises:
            ValueError: Si ni cron ni run_at n'est fourni
        """
        if not cron_expression and not run_at:
            raise ValueError("Either cron_expression or run_at must be provided")
        
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO schedules (job_id, cron_expression, run_at, enabled)
                VALUES (?, ?, ?, ?)
            """, (
                job_id,
                cron_expression,
                run_at.isoformat() if run_at else None,
                1 if enabled else 0
            ))
            
            schedule_id = cursor.lastrowid
            conn.commit()
            return schedule_id
        finally:
            cursor.close()
            conn.close()
    
    def list_schedules(self, job_id: Optional[int] = None, enabled: Optional[bool] = None) -> List[dict]:
        """Liste les schedules avec filtres optionnels.
        
        Args:
            job_id: Filtrer par job_id
            enabled: Filtrer par état (True/False)
        
        Returns:
            Liste des schedules
        """
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        
        try:
            query = "SELECT id, job_id, cron_expression, run_at, enabled FROM schedules WHERE 1=1"
            params = []
            
            if job_id:
                query += " AND job_id = ?"
                params.append(job_id)
            
            if enabled is not None:
                query += " AND enabled = ?"
                params.append(1 if enabled else 0)
            
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            
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
    
    def delete_schedule(self, schedule_id: int) -> bool:
        """Supprime un schedule.
        
        Args:
            schedule_id: ID du schedule
        
        Returns:
            True si supprimé, False si non trouvé
        """
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM schedules WHERE id = ?", (schedule_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            cursor.close()
            conn.close()
    
    def find_idempotent_execution(self, idempotency_key: str) -> Optional[Execution]:
        """Recherche une exécution réussie par clé d'idempotence.
        
        Args:
            idempotency_key: La clé d'idempotence
        
        Returns:
            L'exécution réussie ou None
        
        Note:
            Recherche dans les jobs ayant cette idempotency_key
        """
        if not idempotency_key:
            return None
        
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Chercher un job avec cette clé
            cursor.execute("SELECT id FROM jobs WHERE idempotency_key = ?", (idempotency_key,))
            job_row = cursor.fetchone()
            
            if not job_row:
                return None
            
            job_id = job_row[0]
            
            # Chercher une exécution réussie pour ce job
            cursor.execute(
                "SELECT * FROM executions WHERE job_id = ? AND status = ? ORDER BY completed_at DESC LIMIT 1",
                (job_id, ExecutionStatus.SUCCESS.value)
            )
            exec_row = cursor.fetchone()
            
            if not exec_row:
                return None
            
            # Reconstruire l'execution
            started_at = datetime.fromisoformat(exec_row[4]) if exec_row[4] else None
            completed_at = datetime.fromisoformat(exec_row[5]) if exec_row[5] else None
            
            execution = Execution(
                id=exec_row[0],
                job_id=exec_row[1],
                status=ExecutionStatus(exec_row[2]),
                attempt=exec_row[3],
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=exec_row[6],
                result=json.loads(exec_row[7]) if exec_row[7] else None,
                error_message=exec_row[8],
                traceback=exec_row[9]
            )
            
            return execution
        finally:
            cursor.close()
            conn.close()

