from typing import List, Dict, Set

from ..exceptions import ValidationError
from ..DTO.invalid_values import InvalidValue

class Plug:
    """
    Reusable component representing a single plugboard cycle.
    Swaps characters cyclically before and after rotor processing.
    """
    def __init__(self, plug_cycle: str) -> None:
        """
        Initialize the plugboard cycle with O(1) lookup tables.
        
        Args:
            plug_cycle (str): String representing the cycle (e.g., "ABCD").
            
        Raises:
            ValidationError: If cycle contains duplicate characters or is empty.
        """
        errors = list(self.test(plug_cycle))
        if errors:
            raise ValidationError(f"Invalid plug cycle '{plug_cycle}': {errors[0].message}")

        self.plug = plug_cycle
        self.elements: Set[str] = set(plug_cycle)
        n = len(plug_cycle)

        # Forward mapping: char -> next char in cycle
        self._f_map: Dict[str, str] = {plug_cycle[i]: plug_cycle[(i + 1) % n] for i in range(n)} if n > 0 else {}
        # Backward mapping: char -> previous char in cycle
        self._b_map: Dict[str, str] = {plug_cycle[i]: plug_cycle[(i - 1) % n] for i in range(n)} if n > 0 else {}

    def fplug(self, character: str) -> str:
        """Swap character using the plugboard cycle in forward direction in O(1) time."""
        return self._f_map.get(character, character)

    def bplug(self, character: str) -> str:
        """Swap character using the plugboard cycle in backward direction in O(1) time."""
        return self._b_map.get(character, character)

    def isplug(self, character: str) -> bool:
        """Check if character is part of this plugboard cycle."""
        return character in self.elements

    @staticmethod
    def test(cycle: str) -> List[InvalidValue]:
        """Validate a plugboard cycle for repeated characters or invalid structure."""

        errors = []

        if not isinstance(cycle, str):
            errors.append(InvalidValue(field="Plug", message="Plug cycle must be a string", extra_info=cycle))

        if len(cycle) == 0:
            errors.append(InvalidValue(field="Plug", message="Plug cycle cannot be empty"))

        unique_chars = set(cycle)
        if len(unique_chars) != len(cycle):
            duplicates = [char for char in unique_chars if cycle.count(char) > 1]
            errors.append(InvalidValue(field="Plug", message="Duplicate characters found in plugboard cycle", extra_info=duplicates))

        return errors

    def __repr__(self) -> str:
        return f"Plug('{self.plug_cycle}')"

    # def __eq__(self, other: object) -> bool:
    #     if isinstance(other, Plug):
    #         return self.plug_cycle == other.plug_cycle
    #     return False