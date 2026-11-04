"""Define shared validation exceptions for independent Enigma components."""

from typing import Iterable, Optional

from .enigma import EnigmaError


class ValidationError(EnigmaError):
    """Represent a validation failure with structured component details."""

    component: Optional[str] = None

    def __init__(
        self,
        message: Optional[str] = None,
        errors: Optional[Iterable] = None,
        component: Optional[str] = None,
    ) -> None:
        """Initialize a validation error with optional detailed failures.

        Args:
            message: Summary of the validation failure.
            errors: Detailed validation failures to include.
            component: Machine-readable component name.
        """
        self.errors = list(errors or [])
        self.component = component or self.component
        if self.errors:
            message = message or "Validation failed"
            message = f"{message}:\n" + "\n".join(f"- {error}" for error in self.errors)
        super().__init__(message or "Validation failed")


class ComponentValidationError(ValidationError):
    """Represent validation failure in an independent component."""
