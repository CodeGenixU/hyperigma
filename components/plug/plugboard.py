from typing import List, Optional, Union, Dict, Set

from ..exceptions import ValidationError
from ..DTO.invalid_values import InvalidValue

from .plug import Plug

class Plugboard:
    """
    Reusable component managing a collection of Plug objects.
    Ensures no overlapping characters between different plug cycles.
    """
    def __init__(self, plugs: Optional[List[Union[Plug, str]]] = None) -> None:
        """
        Initialize the Plugboard.
        
        Args:
            plugs (Optional[List[Union[Plug, str]]]): List of Plug objects or plug cycle strings.
        """
        self.plugs: List[Plug] = []
        self._char_map: Dict[str, Plug] = {}

        if plugs:
            for item in plugs:
                plug_obj = item if isinstance(item, Plug) else Plug(item)
                self.add_plug(plug_obj)

    def add_plug(self, plug: Plug) -> None:
        """
        Add a Plug object to the plugboard.
        
        Raises:
            ValidationError: If any character in plug conflicts with an existing plug cycle.
        """
        conflicts = [char for char in plug.elements if char in self._char_map]
        if conflicts:
            raise ValidationError(f"Plug cycle '{plug.plug_cycle}' conflicts with existing plugs on characters: {conflicts}")
        
        self.plugs.append(plug)
        for char in plug.elements:
            self._char_map[char] = plug

    def fplug(self, character: str) -> str:
        """Pass character through matching plug in forward direction."""
        plug = self._char_map.get(character)
        return plug.fplug(character) if plug else character

    def bplug(self, character: str) -> str:
        """Pass character through matching plug in backward direction."""
        plug = self._char_map.get(character)
        return plug.bplug(character) if plug else character

    def characters(self) -> Set[str]:
        """Return a set of all characters involved in the plugboard."""
        return set(self._char_map.keys())

    @staticmethod
    def test(plugs: List[str, Plug]) -> List[InvalidValue]:
        """Validate a list of plug cycles for internal duplicates and cross-cycle conflicts."""

        seen_chars: Set[str] = set()
        errors: List[InvalidValue] = []

        for item in plugs:

            cycle_str = item.plug_cycle if isinstance(item, Plug) else item
            errors.extend(Plug.test(cycle_str))

            for char in cycle_str:

                if char in seen_chars:
                    errors.append(InvalidValue(
                        field="plugs",
                        message=f"Character '{char}' appears in multiple plug cycles",
                        extra_info=char
                    ))

                seen_chars.add(char)

        return errors

    def __repr__(self) -> str:
        return f"Plugboard(plugs={[p.plug for p in self.plugs]})"
