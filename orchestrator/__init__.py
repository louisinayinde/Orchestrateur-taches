"""Orchestrateur de Tâches - Job Orchestrator.

Un système simple mais puissant pour orchestrer et exécuter des tâches Python
avec support de la concurrence (asyncio, threading, multiprocessing).
"""

from orchestrator.core.job import Job, JobType
from orchestrator.core.execution import Execution, ExecutionResult, ExecutionStatus
from orchestrator.core.orchestrator import Orchestrator
from orchestrator.core.config import Config

__version__ = "0.1.0"

__all__ = [
    "Orchestrator",
    "Job",
    "JobType",
    "Execution",
    "ExecutionResult",
    "ExecutionStatus",
    "Config",
]

