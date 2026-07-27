"""
Axiom - Beast of an Ancient Legend
--------------------------------------------
This module simulates the Enigma encryption machine, including rotors, plugboard, and encoding logic.
Configuration is loaded from a dictionary or JSON file (see Configuration Structure for format).

Configuration Validation Flow:
-----------------------------
- Checks type of configuration (dictionary or JSON file).
- Validation is performed ONCE in the __new__ method (using pretest()).
- If the configuration is invalid, an exception is raised and the instance is not created.
- __init__ assumes the configuration is already valid and only initializes the machine.

Configuration Structure:
----------------------------------------------
{
    "setting": {
        "sequence_of_rotor": [str, ...],        # Sequence of rotors, e.g., [r1,r2,r3]
        "iteration": int,                # Initial iteration (rotor position/step)
        "rotation_factor": int,           # Rotation base (affects stepping)
        "plugs": [str, ...]              # List of plugboard cycles (e.g., ["ABCD"])
    },
    "characters": [str, ...],            # List of all valid characters for encoding
    "r1": [int, ...],                    # Rotor 1 wiring (permutation of indices)
    "r2": [int, ...],                    # Rotor 2 wiring
    "r3": [int, ...]                     # Rotor 3 wiring
    # ... more rotors as needed (r4, r5, etc.)
}

- The "setting" object defines the machine's configuration.
- "characters" is the character set used for encoding/decoding.
- Each "rX" key defines a rotor's wiring as a permutation of character indices.

Module Contents:
----------------

Classes:
    Enigma: Main machine controller (encoding/decoding)
    Rotor: Individual rotor logic
    plug: Plugboard cycle logic

Functions:
    - check_type(config): Load and validate configuration from dict, JSON file path, or Path object
    - plug_test(plugs): Validate plugboard cycles for repeated characters and conflicts
    - rotor_test(n, rotor): Validate rotor wiring as a proper permutation of n character indices
    - pretest(file): Comprehensive configuration validation including rotors, plugs, and characters

Classes:
    - Rotor: Individual rotor with wiring, position tracking, and stepping logic
    - plug: Plugboard cycle implementation for character swapping/substitution
    - Enigma: Main machine controller handling configuration, rotors, plugboard, and encoding

Exceptions:
    EnigmaError, ConfigurationError, InvalidCharacterError, ValidationError


Usage Example:
-------------
    >>> enigma = Enigma("configure.json")
    >>> encoded = ''.join(enigma.main(c) for c in "HELLO")
    >>> decoded = ''.join(Enigma("configure.json").main(c) for c in encoded)
    >>> print(decoded)  # 'HELLO'
-------------
    >>> from Enigma import Enigma
    >>> 
    >>> # Create an Enigma machine instance
    >>> enigma = Enigma("configure.json")
    >>> 
    >>> # Encode a message
    >>> message = "HELLO"
    >>> encoded = ""
    >>> for char in message:
    ...     encoded += enigma.main(char)
    >>> print(f"Encoded: {encoded}")
    Encoded: XKLMN
    >>> 
    >>> # Reset the machine to decode
    >>> enigma = Enigma("configure.json")
    >>> decoded = ""
    >>> for char in encoded:
    ...     decoded += enigma.main(char)
    >>> print(f"Decoded: {decoded}")
    Decoded: HELLO
"""

import json
import logging
from typing import List, Union, Dict, Tuple, Optional # pyright: ignore[reportShadowedImports]
from pathlib import Path
from dataclasses import dataclass
# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Custom exception classes for better error handling
class EnigmaError(Exception):
    """Base exception for Enigma machine errors."""
    pass

class ConfigurationError(EnigmaError):
    """Raised when there are issues with the configuration file."""
    pass

class InvalidCharacterError(EnigmaError):
    """Raised when a character is not in the configured character set."""
    pass

class ValidationError(EnigmaError):
    """Raised when validation fails during configuration checks."""
    pass

class InvalidValue(dataclass):
    """
    Data class to hold invalid values found during configuration validation.
    
    Attributes:
    """
    field: str
    message: str
    extra_info: Optional[Dict[str, Union[str, List[str], Dict[str, List[int]]]]] = None

