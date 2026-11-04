"""Assemble and validate the ordered rotor shaft."""

from email import errors
from typing import Tuple, List, Dict, Optional, Union
from unicodedata import name

from ..exceptions import ShaftValidationError
from ..DTO.invalid_values import InvalidValue

from ..rotor.rotor import Rotor

class Shaft:
    """Store the ordered rotors used by the Enigma axle."""

    def __init__(self, n : int, sequence : Union[List[str], List[Rotor], Tuple[str, ...], Tuple[Rotor, ...]], rotors: Optional[Union[Dict[str, Rotor], Dict[str, List[int]]]] = None) -> None:
        """Initialize a shaft from rotor names or Rotor objects.

        Args:
            n: Character set size.
            sequence: Ordered rotor names or objects.
            rotors: Mapping of rotor names to wiring or objects.

        Raises:
            ShaftValidationError: If the rotor assembly is invalid.
        """

        error = self.test(n, sequence, rotors)
        if error:
            raise ShaftValidationError("Invalid rotor shaft", errors=error)

        self.size = n
        self.sequence = []

        if sequence and all(isinstance(i, Rotor) for i in sequence):
            for rotor in sequence:
                self.add_rotor(rotor)
        elif sequence:
            for key in sequence:
                rotor = Rotor(rotors[key], size=n, name=key) if isinstance(rotors[key], list) else rotors[key]
                self.add_rotor(rotor)

    def add_rotor(self, rotor : Rotor) -> None:
        """Add a rotor to the shaft configuration.

        Args:
            rotor: Rotor to append.
        """

        if len(rotor) != self.size:
            raise ShaftValidationError(
                "Invalid rotor shaft",
                errors=[InvalidValue(
                    field=f"rotor.{rotor.name}",
                    code="size_mismatch",
                    message=f"Rotor wiring must be of length {self.size}",
                )],
            )

        self.sequence.append(rotor)


    @staticmethod
    def test(n: int, sequence: Union[List[str], List[Rotor], Tuple[str, ...], Tuple[Rotor, ...]], rotors: Optional[Union[Dict[str, Rotor], Dict[str, List[int]]]] = None) -> List[InvalidValue]:
        """Validate a proposed rotor shaft.

        Args:
            n: Character set size.
            sequence: Ordered rotor names or objects.
            rotors: Mapping of rotor names to wiring or objects.

        Returns:
            Validation errors, or an empty list when valid.
        """

        errors = []

        if not isinstance(n, int) or n <= 0:
            return [InvalidValue(
                field="shaft.size",
                code="invalid_size",
                message="Character set size must be a positive integer",
            )]

        if isinstance(sequence, (list, tuple)) and all(isinstance(i, (str, Rotor)) for i in sequence):
            if all(isinstance(i, Rotor) for i in sequence):
                for rotor in sequence:
                    if len(rotor) != n:
                        errors.append(InvalidValue(
                            field=f"rotor.{rotor.name}",
                            code="size_mismatch",
                            message=f"Rotor wiring must be of length {n}",
                        ))
                    else:
                        errors.extend(Rotor.test(rotor, n))
            else:
                if not isinstance(rotors, dict):
                    errors.append(InvalidValue(
                        field="rotors",
                        code="invalid_type",
                        message="'rotors' must be a dictionary",
                    ))
                else:
                    for rname in sequence:
                        if rname not in rotors:
                            errors.append(InvalidValue(
                                field=f"rotors.{rname}",
                                code="unknown_rotor",
                                message="Rotor is not defined",
                            ))
                        else:
                            rotor_wiring = rotors[rname]
                            if not isinstance(rotor_wiring, (list, tuple)):
                                errors.append(InvalidValue(
                                    field=f"rotors.{rname}",
                                    code="invalid_type",
                                    message="Rotor wiring must be a list or tuple of integers",
                                ))
                            elif len(rotor_wiring) != n:
                                errors.append(InvalidValue(
                                    field=f"rotor.{rname}",
                                    code="size_mismatch",
                                    message=f"Rotor wiring must be of length {n}",
                                ))
                            else:
                                errors.extend(Rotor.test(rotor_wiring, n))
        else:
            errors.append(InvalidValue(
                field="sequence",
                code="invalid_type",
                message="'sequence' must be a list or tuple of strings or Rotor objects",
            ))


        return errors

    def get(self):
        """Yield rotors in shaft order."""
        for i in self.sequence:
            yield i
