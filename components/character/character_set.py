"""Manage and validate the characters supported by the Enigma machine."""

from typing import Optional, List, Tuple, Set, Dict, Union

from ..exceptions import CharacterSetValidationError, InvalidCharacterError
from ..DTO.invalid_values import InvalidValue

class CharacterSet:
    """
    Reusable component for validating and managing the character set used in the Enigma machine.
    Ensures uniqueness and single-character constraints.
    """
    def __init__(self, characters: Union[List[str], Tuple[str, ...], Set[str]]) -> None:
        """
        Initialize the character set with validation.
        
        Args:
            characters (Union[List[str], Tuple[str, ...], Set[str]]): List of characters to be used in the machine.
            
        Raises:
            CharacterSetValidationError: If characters are invalid.
        """
        errors = self.test(characters)
        if errors:
            raise CharacterSetValidationError("Invalid character set", errors=errors)

        self.characters = tuple(characters)
        self.char_to_idx = {char: i for i, char in enumerate(self.characters)}
        self.idx_to_char = {i: char for i, char in enumerate(self.characters)}
        self.size = len(self.characters)

    def fcode(self, char: str) -> int:
        """Get the index of a character.

        Args:
            char: Character to look up.

        Returns:
            The character's numeric index.

        Raises:
            InvalidCharacterError: If char is not configured.
        """
        if char not in self.char_to_idx:
            raise InvalidCharacterError(f"Character '{char}' is not in the configured character set")
        return self.char_to_idx[char]

    def bcode(self, index: int) -> str:
        """Get the character at an index.

        Args:
            index: Numeric character index.

        Returns:
            The character at index.

        Raises:
            IndexError: If index is outside the character set.
        """
        if index < 0 or index >= self.size:
            raise IndexError(f"Index {index} is out of bounds for character set of size {self.size}")
        return self.idx_to_char[index]

    @staticmethod
    def test(characters: Union[List[str], Tuple[str, ...]]) -> List[InvalidValue]:
        """Validate characters for duplicates and invalid lengths.

        Args:
            characters: Characters to validate.

        Returns:
            Validation errors, or an empty list when valid.
        """

        errors = []

        if not isinstance(characters, (list, tuple)):
            errors.append(InvalidValue(
                field="characters",
                code="invalid_type",
                message="Characters must be a list, tuple, or set",
            ))
            return errors


        non_single_chars = [char for char in characters if not isinstance(char, str) or len(char) != 1]
        if non_single_chars:
            errors.append(InvalidValue(
                field="characters",
                code="invalid_character",
                message="Non-single character elements found",
                extra_info=non_single_chars,
            ))
            return errors

        unique_characters = set(characters)
        if len(characters) != len(unique_characters):
            duplicates = [char for char in unique_characters if list(characters).count(char) > 1]
            errors.append(InvalidValue(
                field="characters",
                code="duplicate_character",
                message="Duplicate characters found",
                extra_info=duplicates,
            ))
        return errors

    def __repr__(self) -> str:
        """Represent the character set with its stable index order."""
        l = [None] * self.size
        for char, idx in self.char_to_idx.items():
            l[idx] = char
        return f"CharacterSet({l})"

    def __len__(self) -> int:
        """Return the number of configured characters."""
        return self.size

    def __contains__(self, char: str) -> bool:
        """Check whether a character is configured.

        Args:
            char: Character to test.

        Returns:
            True when char is present.
        """
        return char in self.characters
