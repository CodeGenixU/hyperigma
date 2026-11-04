"""Track the active position and behavior of a rotor."""

from typing import Optional

from ..exceptions import RotorStateValidationError
from ..DTO.invalid_values import InvalidValue
from .rotor import Rotor

class RotorState:
    """
    Reusable component encapsulating the active state of a Rotor inside an Enigma machine.
    Manages pointer position, stepping, and delegates index mappings to the underlying Rotor object.
    """
    def __init__(
        self,
        rotor: Rotor,
        position: int = 0,
        rotation_base: int = 0,
        initial_position: int = 0,
        name: Optional[str] = None
    ) -> None:
        """
        Initialize RotorState.
        
        Args:
            rotor (Rotor): Reusable Rotor object.
            position (int): Rotor position index (0 = rightmost/fastest rotor).
            pointer (int): Initial pointer offset (0 <= pointer < rotor.size).
            rotation_base (int): Base value for stepping calculation.
            name (Optional[str]): Optional name for this rotor state instance.
        """
        if not isinstance(rotor, Rotor):
            raise RotorStateValidationError(
                "Invalid rotor state",
                errors=[InvalidValue(
                    field="rotor",
                    code="invalid_type",
                    message="Expected a Rotor instance",
                )],
            )
        if not isinstance(position, int) or position < 0:
            raise RotorStateValidationError(
                "Invalid rotor state position",
                errors=[InvalidValue(
                    field="position",
                    code="invalid_value",
                    message="Position must be a non-negative integer",
                )],
            )
        if not isinstance(rotation_base, int) or rotation_base < 0:
            raise RotorStateValidationError(
                "Invalid rotor state rotation base",
                errors=[InvalidValue(
                    field="rotation_base",
                    code="invalid_value",
                    message="Rotation base must be a non-negative integer",
                )],
            )
        if not isinstance(initial_position, int):
            raise RotorStateValidationError(
                "Invalid rotor state initial position",
                errors=[InvalidValue(
                    field="initial_position",
                    code="invalid_type",
                    message="Initial position must be an integer",
                )],
            )
        self.rotor = rotor
        self.position = position
        self.rotation_base = rotation_base if rotation_base > 0 else rotor.size
        self.size = len(rotor)
        self.name = name or rotor.name
        self.pointer = initial_position % self.rotation_base ** self.position
        self.next: Optional['RotorState'] = None  # Link to the next RotorState in the Axle chain
        self.prev: Optional['RotorState'] = None  # Link to the previous RotorState in the Axle chain

    def rotate(self, steps: int = 1) -> None:
        """Advance the rotor pointer.

        Args:
            steps: Number of positions to advance.
        """
        self.pointer = (self.pointer + steps) % self.rotation_base

    def fcode(self, n: int) -> int:
        """Encode an index through the rotor forward.

        Args:
            n: Character index to transform.

        Returns:
            The transformed index.
        """
        return self.rotor.fcode(n, self.pointer)

    def bcode(self, n: int) -> int:
        """Encode an index through the rotor backward.

        Args:
            n: Character index to transform.

        Returns:
            The transformed index.
        """
        return self.rotor.bcode(n, self.pointer)

    def __repr__(self) -> str:
        """Represent the rotor state for debugging."""
        return f"RotorState(name='{self.name}', position={self.position}, pointer={self.pointer})"
