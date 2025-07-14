# テスト環境詳細設計書

## 1. 概要

このドキュメントは、PostgreSQL Schema Diff Tool (PGSD)のテスト環境の詳細設計を定義する。

## 2. ファイル詳細設計

### 2.1 pytest.ini

```ini
[tool:pytest]
# テスト検索パス
testpaths = tests

# テストファイルパターン
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# デフォルトオプション
addopts = 
    -ra                          # 全結果のサマリ表示
    --strict-markers             # 未定義マーカーをエラーに
    --strict-config              # 設定エラーを厳密にチェック
    --cov=src/pgsd              # カバレッジ対象
    --cov-branch                 # ブランチカバレッジ有効
    --cov-report=term-missing    # ターミナルに未カバー行表示
    --cov-report=html            # HTMLレポート生成
    --cov-report=xml             # XMLレポート生成（CI用）
    --cov-fail-under=40          # 最低カバレッジ率
    -vv                          # 詳細出力

# テストマーカー定義
markers =
    unit: Unit tests (fast, no external dependencies)
    integration: Integration tests (requires database)
    slow: Slow running tests
    db: Database-related tests
    pg13: PostgreSQL 13 specific tests
    pg14: PostgreSQL 14 specific tests
    pg15: PostgreSQL 15 specific tests
    pg16: PostgreSQL 16 specific tests

# タイムアウト設定
timeout = 300
timeout_method = thread

# ログ設定
log_cli = true
log_cli_level = INFO
log_cli_format = %(asctime)s [%(levelname)8s] %(name)s - %(message)s
log_cli_date_format = %Y-%m-%d %H:%M:%S

# 警告設定
filterwarnings =
    error::UserWarning
    ignore::DeprecationWarning
```

### 2.2 conftest.py

