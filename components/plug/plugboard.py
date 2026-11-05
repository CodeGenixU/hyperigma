"""Provide the immutable runtime plugboard mapping."""

from typing import Dict, Tuple

from ..exceptions import PlugboardValidationError
from ..DTO.invalid_values import InvalidValue

from .plug import Plug
from .plug_registry import PlugRegistry

class Plugboard:
    """
    Finalized runtime mapping created from a :class:`PlugRegistry`.

    This class intentionally has no mutation methods. Build or modify a
    registry before constructing a new plugboard.
    """
    def __init__(self, registry: PlugRegistry) -> None:
        """
        Initialize the Plugboard.
        
        Args:
            registry (PlugRegistry): The plug registry to initialize the plugboard with.
        """
        if not isinstance(registry, PlugRegistry):
            raise PlugboardValidationError(
                "Invalid plugboard",
                errors=[InvalidValue(
                    field="registry",
                    code="invalid_type",
                    message="Expected a PlugRegistry instance",
                )],
            )
        self.plugs: Tuple[Plug, ...] = tuple(registry.plugs)
        self._char_map: Dict[str, Plug] = dict(registry._char_map)
        
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

    def __repr__(self) -> str:
        """Represent the plugboard for debugging."""
        return f"Plugboard(plugs={[p.plug for p in self.plugs]})"

    def __str__(self) -> str:
        """Return a readable description of the plugboard."""
        return f"Plugboard with plugs: {', '.join([p.plug for p in self.plugs])}"
