# 🤝 Guide de Contribution

> Guide pour développer sur le projet Orchestrateur de Tâches

---

## 🎯 Objectifs du Projet

Ce projet est avant tout **pédagogique**. Les objectifs sont :

1. **Apprendre** Python avancé (asyncio, multiprocessing, design patterns)
2. **Comprendre** la concurrence et le GIL
3. **Produire** du code production-ready (type hints, docs, patterns)
4. **Expérimenter** différentes approches techniques

---

## 🚀 Setup Initial

### 1. Environnement

```bash
# Cloner ou naviguer vers le projet
cd Orchestrateur-taches

# Créer un virtualenv
python -m venv venv

# Activer (Windows PowerShell)
venv\Scripts\Activate.ps1

# Activer (Linux/Mac)
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Vérifier l'installation
python --version  # Should be >= 3.11
mypy --version
ruff --version
```

### 2. Configuration

```bash
# Copier la config exemple
cp config.yaml.example config.yaml

# Éditer selon tes besoins (optionnel pour commencer)
```

### 3. Base de Données

```bash
# Initialiser la DB (une fois le script créé)
python -m orchestrator.db.init_db

# Vérifier que jobs.db est créé
ls jobs.db
```

---

## 📝 Workflow de Développement

### Étape 1 : Choisir une Tâche

1. Ouvrir [README.md](README.md) et aller à la section **Backlog Produit**
2. Choisir une tâche du sprint en cours (commencer par Sprint 1)
3. Lire les **critères d'acceptation** de la user story associée

Exemple : `T-002 : Modèle de données SQLite`

### Étape 2 : Créer une Branche (Optionnel)

```bash
# Créer une branche pour la tâche
git checkout -b feature/T-002-modele-donnees

# Ou continuer sur main si projet solo
```

### Étape 3 : Développer

#### A. Écrire le Code

```python
# orchestrator/db/models.py

"""
Models pour la base de données SQLite.

Ce module définit le schéma de la base de données et les
opérations CRUD de base.
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class Job:
    """
    Représente un job à exécuter.
    
    Attributes:
        id: Identifiant unique du job
        name: Nom descriptif du job
        function_path: Chemin vers la fonction (module.function)
        ...
    """
    id: Optional[int]
    name: str
    function_path: str
    # ...
```

**Règles de Code** :
- ✅ Type hints partout
- ✅ Docstrings (Google style) pour les fonctions publiques
- ✅ Noms explicites (pas de `x`, `tmp`, `data`)
- ✅ Fonctions courtes (<50 lignes idéalement)
- ✅ Classes avec responsabilité unique (SOLID)

#### B. Documenter

```python
def create_job(name: str, function: Callable, **kwargs) -> Job:
    """
    Crée un nouveau job dans la base de données.
    
    Args:
        name: Nom unique du job
        function: Fonction Python à exécuter
        **kwargs: Options additionnelles (timeout, max_retries, etc.)
    
    Returns:
        Job créé avec son ID assigné
    
    Raises:
        ValueError: Si le nom existe déjà
        TypeError: Si la fonction n'est pas callable
    
    Example:
        >>> job = create_job("hello", say_hello, args=("World",))
        >>> print(job.id)
        1
    """
    # ...
```

#### C. Gérer les Erreurs

```python
# ❌ MAUVAIS
def get_job(job_id: int):
    job = db.get(job_id)
    return job.name  # Crash si job est None !

# ✅ BON
def get_job(job_id: int) -> Optional[Job]:
    """Récupère un job par son ID."""
    job = db.get(job_id)
    if job is None:
        logger.warning(f"Job {job_id} not found")
        return None
    return job

# ✅ OU avec exception
def get_job(job_id: int) -> Job:
    """Récupère un job par son ID.
    
    Raises:
        JobNotFoundError: Si le job n'existe pas
    """
    job = db.get(job_id)
    if job is None:
        raise JobNotFoundError(f"Job {job_id} not found")
    return job
```

### Étape 4 : Vérifier la Qualité

#### A. Type Checking (mypy)

```bash
# Vérifier les types
mypy orchestrator --strict

# Corriger les erreurs de type
# Exemple d'erreur :
# error: Argument 1 to "get_job" has incompatible type "str"; expected "int"

# Fix :
job = get_job(int(job_id_str))
```

#### B. Linting (ruff)

