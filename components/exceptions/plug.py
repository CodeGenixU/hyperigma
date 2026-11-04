"""Define plugboard-related Enigma exceptions."""

from .validation import ComponentValidationError


class PlugValidationError(ComponentValidationError):
    """Represent an invalid plug cycle."""

    component = "plug"


class PlugboardValidationError(ComponentValidationError):
    """Represent an invalid plugboard."""

    component = "plugboard"
