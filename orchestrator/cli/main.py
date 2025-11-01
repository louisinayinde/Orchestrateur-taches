"""CLI principale pour l'orchestrateur.

Ce module implémente les commandes CLI avec Click.
"""

import asyncio
import sys
from pathlib import Path

import click

from orchestrator import Orchestrator, configure_logger


# Configurer le logger
logger = configure_logger(name="orchestrator.cli", level="INFO", format_type="text")


@click.group()
@click.version_option(version="0.4.0")
@click.option(
    '--db', 
    default="jobs.db",
    help="Chemin vers la base de données"
)
@click.pass_context
def cli(ctx, db):
    """Orchestrateur de Tâches - CLI."""
    ctx.ensure_object(dict)
    ctx.obj['db_path'] = Path(db)


@cli.command()
@click.option('--port', default=9090, help="Port pour les métriques Prometheus")
@click.pass_context
def start(ctx, port):
    """Démarre l'orchestrateur en mode serveur."""
    from orchestrator.monitoring.metrics import OrchestratorMetrics
    
    db_path = ctx.obj['db_path']
    
    click.echo(f"Starting Orchestrator on {db_path}")
    
    # Démarrer le serveur de métriques
    OrchestratorMetrics.start_metrics_server(port=port)
    click.echo(f"Metrics server started on port {port}")
    click.echo(f"Access metrics at http://localhost:{port}/metrics")
    
    # Créer l'orchestrateur
    orch = Orchestrator(db_path=db_path)
    
    click.echo("Orchestrator started successfully!")
    click.echo("Press Ctrl+C to stop")
    
    try:
        # Maintenir le processus actif
        while True:
            asyncio.run(asyncio.sleep(1))
    except KeyboardInterrupt:
        click.echo("\nStopping Orchestrator...")
        sys.exit(0)


@cli.command()
@click.argument('function')
@click.option('--name', required=True, help="Nom du job")
@click.option('--args', help="Arguments positionnels (JSON)")
@click.option('--kwargs', help="Arguments nommés (JSON)")
@click.option('--type', 'job_type', default='sync', help="Type de job: sync, async, thread, process")
@click.option('--retries', default=3, help="Nombre de retries")
@click.option('--timeout', type=int, help="Timeout en secondes")
@click.pass_context
def run(ctx, function, name, args, kwargs, job_type, retries, timeout):
    """Exécute un job immédiatement.
    
    FUNCTION: Chemin vers la fonction (module.function)
    
    Examples:
        orchestrator run mymodule.myfunction --name test --args '[1, 2]'
    """
    from orchestrator import JobType
    
    db_path = ctx.obj['db_path']
    
    # Mapper le type de job
    job_type_map = {
        'sync': JobType.SYNC,
        'async': JobType.ASYNC,
        'thread': JobType.THREAD,
        'process': JobType.PROCESS
    }
    
    if job_type not in job_type_map:
        click.echo(f"Error: Invalid job type '{job_type}'. Use: sync, async, thread, process")
        sys.exit(1)
    
    # Importer la fonction
    try:
        func = _import_function(function)
    except Exception as e:
        click.echo(f"Error: Could not import {function}: {e}")
        sys.exit(1)
    
    # Parser les arguments
    parsed_args = _parse_json(args) if args else ()
    parsed_kwargs = _parse_json(kwargs) if kwargs else {}
    
    # Créer et exécuter le job
    orch = Orchestrator(db_path=db_path)
    
    job = orch.add_job(
        func,
        name=name,
        args=parsed_args,
        kwargs=parsed_kwargs,
        job_type=job_type_map[job_type],
        max_retries=retries,
        timeout_seconds=timeout
    )
    
    click.echo(f"Job '{name}' created (ID: {job.id})")
    click.echo("Executing job...")
    
    # Exécuter le job
    execution = asyncio.run(orch.execute_job(job))
    
    # Afficher le résultat
    if execution.status.value == 'SUCCESS':
        click.echo(click.style("✓ SUCCESS", fg="green"))
        click.echo(f"Result: {execution.result}")
    else:
        click.echo(click.style(f"✗ {execution.status.value}", fg="red"))
        if execution.error_message:
            click.echo(f"Error: {execution.error_message}")


