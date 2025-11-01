"""Module de métriques Prometheus.

Ce module définit et expose les métriques pour le monitoring
via Prometheus.
"""

from prometheus_client import Counter, Gauge, Histogram, start_http_server


class OrchestratorMetrics:
    """Métriques Prometheus pour l'orchestrateur.
    
    Cette classe encapsule toutes les métriques Prometheus utilisées
    pour monitorer l'orchestrateur :
    - Compteurs pour le nombre de jobs
    - Histogrammes pour la durée d'exécution
    - Gauges pour l'état actuel (queue, running)
    
    Attributes:
        jobs_total: Counter - Nombre total de jobs par status
        jobs_duration: Histogram - Durée d'exécution des jobs
        jobs_in_queue: Gauge - Nombre de jobs en attente
        jobs_running: Gauge - Nombre de jobs en cours d'exécution
        executor_pool_size: Gauge - Taille des pools par executor
    
    Example:
        >>> metrics = OrchestratorMetrics()
        >>> metrics.record_job_execution("SUCCESS", 1.5, "ASYNC")
        >>> metrics.set_jobs_in_queue(10)
    """
    
    def __init__(self):
        """Initialise les métriques Prometheus."""
        # Counter : nombre de jobs par status
        self.jobs_total = Counter(
            'orchestrator_jobs_total',
            'Total number of jobs executed',
            ['status', 'job_type']
        )
        
        # Histogram : durée d'exécution
        self.jobs_duration = Histogram(
            'orchestrator_jobs_duration_seconds',
            'Duration of job execution in seconds',
            ['job_type']
        )
        
        # Gauge : jobs en queue
        self.jobs_in_queue = Gauge(
            'orchestrator_jobs_in_queue',
            'Number of jobs currently in queue'
        )
        
        # Gauge : jobs en cours
        self.jobs_running = Gauge(
            'orchestrator_jobs_running',
            'Number of jobs currently running'
        )
        
        # Gauge : taille des pools par executor
        self.executor_pool_size = Gauge(
            'orchestrator_executor_pool_size',
            'Size of executor pools',
            ['executor_type']
        )
        
        # Gauge : jobs running par executor
        self.executor_jobs_running = Gauge(
            'orchestrator_executor_jobs_running',
            'Number of jobs running per executor',
            ['executor_type']
        )
    
    def record_job_execution(
        self,
        status: str,
        duration_seconds: float,
        job_type: str
    ) -> None:
        """Enregistre l'exécution d'un job.
        
        Args:
            status: Le statut (SUCCESS, FAILED, TIMEOUT)
            duration_seconds: Durée en secondes
            job_type: Type de job (SYNC, ASYNC, THREAD, PROCESS)
        """
        # Incrémenter le counter
        self.jobs_total.labels(status=status, job_type=job_type).inc()
        
        # Enregistrer la durée
        if duration_seconds:
            self.jobs_duration.labels(job_type=job_type).observe(duration_seconds)
    
    def set_jobs_in_queue(self, count: int) -> None:
        """Met à jour le nombre de jobs en queue.
        
        Args:
            count: Nombre de jobs en queue
        """
        self.jobs_in_queue.set(count)
    
    def set_jobs_running(self, count: int) -> None:
        """Met à jour le nombre de jobs en cours.
        
        Args:
            count: Nombre de jobs en cours
        """
        self.jobs_running.set(count)
    
    def set_executor_pool_size(self, executor_type: str, size: int) -> None:
        """Met à jour la taille d'un pool d'executor.
        
        Args:
            executor_type: Type d'executor
            size: Taille du pool
        """
        self.executor_pool_size.labels(executor_type=executor_type).set(size)
    
    def set_executor_jobs_running(self, executor_type: str, count: int) -> None:
        """Met à jour le nombre de jobs en cours pour un executor.
        
        Args:
            executor_type: Type d'executor
            count: Nombre de jobs en cours
        """
        self.executor_jobs_running.labels(executor_type=executor_type).set(count)
    
    @staticmethod
    def start_metrics_server(port: int = 9090) -> None:
        """Démarre le serveur HTTP pour exposer les métriques.
        
        Args:
            port: Port pour le serveur HTTP (défaut: 9090)
        
        Example:
            >>> OrchestratorMetrics.start_metrics_server(9090)
            >>> # Métriques disponibles sur http://localhost:9090/metrics
        """
        start_http_server(port)
        print(f"Metrics server started on port {port}")
        print(f"Access metrics at http://localhost:{port}/metrics")

