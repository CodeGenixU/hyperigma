from email import errors
from typing import List, Dict
from unicodedata import name

from ..exceptions import ValidationError
from ..DTO.invalid_values import InvalidValue

from ..rotor.rotor import Rotor

class Shaft:

    def __init__(self, n : int, sequence : List[str, Rotor], rotors: Dict[str, List[int]]) -> None:

        error = self.validate(n, sequence, rotors)
        if error:
            raise ValidationError(f"Invalid Shaft configuration: {error[0].message}")
    
        self.size = n
        self.sequence = []
        self.rotors = {}

        if sequence:
            for key in sequence:
                rotor_obj = Rotor(rotors[key], size=n, name=key) if isinstance(rotors[key], list) else rotors[key]
                self.add_rotor(rotor_obj)

    def add_rotor(self, rotor : Rotor) -> None:
        """Add a new rotor to the shaft configuration."""

        if len(rotor) != self.size:
            raise ValidationError(f"Invalid rotor wiring for '{rotor.name}': {errors[0].message}")

        self.sequence.append(rotor.name)
        if rotor.name not in self.rotors:
            self.rotors[rotor.name] = rotor 

    @staticmethod
    def validate(n: int, sequence: List[str], rotors: Dict[str, List[int]]) -> List[InvalidValue]:

        errors = []
        for rname in sequence:
            if rname not in rotors:
                errors.append(InvalidValue(field="Shaft", message=f"Rotor '{rname}' not defined in rotors"))
            else:
                errors.extend(Rotor.test(rotors[rname], n))
        return errors

    def get(self):
        for i in self.sequence:
            yield self.rotors[i] 
    