@cli.command()
@click.argument('function')
@click.argument('cron')
@click.option('--name', required=True, help="Nom du job")
@click.option('--args', help="Arguments positionnels (JSON)")
@click.option('--kwargs', help="Arguments nommés (JSON)")
@click.option('--type', 'job_type', default='sync', help="Type de job: sync, async, thread, process")
@click.option('--retries', default=3, help="Nombre de retries")
@click.option('--timeout', type=int, help="Timeout en secondes")
@click.pass_context
def schedule(ctx, function, cron, name, args, kwargs, job_type, retries, timeout):
    """Planifie un job avec une expression cron.
    
    FUNCTION: Chemin vers la fonction (module.function)
    CRON: Expression cron (min hour day month weekday)
    
    Examples:
        orchestrator schedule mymodule.myfunction "0 * * * *" --name hourly
        orchestrator schedule mymodule.myfunction "@hourly" --name hourly
    """
    from orchestrator import JobType
    
    db_path = ctx.obj['db_path']
    
    # Mapper le type de job
    job_type_map = {
        'sync': JobType.SYNC,
        'async': JobType.ASYNC,
        'thread': JobType.THREAD,
        'process': JobType.PROCESS
    }
    
    if job_type not in job_type_map:
        click.echo(f"Error: Invalid job type '{job_type}'. Use: sync, async, thread, process")
        sys.exit(1)
    
    # Importer la fonction
    try:
        func = _import_function(function)
    except Exception as e:
        click.echo(f"Error: Could not import {function}: {e}")
        sys.exit(1)
    
    # Parser les arguments
    parsed_args = _parse_json(args) if args else ()
    parsed_kwargs = _parse_json(kwargs) if kwargs else {}
    
    # Créer le job et le planifier
    orch = Orchestrator(db_path=db_path)
    
    job = orch.add_job(
        func,
        name=name,
        args=parsed_args,
        kwargs=parsed_kwargs,
        job_type=job_type_map[job_type],
        max_retries=retries,
        timeout_seconds=timeout
    )
    
    # Planifier le job
    schedule_id = orch.schedule_job(job.id, cron)
    
    click.echo(f"Job '{name}' scheduled (Job ID: {job.id}, Schedule ID: {schedule_id})")
    click.echo(f"Cron expression: {cron}")


@cli.command()
@click.option('--status', help="Filtrer par status (SUCCESS, FAILED, RUNNING, PENDING)")
@click.option('--limit', default=20, help="Nombre maximum de résultats")
@click.pass_context
def list(ctx, status, limit):
    """Liste les jobs et leurs exécutions."""
    db_path = ctx.obj['db_path']
    orch = Orchestrator(db_path=db_path)
    
    # Lister les jobs
    jobs = orch.list_jobs()
    
    if not jobs:
        click.echo("No jobs found")
        return
    
    # Filtrer par status si demandé
    if status:
        status_map = {
            'SUCCESS': 'SUCCESS',
            'FAILED': 'FAILED',
            'RUNNING': 'RUNNING',
            'PENDING': 'PENDING'
        }
        if status not in status_map:
            click.echo(f"Error: Invalid status '{status}'")
            sys.exit(1)
        
        # Filtrer les exécutions
        all_executions = orch.list_executions(limit=limit * 10)
        executions = [e for e in all_executions if e.status.value == status_map[status]]
        executions = executions[:limit]
    else:
        executions = orch.list_executions(limit=limit)
    
    # Afficher les résultats
    if executions:
        click.echo(f"\nShowing {len(executions)} execution(s)\n")
        
        for execution in executions:
            job = orch.get_job(execution.job_id)
            job_name = job.name if job else f"Job {execution.job_id}"
            
            status_color = {
                'SUCCESS': 'green',
                'FAILED': 'red',
                'TIMEOUT': 'yellow',
                'RUNNING': 'blue',
                'PENDING': 'white'
            }.get(execution.status.value, 'white')
            
            click.echo(f"Execution {execution.id}: {job_name}")
            click.echo(f"  Status: {click.style(execution.status.value, fg=status_color)}")
            if execution.result:
                click.echo(f"  Result: {execution.result}")
            if execution.error_message:
                click.echo(f"  Error: {click.style(execution.error_message, fg='red')}")
            click.echo()
    else:
        click.echo("No executions found")


@cli.command()
@click.pass_context
def status(ctx):
    """Affiche le statut de l'orchestrateur."""
    db_path = ctx.obj['db_path']
    orch = Orchestrator(db_path=db_path)
    
    # Statistiques
    jobs = orch.list_jobs()
    executions = orch.list_executions(limit=1000)
    
    # Compter par status
    status_counts = {}
    for execution in executions:
        status = execution.status.value
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # Afficher
    click.echo("\n=== Orchestrator Status ===\n")
    click.echo(f"Database: {db_path}")
    click.echo(f"Total Jobs: {len(jobs)}")
    click.echo(f"Total Executions: {len(executions)}")
    
    if status_counts:
        click.echo("\nExecutions by Status:")
        for status, count in sorted(status_counts.items()):
            click.echo(f"  {status}: {count}")
    
    # Schedules actifs
    schedules = orch.list_schedules()
    if schedules:
        click.echo(f"\nActive Schedules: {len(schedules)}")
        for schedule in schedules:
            job = orch.get_job(schedule.job_id)
            job_name = job.name if job else f"Job {schedule.job_id}"
            click.echo(f"  - {job_name}: {schedule.cron_expression}")
    
    click.echo()


def _import_function(function_path: str):
    """Importe une fonction depuis son chemin.
    
    Args:
        function_path: Chemin vers la fonction (module.function)
        
    Returns:
        La fonction importée
    """
    parts = function_path.split('.')
    if len(parts) < 2:
        raise ValueError("Function path must be in format 'module.function'")
    
    module_path = '.'.join(parts[:-1])
    function_name = parts[-1]
    
    module = __import__(module_path, fromlist=[function_name])
    return getattr(module, function_name)


def _parse_json(json_str: str):
    """Parse une chaîne JSON.
    
    Args:
        json_str: Chaîne JSON
        
    Returns:
        Objet Python parsé
    """
    import json
    return json.loads(json_str)


if __name__ == '__main__':
    cli()

