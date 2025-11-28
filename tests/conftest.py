import pytest
from unittest.mock import patch
from pydantic_settings import SettingsConfigDict

from summx.config import SummXConfig


class TestSummXConfig(SummXConfig):
    """A config class for testing that does not load .env files."""
    __test__ = False  # Tell pytest this is not a test class
    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=None,  # Disable .env file loading
        extra="ignore",
    )


@pytest.fixture(autouse=True)
def isolated_config():
    """Fixture to ensure each test gets a fresh, isolated config by patching the config class."""
    with patch("summx.config.SummXConfig", TestSummXConfig):
        import summx.config
        summx.config._config_instance = None
        yield
        summx.config._config_instance = None