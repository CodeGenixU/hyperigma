from typing import Optional, List, Tuple, Set, Dict, Union

from ..exceptions import ValidationError, InvalidCharacterError
from ..DTO.invalid_values import InvalidValue

class CharacterSet:
    """
    Reusable component for validating and managing the character set used in the Enigma machine.
    Ensures uniqueness and single-character constraints.
    """
    def __init__(self, characters: Union[List[str], Tuple[str, ...], Set[str]]) -> None:
        """
        Initialize CharacterSet with validation.
        
        Args:
            characters (Union[List[str], Tuple[str, ...], Set[str]]): List of characters to be used in the machine.
            
        Raises:
            ValidationError: If character list is invalid (duplicates or non-single characters).
        """
        errors = self.test(characters)
        if errors:
            raise ValidationError(f"Invalid character list: {errors[0].message}")

        self.characters = set(characters)
        self.char_to_idx = {char: i for i, char in enumerate(self.characters)}
        self.idx_to_char = {i: char for i, char in enumerate(self.characters)}
        self.size = len(self.characters)

    def fcode(self, char: str) -> int:
        """Get index of character in the character set."""
        if char not in self.char_to_idx:
            raise InvalidCharacterError(f"Character '{char}' is not in the configured character set")
        return self.char_to_idx[char]

    def bcode(self, index: int) -> str:
        """Get character corresponding to index in the character set."""
        if index < 0 or index >= self.size:
            raise IndexError(f"Index {index} is out of bounds for character set of size {self.size}")
        return self.idx_to_char[index]

    @staticmethod
    def test(characters: Union[List[str], Tuple[str, ...], Set[str]]) -> List[InvalidValue]:
        """Validate character list for duplicates and non-single characters."""

        errors = []

        if not isinstance(characters, (list, tuple, set)):
            errors.append(InvalidValue(field="characters", message="Characters must be a list, tuple, or set"))

        unique_characters = set(characters)
        if len(characters) != len(unique_characters):
            duplicates = [char for char in unique_characters if characters.count(char) > 1]
            errors.append(InvalidValue(field="characters", message="Duplicate characters found", extra_info=duplicates))

        non_single_chars = [char for char in characters if not isinstance(char, str) or len(char) != 1]
        if non_single_chars:
            errors.append(InvalidValue(field="characters", message="Non-single character elements found", extra_info=non_single_chars))

        return errors

    def __repr__(self) -> str:
        l = [None] * self.size
        for char, idx in self.char_to_idx.items():
            l[idx] = char
        return f"CharacterSet({l})"

    def __len__(self) -> int:
        return self.size

    def __contains__(self, char: str) -> bool:
        return char in self.characters