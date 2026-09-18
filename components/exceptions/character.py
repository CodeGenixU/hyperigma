from .enigma import EnigmaError

class InvalidCharacterError(EnigmaError):
    """Raised when a character is not in the configured character set."""
    pass
