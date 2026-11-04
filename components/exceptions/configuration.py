"""Define configuration loading and validation exceptions."""

from .enigma import EnigmaError
from .validation import ComponentValidationError


class ConfigurationError(EnigmaError):
    """Raised when there are issues loading or parsing configuration files or dictionaries."""
    pass

class ConfigurationLoadError(ConfigurationError):
    """Raised when configuration data cannot be loaded into a machine."""
    pass

class ConfigurationValidationError(ComponentValidationError):
    """Represent an invalid complete machine configuration."""

    component = "configuration"
