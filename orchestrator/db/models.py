"""Schéma de base de données SQLite.

Ce module contient le schéma SQL pour créer les tables de la base de données.
"""

# Schéma SQL pour créer les tables

SQL_CREATE_TABLE_JOBS = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    function_path TEXT NOT NULL,
    args_json TEXT,
    kwargs_json TEXT,
    job_type TEXT NOT NULL,
    max_retries INTEGER DEFAULT 3,
    timeout_seconds INTEGER,
    idempotency_key TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

SQL_CREATE_TABLE_EXECUTIONS = """
CREATE TABLE IF NOT EXISTS executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    attempt INTEGER DEFAULT 1,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds REAL,
    result_json TEXT,
    error_message TEXT,
    traceback TEXT,
    FOREIGN KEY (job_id) REFERENCES jobs (id)
);
"""

SQL_CREATE_TABLE_SCHEDULES = """
CREATE TABLE IF NOT EXISTS schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    cron_expression TEXT,
    run_at TIMESTAMP,
    enabled BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs (id)
);
"""

# Index pour améliorer les performances des requêtes fréquentes

SQL_CREATE_INDEX_EXECUTIONS_STATUS = """
CREATE INDEX IF NOT EXISTS idx_executions_status 
ON executions(status);
"""

SQL_CREATE_INDEX_EXECUTIONS_JOB_ID = """
CREATE INDEX IF NOT EXISTS idx_executions_job_id 
ON executions(job_id);
"""

SQL_CREATE_INDEX_EXECUTIONS_STARTED_AT = """
CREATE INDEX IF NOT EXISTS idx_executions_started_at 
ON executions(started_at);
"""

SQL_CREATE_INDEX_JOBS_IDEMPOTENCY_KEY = """
CREATE INDEX IF NOT EXISTS idx_jobs_idempotency_key 
ON jobs(idempotency_key);
"""

# Toutes les commandes SQL à exécuter pour créer la base

CREATE_DATABASE_SQL = [
    SQL_CREATE_TABLE_JOBS,
    SQL_CREATE_TABLE_EXECUTIONS,
    SQL_CREATE_TABLE_SCHEDULES,
    SQL_CREATE_INDEX_EXECUTIONS_STATUS,
    SQL_CREATE_INDEX_EXECUTIONS_JOB_ID,
    SQL_CREATE_INDEX_EXECUTIONS_STARTED_AT,
    SQL_CREATE_INDEX_JOBS_IDEMPOTENCY_KEY,
]

