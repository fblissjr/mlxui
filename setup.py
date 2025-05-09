import os
import re
from setuptools import setup, find_packages
from pathlib import Path

# Root directory of the project where setup.py is located
PROJECT_ROOT = Path(__file__).resolve().parent

# Path to the mlxui package
MLXUI_PACKAGE_DIR = PROJECT_ROOT / "mlxui"


def get_version():
    """
    Reads the version string from mlxui/__init__.py without importing the package.
    This is safer and avoids potential circular dependencies or side effects from importing.
    """
    version_file = MLXUI_PACKAGE_DIR / "__init__.py"
    if not version_file.exists():
        raise RuntimeError(f"Version file not found: {version_file}")

    with open(version_file, "r", encoding="utf-8") as f:
        version_match = re.search(
            r"^__version__\s*=\s*['\"]([^'\"]*)['\"]", f.read(), re.M
        )
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string in __init__.py.")


def get_long_description():
    """Reads the README.md file for the long description."""
    readme_file = PROJECT_ROOT / "README.md"
    if readme_file.exists():
        with open(readme_file, "r", encoding="utf-8") as f:
            return f.read()
    return "mlx and mlx-lm LLM and multimodal playground and experimental workbench UI for apple silicon / macos"  # Fallback


def get_requirements():
    """Reads requirements.txt for install_requires."""
    requirements_file = PROJECT_ROOT / "requirements.txt"
    if requirements_file.exists():
        with open(requirements_file, "r", encoding="utf-8") as f:
            # Filter out empty lines and comments
            return [
                line.strip()
                for line in f
                if line.strip() and not line.strip().startswith("#")
            ]
    return []

__version__ = get_version()
long_description = get_long_description()
requirements = get_requirements()

setup(
    name="mlxui",
    version=__version__,
    description="mlx and mlx-lm LLM and multimodal playground and experimental workbench UI for apple silicon / macos",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Fred Bliss",
    author_email="fred@bliss.ai",  # Optional: Add your email
    url="https://github.com/fblissjr/mlxui",
    license="Apache 2.0",
    packages=find_packages(exclude=["tests*", "scripts*", "frontend*"]),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "mlxui=mlxui.__main__:main",
        ],
    },
    python_requires=">=3.10",
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: User Interfaces",
    ],
)