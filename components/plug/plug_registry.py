"""Assemble and validate plug cycles before machine construction."""

from typing import List, Optional, Union, Dict, Set, Tuple

from ..exceptions import PlugRegistryValidationError
from ..DTO.invalid_values import InvalidValue

from .plug import Plug

class PlugRegistry:
    """
    Mutable construction-time registry of non-overlapping plug cycles.

    A registry is handed to :class:`Plugboard` when the machine is built.
    """
    def __init__(self, plugs: Optional[Union[List[Plug], Tuple[Plug, ...], List[str], Tuple[str, ...]]] = None) -> None:
        """
        Initialize the PlugRegistry.
        
        Args:
            plugs (Optional[List[Plug]]): List of Plug objects.
        """
        self.plugs: List[Plug] = []
        self._char_map: Dict[str, Plug] = {}
        self._char_set: Set[str] = set()
        
        errors = PlugRegistry.test(plugs) if plugs else []
        if errors:
            raise PlugRegistryValidationError("Invalid plugboard", errors=errors)
        
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
            PlugRegistryValidationError: If any character conflicts with an existing cycle.
        """
        if not isinstance(plug, Plug):
            raise PlugRegistryValidationError(
                "Invalid plug",
                errors=[InvalidValue(
                    field="plug",
                    code="invalid_type",
                    message="Expected a Plug instance",
                )],
            )

        errors = Plug.test(plug.plug)
        if errors:
            raise PlugRegistryValidationError("Invalid plug", errors=errors)

        conflicts = set(plug.plug).intersection(self._char_set)
        
        if conflicts:
            raise PlugRegistryValidationError(
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

    def characters(self) -> Set[str]:
        """Return all characters registered in the plug cycles.

        Returns:
            Set of mapped characters.
        """
        return set(self._char_set)

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
                message="PlugRegistry must be a list or tuple",
            )]

        seen_chars: Set[str] = set()
        errors: List[InvalidValue] = []

        for index, item in enumerate(plugs):

            cycle = item.plug if isinstance(item, Plug) else item
            cycle_errors = Plug.test(cycle)
            for error in cycle_errors:
                errors.append(InvalidValue(
                    field=f"plugs[{index}]",
                    code=error.code,
                    message=error.message,
                    extra_info=error.extra_info,
                ))
            if cycle_errors:
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
        return f"PlugRegistry(plugs={[p.plug for p in self.plugs]})"

    def __str__(self) -> str:
        """Return a readable description of the plugboard."""
        return f"PlugRegistry with plugs: {', '.join([p.plug for p in self.plugs])}"
