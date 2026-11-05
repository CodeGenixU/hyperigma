"""Define rotor shaft validation exceptions."""

from .validation import ComponentValidationError


class ShaftValidationError(ComponentValidationError):
    """Represent an invalid rotor shaft."""

    component = "shaft"

class AxleValidationError(ShaftValidationError):
    """Represent an invalid rotor axle."""

    component = "axle"