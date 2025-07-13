from setuptools import setup, find_packages

setup(
    name="pgsd",
    version="0.1.0",
    description="PostgreSQL Schema Diff Tool",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="PostgreSQL Schema Diff Team",
    author_email="",
    url="https://github.com/omasaaki/pgsd",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "psycopg2-binary>=2.9.0",
        "click>=8.0.0", 
        "pyyaml>=6.0",
        "jinja2>=3.0.0",
        "structlog>=22.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.991",
            "pre-commit>=2.20.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "pgsd=pgsd.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)