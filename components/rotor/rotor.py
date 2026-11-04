"""Represent and validate immutable rotor wiring permutations."""

from typing import List, Optional, Union, Dict, Set, Tuple

from ..exceptions import RotorValidationError
from ..DTO.invalid_values import InvalidValue

class Rotor:
    """
    Reusable component representing an immutable rotor wiring specification.
    Stateless with respect to machine position/stepping.
    """
    def __init__(self, wiring: Union[List[int], Tuple[int, ...]], size: Optional[int] = None, name: Optional[str] = None) -> None:
        """
        Initialize the Rotor with wiring indices.
        
        Args:
            wiring (Union[List[int], Tuple[int, ...]]): Permutation of indices from 0 to size-1.
            size (Optional[int]): Total size of character set. Inferred from wiring length if None.
            name (Optional[str]): Optional descriptive name (e.g., 'r1').
            
        Raises:
            RotorValidationError: If wiring is not a valid permutation.
        """
        self.size = size if size is not None else len(wiring)
        self.name = name or None 

        errors = self.test(wiring, self.size)
        if errors:
            raise RotorValidationError("Invalid rotor wiring", errors=errors)

        self.rotor = tuple(wiring)

        reverse_rotor = [0] * self.size
        for i, val in enumerate(self.rotor):
            reverse_rotor[val] = i

        self.reverse_rotor = tuple(reverse_rotor)

    def fcode(self, n: int, pointer: int) -> int:
        """Encode an index through the rotor forward.

        Args:
            n: Character index to transform.
            pointer: Current rotor offset.

        Returns:
            The transformed index.
        """
        input_index = (n + pointer) % self.size
        output_shifted = self.rotor[input_index]
        return (output_shifted - pointer) % self.size

    def bcode(self, n: int, pointer: int) -> int:
        """Encode an index through the rotor backward.

        Args:
            n: Character index to transform.
            pointer: Current rotor offset.

        Returns:
            The transformed index.
        """
        input_shifted = (n + pointer) % self.size
        output_shifted = self.reverse_rotor[input_shifted]
        return (output_shifted - pointer) % self.size

    @staticmethod
    def test(rotor: List[int], size: int) -> List[InvalidValue]:
        """Validate rotor wiring as a permutation.

        Args:
            rotor: Wiring indices to validate.
            size: Expected wiring size.

        Returns:
            Validation errors, or an empty list when valid.
        """
        errors = []

        if not isinstance(rotor, (list, tuple)):
            errors.append(InvalidValue(
                field="rotor",
                code="invalid_type",
                message="Rotor wiring must be a list or tuple of integers",
            ))
            return errors

        if len(rotor) != size:
            errors.append(InvalidValue(
                field="rotor",
                code="size_mismatch",
                message=f"Rotor wiring length ({len(rotor)}) does not match character set size ({size})"
            ))
            return errors

        if not all(isinstance(value, int) and not isinstance(value, bool) for value in rotor):
            errors.append(InvalidValue(
                field="rotor",
                code="invalid_type",
                message="Rotor wiring must contain only integers",
            ))
            return errors

        expected_indices = set(range(size))
        rotor_set = set(rotor)
        extra_elements = list(rotor_set - expected_indices)
        missing_elements = list(expected_indices - rotor_set)
        duplicate_elements = sorted({value for value in rotor if rotor.count(value) > 1})

        if extra_elements:
            errors.append(InvalidValue(
                field="rotor",
                code="extra_indices",
                message="Extra elements found in rotor wiring",
                extra_info=extra_elements,
            ))
        if duplicate_elements:
            errors.append(InvalidValue(
                field="rotor",
                code="duplicate_indices",
                message="Duplicate indices found in rotor wiring",
                extra_info=duplicate_elements,
            ))
        if missing_elements:
            errors.append(InvalidValue(
                field="rotor",
                code="missing_indices",
                message="Missing elements found in rotor wiring",
                extra_info=missing_elements,
            ))
        return errors

    def __repr__(self) -> str:
        """Represent the rotor for debugging."""
        return f"Rotor(name='{self.name}', size={self.size})"

    # def __eq__(self, other: object) -> bool:
    #     if isinstance(other, Rotor):
    #         return self.rotor == other.rotor and self.size == other.size
    #     return False

    def __len__(self):
        """Return the rotor size."""
        return self.size
