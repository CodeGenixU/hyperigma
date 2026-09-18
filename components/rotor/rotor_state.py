from typing import Optional

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
        self.rotor = rotor
        self.position = position
        self.rotation_base = rotation_base if rotation_base > 0 else rotor.size
        self.size = len(rotor)
        self.name = name or rotor.name
        self.pointer = initial_position % self.rotation_base ** self.position
        self.next: Optional['RotorState'] = None  # Link to the next RotorState in the Axle chain
        self.prev: Optional['RotorState'] = None  # Link to the previous RotorState in the Axle chain

    def rotate(self, steps: int = 1) -> None:
        """Advance rotor pointer by steps."""
        self.pointer = (self.pointer + steps) % self.rotation_base

    def fcode(self, n: int) -> int:
        """Forward encoding through the underlying rotor at current pointer."""
        return self.rotor.fcode(n, self.pointer)

    def bcode(self, n: int) -> int:
        """Backward encoding through the underlying rotor at current pointer."""
        return self.rotor.bcode(n, self.pointer)

    def __repr__(self) -> str:
        return f"RotorState(name='{self.name}', position={self.position}, pointer={self.pointer})"
