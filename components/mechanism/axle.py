"""Link rotor states and apply Enigma signal transformations."""


from ..rotor.rotor import Rotor
from ..rotor.rotor_state import RotorState
from ..exceptions import AxleValidationError
from ..DTO.invalid_values import InvalidValue
from .shaft import Shaft

class Axle:
    """
    A collection of RotorState objects that form a chain, representing the mechanical structure of an Enigma machine's rotor assembly.
    """

    def __init__(self, shaft: Shaft, initial_position: int = 0, rotation_base: int = 0) -> None:
        """Build an axle from the rotors in a shaft.

        Args:
            shaft: Shaft containing the rotor sequence.
            initial_position: Initial machine position.
            rotation_base: Base used for rotor stepping.
        """

        self.head = None
        self.tail = None
        if not isinstance(shaft, Shaft):
            raise AxleValidationError(
                "Invalid rotor axle",
                errors=[InvalidValue(
                    field="shaft",
                    code="invalid_type",
                    message="Expected a Shaft instance",
                )],
            )
        self.rotation_base = rotation_base if rotation_base > 0 else shaft.size

        temp = None
        for i, rotor in enumerate(shaft.get(), start=0):
            temp = RotorState(rotor, i, rotation_base, initial_position)
            if self.head is None:
                self.head = self.tail = temp
            else:
                temp.prev = self.tail
                self.tail.next = temp
            self.tail = temp

    def get_rotors(self):
        """Yield rotor states from the head to the tail.

        Yields:
            Rotor states in forward order.
        """
        temp = self.head
        while temp:
            yield temp
            temp = temp.next

    def fcode(self, n: int):
        """Pass an index through rotors in forward order.

        Args:
            n: Index to transform.

        Returns:
            The transformed index.
        """

        temp = self.head
        while temp:
            n = temp.fcode(n)
            temp = temp.next

        return n

    def bcode(self, n: int):
        """Pass an index through rotors in reverse order.

        Args:
            n: Index to transform.

        Returns:
            The transformed index.
        """
        temp = self.tail
        while temp:
            n = temp.bcode(n)
            temp = temp.prev
        return n

    def rotate(self, pointer: int) -> None:
        """Rotate each rotor whose stepping threshold is reached.

        Args:
            pointer: Current machine pointer.
        """

        temp = self.head
        while temp:
            if pointer % (self.rotation_base ** temp.position) == 0:
                temp.rotate()
            temp = temp.next