```bash
# Vérifier le style
ruff check orchestrator

# Auto-fix ce qui peut l'être
ruff check orchestrator --fix

# Erreurs communes :
# - F401: Module imported but unused
# - E501: Line too long
# - N806: Variable in function should be lowercase
```

#### C. Formatting (black)

```bash
# Formatter le code
black orchestrator

# Vérifier sans modifier
black orchestrator --check
```

### Étape 5 : Tester Manuellement

```python
# Créer un script de test dans examples/
# examples/test_sprint1.py

from orchestrator.db.models import Job, create_job
from orchestrator.db.init_db import init_database

# Init DB
init_database()

# Test création job
job = create_job(
    name="test_job",
    function=lambda: print("Hello"),
)

print(f"Job créé : {job}")
print(f"Job ID : {job.id}")

# Test récupération
retrieved = get_job(job.id)
print(f"Job récupéré : {retrieved}")
```

```bash
# Exécuter
python examples/test_sprint1.py
```

### Étape 6 : Commit

```bash
# Voir les changements
git status
git diff

# Ajouter les fichiers
git add orchestrator/db/models.py
git add orchestrator/db/init_db.py

# Commit avec message descriptif
git commit -m "feat(T-002): ajout modèle de données SQLite

- Création des dataclasses Job, Execution, Schedule
- Schéma SQL avec tables et indexes
- Script init_db.py pour créer la base
- Docstrings complètes avec exemples"
```

**Convention de Commit** :
```
<type>(<task-id>): <description courte>

[Corps optionnel avec détails]

[Footer optionnel : Breaking changes, issues, etc.]
```

**Types** :
- `feat`: Nouvelle fonctionnalité
- `fix`: Correction de bug
- `docs`: Documentation uniquement
- `refactor`: Refactoring sans changement de comportement
- `perf`: Amélioration de performance
- `test`: Ajout/modification de tests
- `chore`: Tâches de maintenance (deps, config, etc.)

### Étape 7 : Mettre à Jour la Doc

Si tu as ajouté une feature importante :

1. Mettre à jour [README.md](README.md) si nécessaire
2. Ajouter un exemple dans `examples/`
3. Cocher la tâche comme complétée dans le backlog (optionnel)

---

## 🧪 Testing (Optionnel - Pas requis pour ce projet)

Si tu veux ajouter des tests malgré tout :

```python
# tests/test_models.py
import pytest
from orchestrator.db.models import Job, create_job

def test_create_job():
    job = create_job("test", lambda: None)
    assert job.name == "test"
    assert job.id is not None

def test_create_job_duplicate_name():
    create_job("test", lambda: None)
    with pytest.raises(ValueError):
        create_job("test", lambda: None)
```

```bash
# Installer pytest
pip install pytest pytest-asyncio

# Lancer les tests
pytest tests/

# Avec coverage
pytest --cov=orchestrator tests/
```

---

## 📚 Standards de Code

### Type Hints

```python
# ✅ BON
def process_job(job: Job, timeout: Optional[float] = None) -> ExecutionResult:
    pass

# ❌ MAUVAIS (pas de types)
def process_job(job, timeout=None):
    pass
```

### Docstrings (Google Style)

```python
def complex_function(param1: str, param2: int) -> dict:
    """
    Description courte sur une ligne.
    
    Description longue optionnelle sur plusieurs lignes
    expliquant le contexte et les détails.
    
    Args:
        param1: Description du paramètre 1
        param2: Description du paramètre 2
    
    Returns:
        Description du retour avec son type
    
    Raises:
        ValueError: Dans quel cas cette exception est levée
        TypeError: Dans quel autre cas
    
    Example:
        >>> result = complex_function("test", 42)
        >>> print(result)
        {"status": "ok"}
    """
    pass
```

### Naming Conventions

| Type | Convention | Exemple |
|------|------------|---------|
| Variable | `snake_case` | `job_queue` |
| Fonction | `snake_case` | `execute_job()` |
| Classe | `PascalCase` | `JobExecutor` |
| Constante | `UPPER_SNAKE_CASE` | `MAX_RETRIES` |
| Privé | `_leading_underscore` | `_internal_method()` |
| Module | `snake_case` | `task_queue.py` |

### Structure de Fichier