```python
"""
Pytest configuration and shared fixtures for PGSD tests.
"""
import os
import pytest
import psycopg2
from typing import Generator, Dict, Any, Optional
from pathlib import Path
import docker
from docker.models.containers import Container
import time
from pgsd.utils.logger import get_logger

logger = get_logger(__name__)

# Test configuration
TEST_DB_NAME = "pgsd_test"
TEST_DB_USER = "test_user"
TEST_DB_PASSWORD = "test_pass"
TEST_SCHEMA_PREFIX = "test_schema"

@pytest.fixture(scope="session")
def docker_client():
    """Get Docker client."""
    try:
        client = docker.from_env()
        client.ping()
        return client
    except Exception as e:
        pytest.skip(f"Docker not available: {e}")

@pytest.fixture(scope="session")
def ensure_test_containers(docker_client):
    """Ensure test containers are running."""
    compose_file = Path(__file__).parent.parent / "docker" / "docker-compose.test.yml"
    
    # Check if containers are already running
    containers = docker_client.containers.list(filters={"label": "com.pgsd.test=true"})
    if not containers:
        logger.info("Starting test containers...")
        os.system(f"docker-compose -f {compose_file} up -d")
        time.sleep(5)  # Wait for containers to be ready
    
    yield
    
    # Cleanup handled by developer or CI

@pytest.fixture
def test_db_config(postgres_version) -> Dict[str, Any]:
    """Test database configuration for specific PostgreSQL version."""
    return {
        "host": os.getenv("TEST_DB_HOST", "localhost"),
        "port": postgres_version["port"],
        "database": TEST_DB_NAME,
        "user": TEST_DB_USER,
        "password": TEST_DB_PASSWORD,
    }

@pytest.fixture(
    params=[
        {"port": 5433, "version": "13"},
        {"port": 5434, "version": "14"},
        {"port": 5435, "version": "15"},
        {"port": 5436, "version": "16"},
    ],
    ids=["pg13", "pg14", "pg15", "pg16"]
)
def postgres_version(request) -> Dict[str, Any]:
    """Parameterized fixture for multiple PostgreSQL versions."""
    return request.param

@pytest.fixture
def db_connection(test_db_config, ensure_test_containers):
    """Create database connection for tests."""
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(**test_db_config)
            conn.autocommit = True
            yield conn
            conn.close()
            return
        except psycopg2.OperationalError as e:
            if attempt < max_retries - 1:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                time.sleep(retry_delay)
            else:
                raise

@pytest.fixture
def clean_database(db_connection):
    """Ensure clean database state for each test."""
    cursor = db_connection.cursor()
    
    # Drop all test schemas
    cursor.execute("""
        SELECT schema_name 
        FROM information_schema.schemata 
        WHERE schema_name LIKE %s
    """, (f"{TEST_SCHEMA_PREFIX}%",))
    
    schemas = cursor.fetchall()
    for schema in schemas:
        cursor.execute(f"DROP SCHEMA {schema[0]} CASCADE")
    
    yield db_connection
    
    # Cleanup after test
    cursor.execute("""
        SELECT schema_name 
        FROM information_schema.schemata 
        WHERE schema_name LIKE %s
    """, (f"{TEST_SCHEMA_PREFIX}%",))
    
    schemas = cursor.fetchall()
    for schema in schemas:
        cursor.execute(f"DROP SCHEMA {schema[0]} CASCADE")

@pytest.fixture
def test_schemas_path() -> Path:
    """Path to test schema fixtures."""
    return Path(__file__).parent / "fixtures" / "schemas"

@pytest.fixture
def sample_schema_simple(clean_database) -> str:
    """Create simple test schema."""
    cursor = clean_database.cursor()
    schema_name = f"{TEST_SCHEMA_PREFIX}_simple"
    
    cursor.execute(f"CREATE SCHEMA {schema_name}")
    cursor.execute(f"""
        CREATE TABLE {schema_name}.users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute(f"""
        CREATE TABLE {schema_name}.posts (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES {schema_name}.users(id),
            title VARCHAR(200) NOT NULL,
            content TEXT,
            published_at TIMESTAMP
        )
    """)
    
    return schema_name

@pytest.fixture
def sample_schema_complex(clean_database) -> str:
    """Create complex test schema with various PostgreSQL features."""
    cursor = clean_database.cursor()
    schema_name = f"{TEST_SCHEMA_PREFIX}_complex"
    
    # Complex schema creation SQL would go here
    # Including: views, functions, triggers, indexes, constraints
    
    return schema_name

# Test markers
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "db: mark test as requiring database"
    )

# Hooks for test reporting
def pytest_runtest_setup(item):
    """Setup for each test."""
    logger.debug(f"Starting test: {item.name}")

def pytest_runtest_teardown(item):
    """Teardown for each test."""
    logger.debug(f"Finished test: {item.name}")
```

### 2.3 docker-compose.test.yml 詳細

```yaml
version: '3.8'

x-postgres-common: &postgres-common
  image: postgres:${PG_VERSION}-alpine
  environment:
    POSTGRES_DB: pgsd_test
    POSTGRES_USER: test_user
    POSTGRES_PASSWORD: test_pass
    POSTGRES_INITDB_ARGS: --encoding=UTF-8 --locale=en_US.utf8
  volumes:
    - ./docker/init:/docker-entrypoint-initdb.d:ro
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U test_user -d pgsd_test"]
    interval: 5s
    timeout: 5s
    retries: 10
    start_period: 10s
  labels:
    com.pgsd.test: "true"
  networks:
    - pgsd-test

services:
  postgres-13:
    <<: *postgres-common
    image: postgres:13-alpine
    container_name: pgsd_test_pg13
    ports:
      - "5433:5432"
    environment:
      <<: *postgres-common.environment
      PG_VERSION: "13"

  postgres-14:
    <<: *postgres-common
    image: postgres:14-alpine
    container_name: pgsd_test_pg14
    ports:
      - "5434:5432"
    environment:
      <<: *postgres-common.environment
      PG_VERSION: "14"

  postgres-15:
    <<: *postgres-common
    image: postgres:15-alpine
    container_name: pgsd_test_pg15
    ports:
      - "5435:5432"
    environment:
      <<: *postgres-common.environment
      PG_VERSION: "15"

  postgres-16:
    <<: *postgres-common
    image: postgres:16-alpine
    container_name: pgsd_test_pg16
    ports:
      - "5436:5432"
    environment:
      <<: *postgres-common.environment
      PG_VERSION: "16"

networks:
  pgsd-test:
    name: pgsd_test_network
    driver: bridge

volumes:
  pg13_data:
  pg14_data:
  pg15_data:
  pg16_data:
```

