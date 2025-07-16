from setuptools import setup, find_packages

# Fallback setup.py for compatibility with older build systems
# Primary configuration is in pyproject.toml

setup(
    name="pgsd",
    version="1.0.0",
    description="PostgreSQL Schema Diff Tool - Compare PostgreSQL schemas between databases",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="PGSD Team",
    author_email="pgsd@example.com",
    url="https://github.com/omasaaki/pgsd",
    project_urls={
        "Homepage": "https://github.com/omasaaki/pgsd",
        "Documentation": "https://github.com/omasaaki/pgsd/blob/main/docs/",
        "Repository": "https://github.com/omasaaki/pgsd.git",
        "Issues": "https://github.com/omasaaki/pgsd/issues",
        "Changelog": "https://github.com/omasaaki/pgsd/blob/main/CHANGELOG.md",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "psycopg2-binary>=2.9.0",
        "click>=8.0.0",
        "pyyaml>=6.0",
        "jinja2>=3.0.0",
        "structlog>=22.0.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.0.0",
            "black>=23.0.0",
            "isort>=5.0.0",
            "mypy>=1.0.0",
            "flake8>=6.0.0",
            "bandit>=1.7.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pgsd=pgsd.main:main",
        ],
    },
    keywords=["postgresql", "schema", "diff", "database", "migration", "devops"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
)