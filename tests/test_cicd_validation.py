"""CI/CD validation tests."""

import pytest
import sys
from pathlib import Path


def test_python_version():
    """Test that Python version is supported."""
    assert sys.version_info >= (3, 8), "Python 3.8+ required"


def test_project_structure():
    """Test that basic project structure exists."""
    root = Path(__file__).parent.parent

    # Check src structure
    assert (root / "src" / "pgsd").exists()
    assert (root / "src" / "pgsd" / "__init__.py").exists()

    # Check test structure
    assert (root / "tests").exists()

    # Check CI/CD files
    assert (root / ".github" / "workflows" / "ci.yml").exists()
    assert (root / ".github" / "workflows" / "cd.yml").exists()


def test_configuration_files():
    """Test that configuration files exist."""
    root = Path(__file__).parent.parent

    config_files = [
        "pyproject.toml",
        ".flake8",
        "requirements-dev.txt",
        ".pre-commit-config.yaml",
    ]

    for config_file in config_files:
        assert (root / config_file).exists(), f"{config_file} should exist"


def test_imports():
    """Test that basic imports work."""
    # Test logging utilities import
    from pgsd.utils.log_config import get_default_config
    from pgsd.utils.logger import get_logger
    from pgsd.utils.performance import PerformanceTracker

    # Basic functionality test
    config = get_default_config()
    assert config.level == "INFO"

    logger = get_logger("test")
    assert logger.name == "test"

    tracker = PerformanceTracker()
    assert len(tracker._metrics) == 0


@pytest.mark.parametrize(
    "module_name",
    [
        "pgsd",
        "pgsd.utils",
        "pgsd.utils.log_config",
        "pgsd.utils.logger",
        "pgsd.utils.performance",
    ],
)
def test_module_imports(module_name):
    """Test that all main modules can be imported."""
    import importlib

    try:
        module = importlib.import_module(module_name)
        assert module is not None
    except ImportError as e:
        pytest.fail(f"Failed to import {module_name}: {e}")


def test_coverage_requirement():
    """Test that coverage tools are available."""
    try:
        import pytest_cov

        assert pytest_cov is not None
    except ImportError:
        pytest.fail("pytest-cov is required for coverage reporting")


class TestCI:
    """CI/CD specific tests."""

    def test_github_actions_files(self):
        """Test GitHub Actions workflow files exist."""
        root = Path(__file__).parent.parent
        workflows_dir = root / ".github" / "workflows"

        required_workflows = ["ci.yml", "cd.yml", "security.yml"]

        for workflow in required_workflows:
            workflow_file = workflows_dir / workflow
            assert workflow_file.exists(), f"Workflow {workflow} should exist"

            # Basic YAML validation
            import yaml

            with open(workflow_file) as f:
                try:
                    yaml.safe_load(f)
                except yaml.YAMLError as e:
                    pytest.fail(f"Invalid YAML in {workflow}: {e}")

    def test_dependabot_config(self):
        """Test Dependabot configuration."""
        root = Path(__file__).parent.parent
        dependabot_file = root / ".github" / "dependabot.yml"

        assert dependabot_file.exists()

        import yaml

        with open(dependabot_file) as f:
            config = yaml.safe_load(f)

        assert "version" in config
        assert "updates" in config
        assert len(config["updates"]) >= 2  # pip and github-actions

    def test_issue_templates(self):
        """Test issue templates exist."""
        root = Path(__file__).parent.parent
        templates_dir = root / ".github" / "ISSUE_TEMPLATE"

        assert templates_dir.exists()
        assert (templates_dir / "bug_report.yml").exists()
        assert (templates_dir / "feature_request.yml").exists()


class TestCodeQuality:
    """Code quality validation tests."""

    def test_flake8_config(self):
        """Test flake8 configuration."""
        root = Path(__file__).parent.parent
        flake8_config = root / ".flake8"

        assert flake8_config.exists()

        with open(flake8_config) as f:
            content = f.read()
            assert "max-line-length" in content
            assert "exclude" in content

    def test_black_config(self):
        """Test black configuration in pyproject.toml."""
        root = Path(__file__).parent.parent
        pyproject_file = root / "pyproject.toml"

        assert pyproject_file.exists()

        try:
            if sys.version_info >= (3, 11):
                import tomllib
            else:
                import tomli as tomllib
            with open(pyproject_file, "rb") as f:
                config = tomllib.load(f)
        except ImportError:
            # Fallback for older Python versions
            import configparser

            config = configparser.ConfigParser()
            config.read(pyproject_file)
            # Basic existence check
            return

        assert "tool" in config
        assert "black" in config["tool"]
        assert config["tool"]["black"]["line-length"] == 88

    def test_mypy_config(self):
        """Test mypy configuration."""
        root = Path(__file__).parent.parent
        pyproject_file = root / "pyproject.toml"

        with open(pyproject_file) as f:
            content = f.read()
            assert "[tool.mypy]" in content
            assert "disallow_untyped_defs" in content


if __name__ == "__main__":
    pytest.main([__file__])
