import pytest

@pytest.fixture(autouse=True)
def clear_config_singleton():
    """
    Fixture to automatically reset the config singleton before each test.
    This ensures that tests do not interfere with each other's configuration.
    """
    import summx.config
    summx.config._config_instance = None
    yield
    summx.config._config_instance = None