"""Define validation error details shared by configuration components."""

from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class InvalidValue:
    """
    Holds detailed information about an invalid value discovered during validation.
    
    Attributes:
        field (str): Name of the field or component that failed validation.
        message (str): Explanation of the validation failure.
        extra_info (Optional[Any]): Additional context or conflicting data.
        code (Optional[str]): Stable machine-readable validation category.
    """
    field: str
    message: str
    extra_info: Optional[Any] = None
    code: Optional[str] = None

    def __str__(self) -> str:
        """Format the validation error for display.

        Returns:
            A human-readable description of the invalid value.
        """
        detail = self.message
        if self.extra_info is not None:
            detail = f"{detail} ({self.extra_info})"
        if self.code:
            return f"{self.field}: [{self.code}] {detail}"
        return f"{self.field}: {detail}"