### 2.4 Makefile

```makefile
# Makefile for PGSD test automation

.PHONY: help test test-unit test-integration test-db test-all coverage clean docker-up docker-down

# Default target
help:
	@echo "PostgreSQL Schema Diff Tool - Test Commands"
	@echo "==========================================="
	@echo "make test           - Run all tests"
	@echo "make test-unit      - Run unit tests only"
	@echo "make test-integration - Run integration tests"
	@echo "make test-pg13      - Run tests against PostgreSQL 13"
	@echo "make test-pg14      - Run tests against PostgreSQL 14"
	@echo "make test-pg15      - Run tests against PostgreSQL 15"
	@echo "make test-pg16      - Run tests against PostgreSQL 16"
	@echo "make test-all       - Run tests against all PostgreSQL versions"
	@echo "make coverage       - Generate coverage report"
	@echo "make docker-up      - Start test containers"
	@echo "make docker-down    - Stop test containers"
	@echo "make clean          - Clean test artifacts"

# Test environment setup
docker-up:
	@echo "Starting test containers..."
	@docker-compose -f docker/docker-compose.test.yml up -d
	@echo "Waiting for containers to be ready..."
	@sleep 10
	@docker-compose -f docker/docker-compose.test.yml ps

docker-down:
	@echo "Stopping test containers..."
	@docker-compose -f docker/docker-compose.test.yml down -v

# Test execution
test: docker-up
	@echo "Running all tests..."
	@pytest

test-unit:
	@echo "Running unit tests..."
	@pytest -m unit --cov-fail-under=0

test-integration: docker-up
	@echo "Running integration tests..."
	@pytest -m integration

test-db: docker-up
	@echo "Running database tests..."
	@pytest -m db

# PostgreSQL version specific tests
test-pg13: docker-up
	@echo "Running tests against PostgreSQL 13..."
	@pytest -k pg13

test-pg14: docker-up
	@echo "Running tests against PostgreSQL 14..."
	@pytest -k pg14

test-pg15: docker-up
	@echo "Running tests against PostgreSQL 15..."
	@pytest -k pg15

test-pg16: docker-up
	@echo "Running tests against PostgreSQL 16..."
	@pytest -k pg16

test-all: docker-up
	@echo "Running tests against all PostgreSQL versions..."
	@pytest

# Coverage
coverage: test
	@echo "Generating coverage report..."
	@echo "HTML report: htmlcov/index.html"
	@python -m http.server 8000 --directory htmlcov

# Cleanup
clean:
	@echo "Cleaning test artifacts..."
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@find . -type d -name "htmlcov" -exec rm -rf {} +
	@find . -type f -name ".coverage" -delete
	@find . -type f -name "coverage.xml" -delete
	@find . -type f -name "*.pyc" -delete

# Development helpers
test-watch:
	@echo "Running tests in watch mode..."
	@ptw -- --testmon

test-failed:
	@echo "Running previously failed tests..."
	@pytest --lf

test-debug:
	@echo "Running tests with debugger..."
	@pytest --pdb

# Performance testing
test-profile:
	@echo "Running tests with profiling..."
	@pytest --profile

test-benchmark:
	@echo "Running benchmark tests..."
	@pytest -m benchmark --benchmark-only
```

