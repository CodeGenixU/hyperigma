from email import errors
from typing import Tuple, List, Dict, Optional, Union
from unicodedata import name

from ..exceptions import ValidationError
from ..DTO.invalid_values import InvalidValue

from ..rotor.rotor import Rotor

class Shaft:

    def __init__(self, n : int, sequence : Union[List[str], List[Rotor], Tuple[str, ...], Tuple[Rotor, ...]], rotors: Optional[Union[Dict[str, Rotor], Dict[str, List[int]]]] = None) -> None:

        error = self.test(n, sequence, rotors)
        if error:
            raise ValidationError(f"Invalid Shaft configuration: {error[0].message}")
    
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
        """Add a new rotor to the shaft configuration."""

        if len(rotor) != self.size:
            raise ValidationError(f"Invalid rotor wiring for '{rotor.name}': {errors[0].message}")

        self.sequence.append(rotor)
 

    @staticmethod
    def test(n: int, sequence: Union[List[str], List[Rotor], Tuple[str, ...], Tuple[Rotor, ...]], rotors: Optional[Union[Dict[str, Rotor], Dict[str, List[int]]]] = None) -> List[InvalidValue]:

        errors = []

        if isinstance(sequence, (list, tuple)) and all(isinstance(i, (str, Rotor)) for i in sequence):
            if all(isinstance(i, Rotor) for i in sequence):
                for rotor in sequence:
                    if len(rotor) != n:
                        errors.append(InvalidValue(field=f"rotor.{rotor.name}", message=f"Rotor wiring must be of length {n}"))
                    else:
                        errors.extend(Rotor.test(rotor, n))
            else:
                if not isinstance(rotors, dict):
                    errors.append(InvalidValue(field="rotors", message="'rotors' must be a dictionary"))
                else:
                    for rname in sequence:
                        if rname not in rotors:
                            errors.append(InvalidValue(field="Shaft", message=f"Rotor '{rname}' not defined in rotors"))
                        else:
                            rotor_wiring = rotors[rname]
                            if len(rotor_wiring) != n:
                                errors.append(InvalidValue(field=f"rotor.{rname}", message=f"Rotor wiring must be of length {n}"))
                            elif isinstance(rotor_wiring, list):
                                errors.extend(Rotor.test(rotor_wiring, n))
        else:
            errors.append(InvalidValue(field="sequence", message="'sequence' must be a list or tuple of strings or Rotor objects"))

            
        return errors

    def get(self):
        for i in self.sequence:
            yield i 
    