class Configuration(dataclass):
    """
    Data class to hold Enigma configuration details.
    
    Attributes:
        characters (List[str]): List of valid characters for encoding/decoding.
        sequence_of_rotor (List[str]): Sequence of rotor names (e.g., ["r1", "r2", "r3"]).
        iteration (int): Initial iteration count for rotor stepping.
        rotation_factor (int): Base value for rotor stepping calculations.
        plugs (List[str]): List of plugboard cycle strings.
        rotors (Dict[str, List[int]]): Dictionary mapping rotor names to their wiring permutations.
    """
    characters: List[str]
    number_of_rotors: int
    sequence_of_rotor: List[str]
    iteration: int
    rotation_factor: int
    plugs: List[str]
    rotors: Dict[str, List[int]]

    def __init__(self, config: Union[dict, str, Path]) -> None:
        """
        Initialize the Configuration data class from a dictionary or JSON file path.
        
        Args:
            config (dict or str or Path): Configuration dictionary or path to a JSON file.
        
        Raises:
            ConfigurationError: If the configuration cannot be loaded or is invalid.
        """
        if isinstance(config, dict):
            self._load_from_dict(config)
        elif isinstance(config, (str, Path)):
            self._load_from_file(config)
        else:
            raise TypeError("Config must be a dict or a path to a JSON file.")

    def _load_from_dict(self, config: dict) -> None:
        """
        Load configuration from a dictionary.
        
        Args:
            config (dict): Configuration dictionary.
        Raises:
            ConfigurationError: If required fields are missing or invalid.
        """
        try:
            pretest(config)
            self.characters = config["characters"]
            setting = config["setting"]
            self.sequence_of_rotor = setting["sequence_of_rotor"]
            self.iteration = setting["iteration"]
            self.rotation_factor = setting["rotation_factor"]
            self.plugs = setting["plugs"]
            self.rotors = {key: config[key] for key in self.sequence_of_rotor}
            self.number_of_characters = len(self.characters)
        except KeyError as e:
            raise ConfigurationError(f"Missing required configuration field: {e}")
        except ValueError as e:
            raise ConfigurationError(f"Invalid value in configuration: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading configuration: {e}")

    def _load_from_file(self, file_path: Union[str, Path]) -> None:
        """
        Load configuration from a JSON file.
        
        Args:
            file_path (str or Path): Path to the JSON configuration file.
        Raises:
            ConfigurationError: If the file cannot be read or is invalid.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self._load_from_dict(config)
        except FileNotFoundError:
            raise ConfigurationError(f"Configuration file not found: {file_path}")
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in configuration file '{file_path}': {e}")
        except Exception as e:
            raise ConfigurationError(f"Error reading configuration file '{file_path}': {e}")   

    @staticmethod
    def metadata(config: Configuration):
        """
        Get metadata about the configuration.
        
        Returns:
            Dict[str, Union[int, List[str]]]: Metadata including number of rotors and sequence.
        """
        if config.number_of_characters == 0:
            yield InvalidValue(field="characters", message="Character list is empty")
        for i in config.sequence_of_rotor:
            if i not in config.rotors:
                yield InvalidValue(field=i, message=f"Rotor '{i}' is missing from configuration")
        
    @staticmethod
    def character_list_test(characters: List[str]):
        """
        Get the list of valid characters for encoding/decoding.
        
        Returns:
            List[str]: List of characters.
        """
        # Validate character list
        character_errors = []
                
        # Check for empty character list
        
        # Check for duplicate characters
        unique_characters = set(characters)
        if len(characters) != len(unique_characters):
            duplicates = [char for char in unique_characters if characters.count(char) > 1]
            yield InvalidValue(field="characters", message=f"Duplicate characters found", extra_info = duplicates)
        
        # Check that all elements are single characters (strings of length 1)
        non_single_chars = [char for char in characters if not isinstance(char, str) or len(char) != 1]
        if non_single_chars:
            yield InvalidValue(field="characters", message=f"Non-single character elements found", extra_info = non_single_chars)

    @staticmethod
    def plug_test(plugs: List[str]):
        """
        Check for repeated characters in plugboard cycles.
        
        This function validates that no character appears in multiple plugboard cycles,
        which would create ambiguous mappings in the Enigma machine.
        
        Args:
            plugs: List of plugboard cycle strings (e.g., ["ABCD", "EFGH"])
            
        Returns:
            List of repeated characters if found, True if no repeats
            
        Example:
            >>> plug_test(["ABCD", "EFGH"])
            True
            >>> plug_test(["ABCD", "EFGC"])
            ['C', 'G']
        """
        seen_chars = set()  # O(1) lookup for better performance
        repeated_characters: List[str] = []
        
        for plug_cycle in plugs:
            for char in plug_cycle:
                if char in seen_chars:
                    repeated_characters.append(char)
                seen_chars.add(char)
        if repeated_characters:
            yield InvalidValue(field="plugs", message="Repeated characters found in plugboard cycles", extra_info=repeated_characters)
    
    @staticmethod
    def rotor_test(n: int, rotors: Dict[str, List[int]]):
        """
        Validate rotor wiring as a permutation of n indices.
        
        This function ensures that the rotor wiring is a valid permutation,
        meaning each index from 0 to n-1 appears exactly once.
        
        Args:
            n: Number of characters in the character set
            rotors: Dictionary mapping rotor names to their wiring permutations
        """
        for i in rotors:
            if len(rotors[i]) != n:
                yield InvalidValue(field=i, message=f"Rotor '{i}' wiring length ({len(rotors[i])}) does not match number of characters ({n})")

    @staticmethod
    def pretest(config: dict):
        """
        Validate configuration file for consistency and correctness.
        
        This function performs comprehensive validation of the Enigma configuration:
        - Checks that the number of rotors matches the sequence
        - Validates plugboard cycles for repeated characters
        - Ensures each rotor wiring is a valid permutation
        
        Args:
            config: Configuration dictionary
        """
        errors = []
        for i in Configuration.metadata(config):
            errors.append(i)
        for i in Configuration.character_list_test(config.characters):
            errors.append(i)
        for i in Configuration.plug_test(config.plugs):
            errors.append(i)
        for i in Configuration.rotor_test(len(config.characters), config.rotors):
            errors.append(i)
        if errors:
            for error in errors:
                logger.error(f"Validation error: {error.field} - {error.message} - Extra Info: {error.extra_info}")
            raise ValidationError("Configuration validation failed. See logs for details.")

    def obj(self, rotors: Dict[str, List[int]], plugs: List[str], size: int):
        """
        Initialize the Enigma machine with the validated configuration.
        This method sets up the rotors and plugboard based on the configuration.
        """
        # Implementation of initialization logic goes here
        for name, wiring in rotors.items():
            temp = Rotor(wiring, size)
            self.rotors[name] = temp
            yield temp
        self.rotors = {name: Rotor(wiring, size) for idx, (name, wiring) in enumerate(rotors.items())}
        pass


class Rotor:
    """
    Represents a single rotor in the Enigma` machine.
    Handles rotor wiring, position, and rotation logic.
    """
    def __init__(self, rotor: List[int], size: int):
        """
        Initialize the rotor.
        
        Args:
            rotor: The rotor wiring (permutation of character indices).
            size: The size of the rotor.
        """

        errors = list(Rotor.test(rotor, size))
        if errors:
            yield from errors
            return

        self.rotor = rotor
        self.reverse_rotor = [0] * size
        self.size = size
        for i, val in enumerate(self.rotor):
            self.reverse_rotor[val] = i

    def fcode(self, n: int, pointer: int) -> int:
        """
        Forward encoding through the rotor.
        
        This method processes a character index through the rotor in the forward
        direction. The rotor rotates (steps) if it's at a turnover position,
        which is determined by the iteration count and position.
        
        Args:
            n: Input character index
            pointer: Current pointer position
        Returns:
            Encoded character index after forward rotor processing
        """
        # 1. Apply offset to the input index
        input_index = (n + pointer) % self.size
        
        # 2. Find the encoded value using the fixed wiring list
        output_shifted_index = self.rotor[input_index]
        
        # 3. Subtract the offset from the output to align it correctly
        output_index = (output_shifted_index - pointer) % self.size

        return output_index
    
    def bcode(self, n: int, pointer: int) -> int:
        """
        Backward encoding through the rotor (inverse mapping).
        
        This method processes a character index through the rotor in the backward
        direction, applying the inverse of the forward rotor mapping. This is
        used when the signal returns through the rotors after reflection.
        
        Args:
            n: Encoded character index
            pointer: Current pointer position
            
        Returns:
            Decoded character index after backward rotor processing
        """
        # 1. Apply the offset to the input value to account for the rotation
        input_value_shifted = (n + pointer) % self.size
        
        # 2. Find the index of this shifted value in the list (the inverse mapping)
        output_index_shifted = self.reverse_rotor[input_value_shifted]

        # 3. Subtract the offset from the resulting index to align it correctly
        output_index = (output_index_shifted - pointer) % self.size
        return output_index
    @staticmethod
    def test(rotor, size):
        """
        Test the rotor wiring for correctness.
        
        This method checks that the rotor wiring is a valid permutation of indices,
        meaning each index from 0 to rotor_size - 1 appears exactly once.
        
        Returns:
            True if valid, False otherwise
        """
        expected_indices = set(range(size))
        rotor_set = set(rotor)
        
        extra_elements = list(rotor_set - expected_indices)
        missing_elements = list(expected_indices - rotor_set)
        
        if extra_elements:
            yield   InvalidValue(field="Rotor", message=f"Extra elements found in rotor wiring", extra_info=extra_elements)
        if missing_elements:
            yield InvalidValue(field="Rotor", message=f"Missing elements found in rotor wiring", extra_info=missing_elements)

class RotorState:
    """
    Represents the state of a rotor, including its wiring, position, and pointer.
    This class is used to encapsulate the rotor's configuration and current state.
    """
    def __init__(self, rotor: Rotor, position: int, cls: Enigma):
        """
        Initialize the RotorState.
        
        Args:
            rotor: The rotor wiring (permutation of character indices).
            position: The position of this rotor in the machine (0 = rightmost).
            pointer: The current pointer position for this rotor.
        """
        self.enigma = cls
        self.rotor = rotor
        self.position = position
        self.rotation_base = cls.rotation_base
        self.size = self.rotor.size
        self.pointer = self.enigma.iteration % (self.rotation_base ** self.position)

    def rotate(self):
        """
        Rotate the rotor by one position (step forward).
        """
        self.pointer += 1

    def fcode(self, n: int) -> int:
        """
        Forward encoding through the rotor.
        
        Args:
            n: Input character index
            
        Returns:
            Encoded character index after forward rotor processing
        """
        return self.rotor.fcode(n, self.pointer)

    def bcode(self, n: int) -> int:
        """
        Backward encoding through the rotor (inverse mapping).
        
        Args:
            n: Encoded character index
            
        Returns:
            Decoded character index after backward rotor processing
        """
        return self.rotor.bcode(n, self.pointer)
    

class Plug:  # Standard Python naming convention uses PascalCase for classes
    """
    Represents a plugboard cycle (swapping characters before/after rotors).
    """
    def __init__(self, plug_cycle: str) -> None:
        """
        Initialize the plugboard cycle with O(1) lookup tables.
        """
        self.plug_cycle = plug_cycle
        self.elements = set(plug_cycle)  # For O(1) membership checks    
        # Build forward and backward mapping dictionaries once during initialization
        n = len(plug_cycle)
        if n == 0:
            self._f_map = {}
            self._b_map = {}
            return

        # Forward mapping: char -> next char (with wrap-around)
        self._f_map = {plug_cycle[i]: plug_cycle[(i + 1) % n] for i in range(n)}
        
        # Backward mapping: char -> previous char (with wrap-around)
        self._b_map = {plug_cycle[i]: plug_cycle[(i - 1) % n] for i in range(n)}

    def fplug(self, character: str) -> str:
        """
        Swap character using the plugboard cycle in O(1) time in forward direction.
        
        Args:
            character: Character to swap            
        Returns:
            Swapped character according to the cycle (or original if not in cycle)
        """
        return self._f_map.get(character, character)

    def bplug(self, character: str) -> str:
        """
        Swap character using the plugboard cycle in O(1) time in backward direction.
        Args:
            character: Character to swap            
        Returns:
            Swapped character according to the cycle
        """
        return self._b_map.get(character, character)

    def isplug(self, character: str) -> bool:
        """
        Check if the character is part of the plugboard cycle.
        
        Args:
            character: Character to check
        Returns:
            True if character is in the cycle, False otherwise
        """
        return character in self.elements

    @staticmethod
    def test(cycle: str):
        """
        Validate the plugboard cycle for repeated characters.
        
        Args:
            cycle: Plugboard cycle string (e.g., "ABCD")
            
        Returns:
            True if valid (no repeats), False if invalid (repeats found)
        """
        unique_chars = set(cycle)
        if len(unique_chars) != len(cycle):
            duplicates = [char for char in unique_chars if cycle.count(char) > 1]
            yield InvalidValue(field="Plug", message=f"Duplicate characters found in plugboard cycle", extra_info=duplicates)
    
class Enigma:
    """
    Main Enigma machine class. Handles loading configuration, managing rotors and plugboard, and encoding characters.
    
    Attributes:
        characters (List[str]): Character set used for encoding/decoding
        number_of_rotors (int): Number of rotors in the machine
        iteration (int): Current step count (affects rotor positions)
        rotation_base (int): Base value for rotor stepping calculations
        rotor (Dict[int, Rotor]): Dictionary of rotor instances indexed by position
        plug (List[str]): List of plugboard cycle strings from configuration
        plugs (Dict[str, plug]): Dictionary of plugboard cycle instances
    """
    def __new__(cls, file: Union[str, dict]) -> 'EnigmaClass':
        """
        Validate configuration before creating an Enigma instance.
        
        Args:
            file: Path to the JSON configuration file or configuration dictionary.
            
        Returns:
            Enigma instance if validation passes.
            
        Raises:
            ConfigurationError: If configuration file cannot be loaded or is invalid.
            ValidationError: If configuration validation fails.
        """
        logger.info(f"Creating Enigma instance with configuration: {file}")
        
        try:
            precheck = pretest(file)
            if len(precheck[1]) != 0:
                # Build detailed error message
                error_messages = []
                for component, status in precheck[0].items():
                    if not status:
                        error_messages.append(f"Component '{component}' failed validation")
                
                for error_type, error_details in precheck[1].items():
                    error_messages.append(f"{error_type}: {error_details}")
                
                error_msg = f"Configuration validation failed:\n" + "\n".join(error_messages)
                logger.error(error_msg)
                raise ValidationError(error_msg)
            
            logger.info("Configuration validation successful, creating Enigma instance")
            return super().__new__(cls)
        except (ConfigurationError, ValidationError):
            # Re-raise these specific exceptions as-is
            raise
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {file}")
            raise ConfigurationError(f"Configuration file not found: {file}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            raise ConfigurationError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            logger.error(f"Unexpected error loading configuration: {e}")
            raise ConfigurationError(f"Unexpected error loading configuration: {e}")
    
    def __init__(self, file: Union[str, dict]) -> None:
        """
        Initialize the Enigma machine from a configuration file or dictionary.

        Args:
            file: Path to the JSON configuration file or a configuration dictionary.

        Note:
            Configuration validation is performed in __new__ (via pretest()).
            This method assumes the configuration is already valid and only initializes the machine.
        """
        logger.debug("Initializing Enigma machine components")
        
        # Load configuration (already validated in __new__)
        key = check_type(file)

        # Set character set
        self.characters = key["characters"]

        # Initialize machine settings (number of rotors, initial iteration, and rotation base)
        # rotation_base: Used in rotor stepping logic. If rotation_factor is 0 in config,
        # defaults to character set length for classic Enigma behavior; otherwise uses the configured value.
        # This allows custom stepping patterns without modifying the configuration file.
        self.number_of_rotors = key["setting"]["number_of_rotors"]
        self.iteration = key["setting"]["iteration"]
        self.rotation_base = len(self.characters) if key["setting"]["rotation_factor"] == 0 else key["setting"]["rotation_factor"]

        # Initialize rotors in the specified sequence
        sequence_parts = key["setting"]["sequence_of_rotor"].split(">")
        self.rotor: Dict[int, Rotor] = {}
        for i in range(self.number_of_rotors):
            rotor_name = sequence_parts[i]
            self.rotor[i] = Rotor(key[rotor_name], i, self)

        # Initialize plugboard cycles and plug objects
        self.plug = key["setting"]["plugs"]
        self.plugs: Dict[str, plug] = {}
        for i in self.plug:
            self.plugs[i] = plug(i)

        # Log successful initialization
        logger.info(f"Enigma machine initialized with {self.number_of_rotors} rotors and {len(self.characters)} characters")
    
    def __plugin(self, char: str, mode: int = 0) -> str:
        """
        Pass character through the plugboard (forward or backward).
        
        This method applies plugboard substitution to a character. If the character
        is part of a plugboard cycle, it gets swapped with the next character in
        the cycle. If not in any cycle, the character remains unchanged.
        
        Args:
            char: Character to swap
            mode: 0 for forward mapping, 1 for backward mapping
            
        Returns:
            Swapped character (or original if not in any plugboard cycle)
        """
        for i in self.plug:
            if char in i:
                return self.plugs[i].plugs(char, mode)
        else:
            return char
    
    def __prerotor(self, char: str) -> int:
        """
        Convert character to its index in the character set.
        
        This method maps a character to its corresponding index in the
        configured character set for rotor processing.
        
        Args:
            char: Character to convert
            
        Returns:
            Index of the character in the character set
        """
        return self.characters.index(char)
    
    def __postrotor(self, char: int) -> str:
        """
        Convert index back to character after rotor processing.
        
        This method converts a rotor-processed index back to its corresponding
        character in the configured character set.
        
        Args:
            char: Index to convert
            
        Returns:
            Character at the given index in the character set
        """
        return self.characters[char]

    def main(self, char: str) -> str:
        """
        Encode/Decode a single character using the Enigma machine logic.
        
        This method implements the complete Enigma encryption/decryption process:
        1. Plugboard forward mapping
        2. Forward pass through all rotors
        3. Reflection (signal reversal)
        4. Backward pass through all rotors
        5. Plugboard backward mapping
        6. Rotor stepping for next character
        
        Args:
            char: Character to encode or decode
            
        Returns:
            Encoded or decoded character
            
        Raises:
            InvalidCharacterError: If character is not in the configured character set
            
        Example:
            >>> enigma = Enigma("configure.json")
            >>> enigma.main("A")
            'X'
            >>> enigma.main("X")  # Decoding the same character
            'A'
        """
        # Validates input from character set
        if char not in self.characters:
            logger.error(f"Invalid character '{char}' not in character set")
            raise InvalidCharacterError(f"Character '{char}' is not in the configured character set")
        
        logger.debug(f"Processing character: '{char}'")
        
        # Pass through plugboard (forward)
        first_encode = self.__plugin(char)
        # Convert to index
        rotor_encode = self.__prerotor(first_encode)
        # Pass through all rotors (forward)
        for i in self.rotor:
            rotor_encode = self.rotor[i].fcode(rotor_encode)
        # Reflector (reverse the signal)
        reflector = len(self.characters) - 1 - rotor_encode
        # Pass back through all rotors (backward)
        for i in range(self.number_of_rotors - 1, -1, -1):
            reflector = self.rotor[i].bcode(reflector)
        # Convert back to character
        rotor_decode = self.__postrotor(reflector)
        # Pass through plugboard (backward)
        final_encode = self.__plugin(rotor_decode, 1)
        # Advance iteration (rotor stepping)
        self.iteration += 1
        
        logger.debug(f"Encoded '{char}' -> '{final_encode}' (iteration: {self.iteration})")
        return final_encode


