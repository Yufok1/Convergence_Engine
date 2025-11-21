#!/usr/bin/env python3
"""
Setup script for Djinn Kernel
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="djinn-kernel",
    version="1.0.0",
    author="Djinn Kernel Project",
    author_email="",  # Add your email if desired
    description="A sophisticated AI system implementing Kleene's Recursion Theorem for sovereign identity anchoring and mathematical completion through violation pressure dynamics",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="",  # Add your GitHub URL when available
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Distributed Computing",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
        "cli": [
            "rich>=10.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "djinn-kernel=djinn_kernel.cli:main",  # Add when CLI is implemented
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="ai, mathematical, recursion, kleene, identity, orchestration, system",
    project_urls={
        "Bug Reports": "",  # Add when GitHub is available
        "Source": "",       # Add when GitHub is available
        "Documentation": "", # Add when docs are available
    },
)
