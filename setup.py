"""Setup script for Orchestrateur de Tâches"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    with open(requirements_path) as f:
        requirements = [
            line.strip() 
            for line in f 
            if line.strip() and not line.startswith("#")
        ]

setup(
    name="orchestrator-taches",
    version="1.0.0",
    author="Junior Developer",
    author_email="dev@example.com",
    description="Un orchestrateur de tâches async avec persistance et monitoring",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/Orchestrateur-taches",
    packages=find_packages(exclude=["tests", "examples", "docs"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "orchestrator=orchestrator.cli.main:cli",
        ],
    },
    include_package_data=True,
    keywords="orchestrator scheduler async jobs tasks asyncio multiprocessing",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/Orchestrateur-taches/issues",
        "Source": "https://github.com/yourusername/Orchestrateur-taches",
        "Documentation": "https://github.com/yourusername/Orchestrateur-taches/docs",
    },
)