```python
"""
Module docstring expliquant le but du module.
"""

# 1. Imports standard library
import os
import sys
from typing import Optional, List

# 2. Imports third-party
import aiohttp
from pydantic import BaseModel

# 3. Imports locaux
from orchestrator.core.job import Job
from orchestrator.db.repository import JobRepository

# 4. Constantes
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 60

# 5. Classes et fonctions
class JobExecutor:
    """Class docstring."""
    pass

def execute_job(job: Job) -> None:
    """Function docstring."""
    pass
```

---

## 🐛 Debugging

### Logging

```python
import logging
import json_logging

# Setup logging (dans main ou __init__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Utilisation
logger.debug("Starting job execution")
logger.info(f"Job {job.id} started")
logger.warning(f"Job {job.id} retry attempt {attempt}")
logger.error(f"Job {job.id} failed: {error}", exc_info=True)
```

### Debug Asyncio

```python
# Activer le debug mode
import asyncio
asyncio.run(main(), debug=True)

# Détecter les coroutines non awaited
import warnings
warnings.simplefilter('always', ResourceWarning)
```

### Debug Multiprocessing

```python
# Logger dans chaque process
import multiprocessing
import logging

def worker(n):
    # Chaque process doit setup son logger
    logger = logging.getLogger(f"worker-{n}")
    logger.info(f"Worker {n} started")
    # ...

if __name__ == "__main__":
    # Utiliser 'spawn' pour plus de clarté (recommandé)
    multiprocessing.set_start_method('spawn')
```

### Outils de Profiling

```python
# Profiler du code
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Code à profiler
result = heavy_computation()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumtime')
stats.print_stats(10)  # Top 10 fonctions
```

---

## 🎨 Design Patterns Utilisés

### 1. Factory Pattern

```python
class ExecutorFactory:
    """Crée le bon type d'executor selon le job"""
    
    @staticmethod
    def create_executor(job_type: JobType) -> BaseExecutor:
        if job_type == JobType.ASYNC:
            return AsyncExecutor()
        elif job_type == JobType.THREAD:
            return ThreadExecutor()
        elif job_type == JobType.PROCESS:
            return ProcessExecutor()
        else:
            raise ValueError(f"Unknown job type: {job_type}")
```

### 2. Strategy Pattern

```python
class BaseExecutor(ABC):
    """Interface pour tous les executors"""
    
    @abstractmethod
    async def execute(self, job: Job) -> ExecutionResult:
        pass

# Différentes stratégies d'exécution
class AsyncExecutor(BaseExecutor):
    async def execute(self, job: Job) -> ExecutionResult:
        # Stratégie asyncio
        pass

class ThreadExecutor(BaseExecutor):
    async def execute(self, job: Job) -> ExecutionResult:
        # Stratégie threading
        pass
```

### 3. Observer Pattern (pour metrics)

```python
class MetricsObserver:
    """Observe les événements du système"""
    
    def on_job_started(self, job: Job):
        metrics.job_started_counter.inc()
    
    def on_job_completed(self, job: Job, duration: float):
        metrics.job_duration_histogram.observe(duration)
        metrics.job_completed_counter.labels(status="success").inc()
    
    def on_job_failed(self, job: Job, error: Exception):
        metrics.job_completed_counter.labels(status="failed").inc()

# Dans Orchestrator
orchestrator.add_observer(MetricsObserver())
```

### 4. Builder Pattern (pour config)

```python
class OrchestratorBuilder:
    """Builder pour créer un orchestrator configuré"""
    
    def __init__(self):
        self.config = OrchestratorConfig()
    
    def with_async_executor(self, max_concurrent: int) -> 'OrchestratorBuilder':
        self.config.max_async_concurrent = max_concurrent
        return self
    
    def with_database(self, url: str) -> 'OrchestratorBuilder':
        self.config.database_url = url
        return self
    
    def build(self) -> Orchestrator:
        return Orchestrator(self.config)

# Usage
orch = (OrchestratorBuilder()
        .with_async_executor(10)
        .with_database("sqlite:///jobs.db")
        .build())
```

---

## 📊 Métriques et Monitoring

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Définir les métriques
jobs_total = Counter(
    'jobs_total',
    'Total number of jobs executed',
    ['status']  # Labels: success, failed, timeout
)

jobs_duration = Histogram(
    'jobs_duration_seconds',
    'Job execution duration in seconds',
    buckets=[0.1, 0.5, 1, 5, 10, 30, 60, 300, 600]
)

