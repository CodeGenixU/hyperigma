"""Define character-related Enigma exceptions."""

from .enigma import EnigmaError
from .validation import ComponentValidationError


class CharacterSetValidationError(ComponentValidationError):
    """Represent an invalid character set."""

    component = "character_set"


class InvalidCharacterError(EnigmaError):
    """Raised when a character is not in the configured character set."""
    pass
"""Define character-related Enigma exceptions."""
