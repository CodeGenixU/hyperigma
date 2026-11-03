from typing import List, Optional, Union, Dict, Set, Tuple

from ..exceptions import ValidationError
from ..DTO.invalid_values import InvalidValue

from .plug import Plug

class Plugboard:
    """
    Reusable component managing a collection of Plug objects.
    Ensures no overlapping characters between different plug cycles.
    """
    def __init__(self, plugs: Optional[Union[List[Plug], Tuple[Plug, ...], List[str], Tuple[str, ...]]] = None) -> None:
        """
        Initialize the Plugboard.
        
        Args:
            plugs (Optional[List[Plug]]): List of Plug objects.
        """
        self.plugs: List[Plug] = []
        self._char_map: Dict[str, Plug] = {}
        self._char_set: Set[str] = set()
        
        errors = Plugboard.test(plugs) if plugs else []
        if errors:
                    raise ValidationError(f"Plug cycle '{item.plug}' conflicts with existing plugs on characters: {errors[0].message}")
        
        if plugs:
            for i in plugs:
                item = i if isinstance(i, Plug) else Plug(i)
                self.add_plug(item)

        
    def add_plug(self, plug: Plug) -> None:
        """
        Add a Plug object to the plugboard.
        
        Raises:
            ValidationError: If any character in plug conflicts with an existing plug cycle.
        """
        conflicts = [char for char in plug.plug if char in self._char_set]
        
        if conflicts:
            raise ValidationError(f"Plug cycle '{plug.plug}' conflicts with existing plugs on characters: {conflicts}")
        
        self.plugs.append(plug)
        for char in plug.plug:
            self._char_map[char] = plug
            self._char_set.add(char)

    def fplug(self, character: str) -> str:
        """Pass character through matching plug in forward direction."""
        plug = self._char_map.get(character, None)
        return plug.fplug(character) if plug else character

    def bplug(self, character: str) -> str:
        """Pass character through matching plug in backward direction."""
        plug = self._char_map.get(character, None)
        return plug.bplug(character) if plug else character

    def characters(self) -> Set[str]:
        """Return a set of all characters involved in the plugboard."""
        return self._char_set

    @staticmethod
    def test(plugs: Union[List[Plug], Tuple[Plug, ...], List[str], Tuple[str, ...]]) -> List[InvalidValue]:
        """Validate a list of plug cycles for internal duplicates and cross-cycle conflicts."""

        seen_chars: Set[str] = set()
        errors: List[InvalidValue] = []

        for item in plugs:

            cycle = item.plug if isinstance(item, Plug) else item

            for char in cycle:

                if char in seen_chars:
                    errors.append(InvalidValue(
                        field="plugs",
                        message=f"Character '{char}' appears in multiple plug cycles",
                        extra_info=char
                    ))
                    continue
                seen_chars.add(char)

        return errors

    def __repr__(self) -> str:
        return f"Plugboard(plugs={[p.plug for p in self.plugs]})"

    def __str__(self) -> str:
        return f"Plugboard with plugs: {', '.join([p.plug for p in self.plugs])}"
