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
    """
    field: str
    message: str
    extra_info: Optional[Any] = None
