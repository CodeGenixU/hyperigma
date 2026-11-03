
from ..rotor.rotor import Rotor
from ..rotor.rotor_state import RotorState
from .shaft import Shaft

class Axle:
    """
    A collection of RotorState objects that form a chain, representing the mechanical structure of an Enigma machine's rotor assembly.
    """

    def __init__(self, shaft: Shaft, initial_position: int = 0, rotation_base: int = 0) -> None:

        self.head = None
        self.tail = None
        self.rotation_base = rotation_base if rotation_base > 0 else shaft.size
        if not isinstance(shaft, Shaft):
            raise Exception

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
        temp = self.head
        while temp:
            yield temp
            temp = temp.next

    def fcode(self, n: int):

        temp = self.head
        while temp:
            n = temp.fcode(n)
            temp = temp.next

        return n

    def bcode(self, n: int):
        temp = self.tail
        while temp:
            n = temp.bcode(n)
            temp = temp.prev
        return n

    def rotate(self, pointer: int) -> None:

        temp = self.head
        while temp:
            if pointer % (self.rotation_base ** temp.position) == 0:
                temp.rotate()
            temp = temp.next
        