jobs_in_queue = Gauge(
    'jobs_in_queue',
    'Current number of jobs in queue'
)

# Utiliser
jobs_total.labels(status='success').inc()
jobs_duration.observe(3.5)
jobs_in_queue.set(42)

# Exposer sur :9090
start_http_server(9090)
```

---

## 🎓 Apprentissage Continu

### À Chaque Sprint

1. **Avant** : Lire la doc officielle Python du concept du sprint
2. **Pendant** : Expérimenter dans un notebook ou script test
3. **Après** : Documenter ce que tu as appris

### Questions à te Poser

Pour chaque feature :
- ✅ Pourquoi ce design ?
- ✅ Quelles sont les alternatives ?
- ✅ Quels sont les trade-offs ?
- ✅ Comment cela scale ?
- ✅ Quelles sont les edge cases ?

### Ressources par Sprint

**Sprint 1-2** :
- [SQLite Tutorial](https://docs.python.org/3/library/sqlite3.html)
- [Queue Module](https://docs.python.org/3/library/queue.html)

**Sprint 3-4** :
- [asyncio Documentation](https://docs.python.org/3/library/asyncio.html)
- [Real Python - Async IO](https://realpython.com/async-io-python/)

**Sprint 5** :
- [concurrent.futures](https://docs.python.org/3/library/concurrent.futures.html)
- [multiprocessing](https://docs.python.org/3/library/multiprocessing.html)
- Notre guide : [CONCURRENCY_GUIDE.md](docs/CONCURRENCY_GUIDE.md)

---

## 🤝 Collaboration (Si Projet en Équipe)

### Pull Request

```markdown
## Description
Implémentation du modèle de données SQLite (T-002)

## Changements
- Ajout de `orchestrator/db/models.py` avec dataclasses
- Schéma SQL avec 3 tables : jobs, executions, schedules
- Script init_db.py pour créer la base

## Tests
- [x] Tests manuels avec examples/test_sprint1.py
- [x] mypy --strict passe
- [x] ruff check passe

## Checklist
- [x] Code documenté (docstrings)
- [x] Type hints présents
- [x] Exemples d'utilisation ajoutés
- [x] README à jour si nécessaire
```

### Code Review Checklist

Quand tu review du code (ou ton propre code) :

- [ ] Le code fait-il ce qu'il est censé faire ?
- [ ] Les types sont-ils corrects ?
- [ ] Y a-t-il de la duplication ?
- [ ] Les noms sont-ils explicites ?
- [ ] La complexité est-elle nécessaire ?
- [ ] Les erreurs sont-elles gérées ?
- [ ] Le code est-il thread-safe si nécessaire ?
- [ ] Les ressources sont-elles nettoyées (DB, files) ?

---

## 📖 Définition of Done (DoD)

Une tâche est **Done** quand :

### Code
- [ ] Le code implémente tous les critères d'acceptation
- [ ] Type hints présents sur toutes les fonctions publiques
- [ ] Pas de `print()` de debug (utiliser `logging`)
- [ ] Pas de code commenté ou de TODOs non résolus

### Qualité
- [ ] `mypy orchestrator --strict` passe
- [ ] `ruff check orchestrator` passe
- [ ] `black orchestrator --check` passe
- [ ] Pas de code dupliqué évident

### Documentation
- [ ] Docstrings (Google style) sur classes et fonctions publiques
- [ ] Exemple d'utilisation dans `examples/` si nouvelle feature
- [ ] README à jour si changement d'API publique
- [ ] Commentaires dans le code pour parties complexes

### Testing
- [ ] Tests manuels effectués
- [ ] Edge cases testés (None, empty, error cases)
- [ ] Tests automatiques si ajoutés (optionnel)

### Commit
- [ ] Commit avec message descriptif
- [ ] Pas de fichiers non liés dans le commit
- [ ] `.gitignore` à jour si nouveaux fichiers générés

---

## 🎯 Prochaines Étapes

1. **Lire** ce guide en entier
2. **Setup** l'environnement
3. **Commencer** par T-001 du Sprint 1
4. **Appliquer** les standards de code
5. **Itérer** et s'améliorer

---

**Bon développement ! 🚀**

N'hésite pas à expérimenter, casser des choses, et apprendre de tes erreurs.
C'est en codant qu'on devient développeur !

