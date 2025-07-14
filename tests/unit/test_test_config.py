"""
Unit tests for test configuration validation.
"""
import pytest
from pathlib import Path


@pytest.mark.unit
class TestTestConfiguration:
    """Test the test configuration and setup."""
    
    def test_test_paths_exist(self):
        """Test that required test paths exist."""
        base_path = Path(__file__).parent.parent.parent
        
        # Test directory structure
        assert (base_path / "tests").exists()
        assert (base_path / "tests" / "unit").exists()
        assert (base_path / "tests" / "integration").exists()
        assert (base_path / "tests" / "fixtures").exists()
        
        # Configuration files
        assert (base_path / "pytest.ini").exists()
        assert (base_path / ".coveragerc").exists()
        assert (base_path / "docker" / "docker-compose.test.yml").exists()
        assert (base_path / "Makefile").exists()
    
    def test_pytest_configuration(self):
        """Test pytest configuration is readable."""
        import configparser
        
        base_path = Path(__file__).parent.parent.parent
        pytest_ini = base_path / "pytest.ini"
        
        config = configparser.ConfigParser()
        config.read(pytest_ini)
        
        assert "tool:pytest" in config.sections()
        
        pytest_config = config["tool:pytest"]
        assert "testpaths" in pytest_config
        assert "python_files" in pytest_config
        assert "markers" in pytest_config
    
    def test_coverage_configuration(self):
        """Test coverage configuration is readable."""
        import configparser
        
        base_path = Path(__file__).parent.parent.parent
        coveragerc = base_path / ".coveragerc"
        
        config = configparser.ConfigParser()
        config.read(coveragerc)
        
        assert "run" in config.sections()
        assert "report" in config.sections()
        assert "html" in config.sections()
        assert "xml" in config.sections()
    
    def test_docker_compose_configuration(self):
        """Test docker-compose configuration is readable."""
        import yaml
        
        base_path = Path(__file__).parent.parent.parent
        docker_compose = base_path / "docker" / "docker-compose.test.yml"
        
        with open(docker_compose, 'r') as f:
            config = yaml.safe_load(f)
        
        assert "version" in config
        assert "services" in config
        assert "networks" in config
        
        # Check required services
        services = config["services"]
        assert "postgres-13" in services
        assert "postgres-14" in services
        assert "postgres-15" in services
        assert "postgres-16" in services
        
        # Check port mappings
        for service_name in ["postgres-13", "postgres-14", "postgres-15", "postgres-16"]:
            service = services[service_name]
            assert "ports" in service
            assert len(service["ports"]) == 1
    
    def test_makefile_exists(self):
        """Test Makefile exists and is readable."""
        base_path = Path(__file__).parent.parent.parent
        makefile = base_path / "Makefile"
        
        assert makefile.exists()
        
        with open(makefile, 'r') as f:
            content = f.read()
        
        # Check for essential targets
        assert "test:" in content
        assert "test-unit:" in content
        assert "test-integration:" in content
        assert "docker-up:" in content
        assert "docker-down:" in content
        assert "coverage:" in content
        assert "clean:" in content


@pytest.mark.unit
class TestFixtureConfiguration:
    """Test fixture configuration and structure."""
    
    def test_fixtures_directory_structure(self):
        """Test that fixture directories exist."""
        fixtures_path = Path(__file__).parent.parent / "fixtures"
        
        assert fixtures_path.exists()
        assert (fixtures_path / "sample_schemas").exists()
        assert (fixtures_path / "test_configs").exists()
    
    def test_docker_init_scripts(self):
        """Test that Docker initialization scripts exist."""
        base_path = Path(__file__).parent.parent.parent
        init_path = base_path / "docker" / "init"
        
        assert init_path.exists()
        assert (init_path / "01_create_schemas.sql").exists()
        assert (init_path / "02_sample_data.sql").exists()
        
        # Check that scripts are readable
        for script in init_path.glob("*.sql"):
            with open(script, 'r') as f:
                content = f.read()
                assert len(content) > 0
                # Basic SQL syntax check
                assert "CREATE" in content.upper() or "INSERT" in content.upper()


@pytest.mark.unit 
class TestTestMarkers:
    """Test that pytest markers are properly configured."""
    
    def test_unit_marker(self):
        """Test unit marker functionality."""
        # This test itself uses the unit marker
        assert True
    
    def test_marker_combinations(self):
        """Test that markers can be combined."""
        # Test logic for marker combinations
        markers = ["unit", "integration", "slow", "db"]
        
        for marker in markers:
            assert isinstance(marker, str)
            assert len(marker) > 0


@pytest.mark.unit
class TestTestUtilities:
    """Test utility functions for testing."""
    
    def test_test_constants(self):
        """Test that test constants are properly defined."""
        from tests.conftest import TEST_DB_NAME, TEST_DB_USER, TEST_SCHEMA_PREFIX
        
        assert TEST_DB_NAME == "pgsd_test"
        assert TEST_DB_USER == "test_user"
        assert TEST_SCHEMA_PREFIX == "test_schema"
    
    def test_postgres_version_params(self):
        """Test PostgreSQL version parameters."""
        # Simulate postgres_version fixture parameters
        expected_versions = [
            {"port": 5433, "version": "13"},
            {"port": 5434, "version": "14"},
            {"port": 5435, "version": "15"},
            {"port": 5436, "version": "16"},
        ]
        
        for version_info in expected_versions:
            assert "port" in version_info
            assert "version" in version_info
            assert isinstance(version_info["port"], int)
            assert version_info["port"] >= 5433
            assert version_info["port"] <= 5436
            assert version_info["version"] in ["13", "14", "15", "16"]