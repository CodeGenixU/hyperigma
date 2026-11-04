"""Manage a collection of non-overlapping plugboard cycles."""

from typing import List, Optional, Union, Dict, Set, Tuple

from ..exceptions import PlugboardValidationError
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
            raise PlugboardValidationError("Invalid plugboard", errors=errors)
        
        if plugs:
            for i in plugs:
                item = i if isinstance(i, Plug) else Plug(i)
                self.add_plug(item)

        
    def add_plug(self, plug: Plug) -> None:
        """
        Add a plug cycle to the plugboard.

        Args:
            plug: Plug cycle to add.
        
        Raises:
            PlugboardValidationError: If any character conflicts with an existing cycle.
        """
        conflicts = [char for char in plug.plug if char in self._char_set]
        
        if conflicts:
            raise PlugboardValidationError(
                "Plug cycle conflicts with existing plugs",
                errors=[InvalidValue(
                    field="plug",
                    code="overlapping_characters",
                    message="Characters already belong to another plug cycle",
                    extra_info=conflicts,
                )],
            )
        
        self.plugs.append(plug)
        for char in plug.plug:
            self._char_map[char] = plug
            self._char_set.add(char)

    def fplug(self, character: str) -> str:
        """Pass a character through its matching plug forward.

        Args:
            character: Character to map.

        Returns:
            The mapped character.
        """
        plug = self._char_map.get(character, None)
        return plug.fplug(character) if plug else character

    def bplug(self, character: str) -> str:
        """Pass a character through its matching plug backward.

        Args:
            character: Character to map.

        Returns:
            The mapped character.
        """
        plug = self._char_map.get(character, None)
        return plug.bplug(character) if plug else character

    def characters(self) -> Set[str]:
        """Return all characters involved in the plugboard.

        Returns:
            Set of mapped characters.
        """
        return self._char_set

    @staticmethod
    def test(plugs: Union[List[Plug], Tuple[Plug, ...], List[str], Tuple[str, ...]]) -> List[InvalidValue]:
        """Validate plug cycles for duplicates and conflicts.

        Args:
            plugs: Plug cycles to validate.

        Returns:
            Validation errors, or an empty list when valid.
        """

        if not isinstance(plugs, (list, tuple)):
            return [InvalidValue(
                field="plugs",
                code="invalid_type",
                message="Plugboard must be a list or tuple",
            )]

        seen_chars: Set[str] = set()
        errors: List[InvalidValue] = []

        for index, item in enumerate(plugs):

            cycle = item.plug if isinstance(item, Plug) else item
            if not isinstance(cycle, (str, list, tuple)):
                errors.append(InvalidValue(
                    field=f"plugs[{index}]",
                    code="invalid_type",
                    message="Plug cycle must be a string, list, or tuple",
                ))
                continue
            if not cycle:
                errors.append(InvalidValue(
                    field=f"plugs[{index}]",
                    code="empty_cycle",
                    message="Plug cycle cannot be empty",
                ))
                continue

            cycle_chars: Set[str] = set()
            for char in cycle:
                if char in cycle_chars:
                    errors.append(InvalidValue(
                        field=f"plugs[{index}]",
                        code="duplicate_character",
                        message=f"Character '{char}' appears more than once in this plug cycle",
                        extra_info=char
                    ))
                elif char in seen_chars:
                    errors.append(InvalidValue(
                        field=f"plugs[{index}]",
                        code="overlapping_characters",
                        message=f"Character '{char}' appears in multiple plug cycles",
                        extra_info=char
                    ))
                cycle_chars.add(char)
                seen_chars.add(char)

        return errors

    def __repr__(self) -> str:
        """Represent the plugboard for debugging."""
        return f"Plugboard(plugs={[p.plug for p in self.plugs]})"

    def __str__(self) -> str:
        """Return a readable description of the plugboard."""
        return f"Plugboard with plugs: {', '.join([p.plug for p in self.plugs])}"
