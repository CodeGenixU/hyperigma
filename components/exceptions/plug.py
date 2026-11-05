"""Define plugboard-related Enigma exceptions."""

from .validation import ComponentValidationError


class PlugValidationError(ComponentValidationError):
    """Represent an invalid plug cycle."""

    component = "plug"


class PlugRegistryValidationError(ComponentValidationError):
    """Represent an invalid plug registry."""

    component = "plugregistry"


class PlugboardValidationError(ComponentValidationError):
    """Represent an invalid finalized plugboard."""

    component = "plugboard"
