"""Define rotor-related Enigma exceptions."""

from .validation import ComponentValidationError


class RotorValidationError(ComponentValidationError):
    """Represent invalid rotor wiring."""

    component = "rotor"


class RotorStateValidationError(ComponentValidationError):
    """Represent invalid active rotor state."""

    component = "rotor_state"
