
from .enigma import EnigmaError

class ConfigurationError(EnigmaError):
    """Raised when there are issues loading or parsing configuration files or dictionaries."""
    pass

class ValidationError(EnigmaError):
    """Raised when configuration validation fails."""
    pass