# プロジェクト基盤構築手順書

## 📋 概要
PostgreSQL Schema Diff Tool (PGSD) のプロジェクト基盤を構築する手順書

## 🎯 前提条件
- Python 3.9以上がインストール済み
- Git がインストール済み
- プロジェクトルートディレクトリに移動済み (`/home/masaaki/projects/pgsd`)

## 📁 Step 1: ディレクトリ構造作成

### 1.1 基本ディレクトリ作成
```bash
# ソースコードディレクトリ
mkdir -p src/pgsd/{config,core,database,reports,utils}

# テストディレクトリ
mkdir -p tests/{unit,integration,fixtures}
mkdir -p tests/unit/{test_config,test_core,test_database,test_reports,test_utils}
mkdir -p tests/integration/test_end_to_end
mkdir -p tests/fixtures/{sample_schemas,test_configs}

# 設定ディレクトリ
mkdir -p config

# ドキュメントディレクトリ
mkdir -p docs

# GitHub Actions
mkdir -p .github/workflows
```

### 1.2 __init__.pyファイル作成
```bash
# パッケージ初期化ファイル
touch src/pgsd/__init__.py
touch src/pgsd/config/__init__.py
touch src/pgsd/core/__init__.py
touch src/pgsd/database/__init__.py
touch src/pgsd/reports/__init__.py
touch src/pgsd/utils/__init__.py

# テスト初期化ファイル
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py
```

## 🐍 Step 2: Python設定ファイル作成

### 2.1 setup.py作成
```python
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
```

### 2.2 pyproject.toml作成
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "pgsd"
version = "0.1.0"
description = "PostgreSQL Schema Diff Tool"
readme = "README.md"
requires-python = ">=3.9"
license = {text = "MIT"}
authors = [
    {name = "PostgreSQL Schema Diff Team"},
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]

[project.scripts]
pgsd = "pgsd.main:main"

[tool.black]
line-length = 88
target-version = ['py39']

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "--cov=src/pgsd --cov-report=html --cov-report=term-missing --cov-fail-under=80"
```

### 2.3 setup.cfg作成
```ini
[metadata]
name = pgsd
version = 0.1.0

[options]
packages = find:
package_dir =
    = src
python_requires = >=3.9

[options.packages.find]
where = src

[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .git,__pycache__,build,dist,.eggs
```

## 📦 Step 3: 依存関係ファイル作成

### 3.1 requirements.txt作成
```
psycopg2-binary>=2.9.0
click>=8.0.0
pyyaml>=6.0
jinja2>=3.0.0
structlog>=22.0.0
```

### 3.2 requirements-dev.txt作成
```
-r requirements.txt
pytest>=7.0.0
pytest-cov>=4.0.0
black>=22.0.0
flake8>=5.0.0
mypy>=0.991
pre-commit>=2.20.0
```

## 🔧 Step 4: 開発ツール設定

### 4.1 .gitignore作成
```
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/
cover/

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Project specific
config/pgsd.yaml
logs/
reports/
*.log
```

### 4.2 .pre-commit-config.yaml作成
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 22.10.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v0.991
    hooks:
      - id: mypy
        additional_dependencies: [types-PyYAML]
```

## 🚀 Step 5: 基本ソースコード作成

### 5.1 パッケージ初期化
```python
# src/pgsd/__init__.py
"""PostgreSQL Schema Diff Tool."""

__version__ = "0.1.0"
__author__ = "PostgreSQL Schema Diff Team"
```

### 5.2 メインエントリーポイント
```python
# src/pgsd/main.py
"""Main entry point for PGSD."""

import sys
from typing import Optional

def main(args: Optional[list] = None) -> int:
    """Main entry point."""
    if args is None:
        args = sys.argv[1:]
    
    print("PostgreSQL Schema Diff Tool v0.1.0")
    print("Not implemented yet.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### 5.3 基本テスト
```python
# tests/test_basic.py
"""Basic test to verify package is importable."""

import pgsd


def test_package_import():
    """Test that package can be imported."""
    assert pgsd.__version__ == "0.1.0"


def test_main_entry_point():
    """Test main entry point."""
    from pgsd.main import main
    result = main([])
    assert result == 0
```

## 📋 Step 6: 設定ファイル例作成

### 6.1 pgsd.yaml.example作成
```yaml
# config/pgsd.yaml.example
# PostgreSQL Schema Diff Tool Configuration

# Database connections
source:
  host: "localhost"
  port: 5432
  database: "source_db"
  schema: "public"
  user: "user"
  password: "password"

target:
  host: "localhost"
  port: 5432
  database: "target_db"
  schema: "public"
  user: "user"
  password: "password"

# Output settings
output:
  format: "html"  # html, markdown, json, xml
  path: "reports/"
  timezone: "UTC"

# Logging settings
logging:
  level: "INFO"
  format: "json"
  file: "logs/pgsd.log"
```

### 6.2 logging.yaml作成
```yaml
# config/logging.yaml
version: 1
disable_existing_loggers: false

formatters:
  json:
    format: '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "module": "%(name)s", "message": "%(message)s"}'
  simple:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: simple
    stream: ext://sys.stdout

  file:
    class: logging.handlers.RotatingFileHandler
    level: DEBUG
    formatter: json
    filename: logs/pgsd.log
    maxBytes: 10485760
    backupCount: 5

loggers:
  pgsd:
    level: DEBUG
    handlers: [console, file]
    propagate: false

root:
  level: INFO
  handlers: [console]
```

## 🧪 Step 7: 検証手順

### 7.1 パッケージインストール検証
```bash
# 開発モードでインストール
pip install -e .

# インポート確認
python -c "import pgsd; print(pgsd.__version__)"

# エントリーポイント確認
python -m pgsd
pgsd
```

### 7.2 テスト実行検証
```bash
# テスト実行
pytest

# カバレッジ確認
pytest --cov=src/pgsd --cov-report=html
```

### 7.3 開発ツール検証
```bash
# フォーマット確認
black --check src/

# リント確認
flake8 src/

# 型チェック確認
mypy src/
```

## ✅ Step 8: 最終確認チェックリスト

- [ ] すべてのディレクトリが作成されている
- [ ] __init__.pyファイルが適切に配置されている
- [ ] setup.py/pyproject.tomlが正しく設定されている
- [ ] requirements.txtに依存関係が記載されている
- [ ] .gitignoreが適切に設定されている
- [ ] パッケージがインポート可能
- [ ] エントリーポイントが動作する
- [ ] テストが実行できる
- [ ] 開発ツールが動作する

## 🚨 トラブルシューティング

### よくある問題と解決法

1. **ImportError: No module named 'pgsd'**
   - `pip install -e .` を実行してエディタブルインストール

2. **pytest: command not found**
   - `pip install -r requirements-dev.txt` で開発依存関係をインストール

3. **black/flake8 エラー**
   - `black src/` でコードフォーマット適用
   - エラー内容に従ってコード修正

4. **Permission denied エラー**
   - ディレクトリの作成権限を確認
   - 必要に応じて sudo 使用

---

**作成日**: 2025-07-12  
**関連チケット**: PGSD-009  
**更新履歴**: 初版作成