### 2.5 サンプルテストケース設計

#### 2.5.1 単体テスト例 (test_logger.py)

```python
"""Unit tests for logger module."""
import pytest
from pgsd.utils.logger import get_logger, LogConfig
from pgsd.utils.log_config import get_default_config

@pytest.mark.unit
class TestLogger:
    """Test logger functionality."""
    
    def test_get_logger_returns_logger_instance(self):
        """Test that get_logger returns a logger instance."""
        logger = get_logger("test_module")
        assert logger is not None
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")
    
    def test_logger_singleton_pattern(self):
        """Test that same logger instance is returned for same name."""
        logger1 = get_logger("test_module")
        logger2 = get_logger("test_module")
        assert logger1 is logger2
    
    def test_different_loggers_for_different_names(self):
        """Test that different instances are returned for different names."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")
        assert logger1 is not logger2
```

#### 2.5.2 統合テスト例 (test_database_connection.py)

```python
"""Integration tests for database connectivity."""
import pytest
import psycopg2

@pytest.mark.integration
@pytest.mark.db
class TestDatabaseConnection:
    """Test database connection functionality."""
    
    def test_connect_to_postgres(self, test_db_config):
        """Test basic connection to PostgreSQL."""
        conn = psycopg2.connect(**test_db_config)
        assert conn is not None
        
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        
        expected_version = test_db_config.get("version", "")
        if expected_version:
            assert expected_version in version
        
        conn.close()
    
    def test_create_schema(self, clean_database):
        """Test schema creation."""
        cursor = clean_database.cursor()
        schema_name = "test_schema_creation"
        
        cursor.execute(f"CREATE SCHEMA {schema_name}")
        
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name = %s
        """, (schema_name,))
        
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == schema_name
        
        # Cleanup
        cursor.execute(f"DROP SCHEMA {schema_name}")
```

### 2.6 CI/CD統合設計

#### GitHub Actions 統合
```yaml
# .github/workflows/ci.yml の test ジョブ
test:
  name: Test Python ${{ matrix.python-version }}
  runs-on: ${{ matrix.os }}
  strategy:
    matrix:
      os: [ubuntu-latest]
      python-version: ['3.8', '3.9', '3.10', '3.11', '3.12']
  
  services:
    postgres-13:
      image: postgres:13-alpine
      env:
        POSTGRES_DB: pgsd_test
        POSTGRES_USER: test_user
        POSTGRES_PASSWORD: test_pass
      options: >-
        --health-cmd pg_isready
        --health-interval 10s
        --health-timeout 5s
        --health-retries 5
      ports:
        - 5433:5432
```

## 3. テストデータ設計

### 3.1 基本スキーマ (simple)
- ユーザーテーブル
- 投稿テーブル
- 基本的な外部キー関係

### 3.2 複雑スキーマ (complex)
- パーティションテーブル
- マテリアライズドビュー
- カスタム型
- トリガー
- ストアドプロシージャ

### 3.3 エッジケース (edge_cases)
- 極端に長いテーブル名
- 予約語を含むカラム名
- 循環参照
- 大量のインデックス

## 4. 実装優先順位

1. **Phase 1: 基本環境** (本チケット)
   - pytest.ini
   - 基本的なconftest.py
   - docker-compose.test.yml
   - Makefile
   - サンプルテスト

2. **Phase 2: 拡張** (将来)
   - パフォーマンステスト
   - 負荷テスト
   - E2Eテスト
   - ビジュアルレグレッション

## 5. 検証項目

### 5.1 動作確認
- [ ] pytest実行可能
- [ ] Docker環境起動
- [ ] 各PostgreSQLバージョン接続
- [ ] カバレッジ測定
- [ ] CI/CD統合

### 5.2 パフォーマンス
- [ ] テスト実行時間 < 30秒
- [ ] メモリ使用量適切
- [ ] 並列実行可能

---

作成日: 2025-07-14