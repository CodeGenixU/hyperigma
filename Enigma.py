"""
Axiom - Beast of an Ancient Legend
--------------------------------------------
This module simulates the Enigma encryption machine, including rotors, plugboard, and encoding logic.
Configuration is loaded from a dictionary or JSON file (see Configuration Structure for format).

Architecture & Decoupled Components:
------------------------------------
- Plug: Independent, reusable plugboard cycle logic for character swapping.
- Plugboard: Independent, reusable collection of Plug objects with non-overlapping validation.
- Rotor: Independent, reusable, immutable rotor wiring specification and index substitution logic.
- RotorState: Independent, reusable active state wrapper for a Rotor (position, pointer, stepping).
- Configuration: Configuration loading, normalization, and pre-validation.
- Enigma: Main machine controller orchestrating rotors, plugboard, and encoding/decoding.

Configuration Structure:
----------------------------------------------
{
    "setting": {
        "number_of_rotors": 3,
        "sequence_of_rotor": "r1>r2>r3",  # or ["r1", "r2", "r3"]
        "iteration": 25,
        "rotation_factor": 0,
        "plugs": ["ABCD", ...]
    },
    "characters": [...],
    "r1": [...],
    "r2": [...],
    "r3": [...]
}

Module Contents:
----------------
Classes:
    Enigma: Main machine controller (encoding/decoding)
    Rotor: Reusable rotor wiring specification
    RotorState: Reusable rotor active state (position & pointer)
    Plug: Reusable single plugboard cycle
    Plugboard: Reusable collection of plugs
    Configuration: Machine configuration manager and validator

Functions:
    - check_type(config): Load and validate configuration from dict, JSON file path, or Path object
    - plug_test(plugs): Validate plugboard cycles for repeated characters and conflicts
    - rotor_test(n, rotor): Validate rotor wiring as a proper permutation of n character indices
    - pretest(file): Comprehensive configuration validation including rotors, plugs, and characters

Exceptions:
    EnigmaError, ConfigurationError, InvalidCharacterError, ValidationError

Usage Example:
-------------
    >>> from Enigma import Enigma, Rotor, RotorState, Plug, Plugboard
    >>> enigma = Enigma("configure.json")
    >>> encoded = enigma.encode("HELLO")
    >>> decoded = Enigma("configure.json").decode(encoded)
    >>> print(decoded)  # 'HELLO'
"""

import json
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Union, Optional, Tuple, Iterator, Any, Set

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


# Exception hierarchy
class EnigmaError(Exception):
    """Base exception for all Enigma machine errors."""
    pass


class ConfigurationError(EnigmaError):
    """Raised when there are issues loading or parsing configuration files or dictionaries."""
    pass


class ValidationError(EnigmaError):
    """Raised when configuration validation fails."""
    pass


class InvalidCharacterError(EnigmaError):
    """Raised when a character is not in the configured character set."""
    pass


@dataclass
class InvalidValue:
    """
    Holds detailed information about an invalid value discovered during validation.
    
    Attributes:
        field (str): Name of the field or component that failed validation.
        message (str): Explanation of the validation failure.
        extra_info (Optional[Any]): Additional context or conflicting data.
    """
    field: str
    message: str
    extra_info: Optional[Any] = None


# ============================================================================
# Reusable Component: Plug & Plugboard
# ============================================================================

class Plug:
    """
    Reusable component representing a single plugboard cycle.
    Swaps characters cyclically before and after rotor processing.
    """
    def __init__(self, plug_cycle: str) -> None:
        """
        Initialize the plugboard cycle with O(1) lookup tables.
        
        Args:
            plug_cycle (str): String representing the cycle (e.g., "ABCD").
            
        Raises:
            ValidationError: If cycle contains duplicate characters or is empty.
        """
        errors = list(self.test(plug_cycle))
        if errors:
            raise ValidationError(f"Invalid plug cycle '{plug_cycle}': {errors[0].message}")

        self.plug_cycle = plug_cycle
        self.elements: Set[str] = set(plug_cycle)
        n = len(plug_cycle)

        # Forward mapping: char -> next char in cycle
        self._f_map: Dict[str, str] = {plug_cycle[i]: plug_cycle[(i + 1) % n] for i in range(n)} if n > 0 else {}
        # Backward mapping: char -> previous char in cycle
        self._b_map: Dict[str, str] = {plug_cycle[i]: plug_cycle[(i - 1) % n] for i in range(n)} if n > 0 else {}

    def fplug(self, character: str) -> str:
        """Swap character using the plugboard cycle in forward direction in O(1) time."""
        return self._f_map.get(character, character)

    def bplug(self, character: str) -> str:
        """Swap character using the plugboard cycle in backward direction in O(1) time."""
        return self._b_map.get(character, character)

    def isplug(self, character: str) -> bool:
        """Check if character is part of this plugboard cycle."""
        return character in self.elements

    @staticmethod
    def test(cycle: str) -> Iterator[InvalidValue]:
        """Validate a plugboard cycle for repeated characters or invalid structure."""
        if not isinstance(cycle, str):
            yield InvalidValue(field="Plug", message="Plug cycle must be a string", extra_info=cycle)
            return
        if len(cycle) == 0:
            yield InvalidValue(field="Plug", message="Plug cycle cannot be empty")
            return
        unique_chars = set(cycle)
        if len(unique_chars) != len(cycle):
            duplicates = [char for char in unique_chars if cycle.count(char) > 1]
            yield InvalidValue(field="Plug", message="Duplicate characters found in plugboard cycle", extra_info=duplicates)

    def __repr__(self) -> str:
        return f"Plug('{self.plug_cycle}')"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Plug):
            return self.plug_cycle == other.plug_cycle
        return False


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

    @staticmethod
    def test(plugs: List[Union[Plug, str]]) -> Iterator[InvalidValue]:
        """Validate a list of plug cycles for internal duplicates and cross-cycle conflicts."""
        seen_chars: Set[str] = set()
        for item in plugs:
            cycle_str = item.plug_cycle if isinstance(item, Plug) else item
            for err in Plug.test(cycle_str):
                yield err
            for char in cycle_str:
                if char in seen_chars:
                    yield InvalidValue(
                        field="plugs",
                        message=f"Character '{char}' appears in multiple plug cycles",
                        extra_info=char
                    )
                seen_chars.add(char)

    def __repr__(self) -> str:
        return f"Plugboard(plugs={[p.plug_cycle for p in self.plugs]})"


# ============================================================================
# Reusable Component: Rotor & RotorState
# ============================================================================

class Rotor:
    """
    Reusable component representing an immutable rotor wiring specification.
    Stateless with respect to machine position/stepping.
    """
    def __init__(self, wiring: List[int], size: Optional[int] = None, name: Optional[str] = None) -> None:
        """
        Initialize the Rotor with wiring indices.
        
        Args:
            wiring (List[int]): Permutation of indices from 0 to size-1.
            size (Optional[int]): Total size of character set. Inferred from wiring length if None.
            name (Optional[str]): Optional descriptive name (e.g., 'r1').
            
        Raises:
            ValidationError: If wiring is not a valid permutation.
        """
        self.size = size if size is not None else len(wiring)
        self.name = name or "Rotor"

        errors = list(self.test(wiring, self.size))
        if errors:
            raise ValidationError(f"Invalid rotor wiring for '{self.name}': {errors[0].message}")

        self.rotor = list(wiring)
        self.reverse_rotor = [0] * self.size
        for i, val in enumerate(self.rotor):
            self.reverse_rotor[val] = i

    def fcode(self, n: int, pointer: int = 0) -> int:
        """Forward encoding of character index n given current pointer offset."""
        input_index = (n + pointer) % self.size
        output_shifted = self.rotor[input_index]
        return (output_shifted - pointer) % self.size

    def bcode(self, n: int, pointer: int = 0) -> int:
        """Backward encoding of character index n given current pointer offset."""
        input_shifted = (n + pointer) % self.size
        output_shifted = self.reverse_rotor[input_shifted]
        return (output_shifted - pointer) % self.size

    @staticmethod
    def test(rotor: List[int], size: int) -> Iterator[InvalidValue]:
        """Validate rotor wiring as a valid permutation of 0 to size-1."""
        if not isinstance(rotor, list):
            yield InvalidValue(field="Rotor", message="Rotor wiring must be a list of integers")
            return
        if len(rotor) != size:
            yield InvalidValue(
                field="Rotor",
                message=f"Rotor wiring length ({len(rotor)}) does not match character set size ({size})"
            )
            return

        expected_indices = set(range(size))
        rotor_set = set(rotor)
        extra_elements = list(rotor_set - expected_indices)
        missing_elements = list(expected_indices - rotor_set)

        if extra_elements:
            yield InvalidValue(field="Rotor", message="Extra elements found in rotor wiring", extra_info=extra_elements)
        if missing_elements:
            yield InvalidValue(field="Rotor", message="Missing elements found in rotor wiring", extra_info=missing_elements)

    def __repr__(self) -> str:
        return f"Rotor(name='{self.name}', size={self.size})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Rotor):
            return self.rotor == other.rotor and self.size == other.size
        return False


class RotorState:
    """
    Reusable component encapsulating the active state of a Rotor inside an Enigma machine.
    Manages pointer position, stepping, and delegates index mappings to the underlying Rotor object.
    """
    def __init__(
        self,
        rotor: Rotor,
        position: int = 0,
        pointer: int = 0,
        rotation_base: int = 0,
        name: Optional[str] = None
    ) -> None:
        """
        Initialize RotorState.
        
        Args:
            rotor (Rotor): Reusable Rotor object.
            position (int): Rotor position index (0 = rightmost/fastest rotor).
            pointer (int): Initial pointer offset (0 <= pointer < rotor.size).
            rotation_base (int): Base value for stepping calculation.
            name (Optional[str]): Optional name for this rotor state instance.
        """
        self.rotor = rotor
        self.position = position
        self.rotation_base = rotation_base if rotation_base > 0 else rotor.size
        self.size = rotor.size
        self.name = name or rotor.name
        self.pointer = pointer % self.size

    def rotate(self, steps: int = 1) -> None:
        """Advance rotor pointer by steps."""
        self.pointer = (self.pointer + steps) % self.size

    def update_pointer(self, iteration: int, rotation_base: Optional[int] = None) -> None:
        """
        Update pointer based on iteration count and position using base-N stepping math.
        
        Formula: pointer = (iteration // (rotation_base ** position)) % size
        """
        base = rotation_base if (rotation_base and rotation_base > 0) else self.rotation_base
        divisor = base ** self.position
        self.pointer = (iteration // divisor) % self.size

    def fcode(self, n: int) -> int:
        """Forward encoding through the underlying rotor at current pointer."""
        return self.rotor.fcode(n, self.pointer)

    def bcode(self, n: int) -> int:
        """Backward encoding through the underlying rotor at current pointer."""
        return self.rotor.bcode(n, self.pointer)

    def reset(self, pointer: int = 0) -> None:
        """Reset pointer to specified value."""
        self.pointer = pointer % self.size

    def __repr__(self) -> str:
        return f"RotorState(name='{self.name}', position={self.position}, pointer={self.pointer})"


# ============================================================================
# Configuration Handling & Validation
# ============================================================================

class Configuration:
    """
    Data structure for loading, parsing, and validating Enigma machine configuration.
    """
    def __init__(self, config: Union[dict, str, Path]) -> None:
        """
        Initialize Configuration from a dictionary or JSON file path.
        
        Args:
            config (Union[dict, str, Path]): Config dict or file path.
        """
        if isinstance(config, Configuration):
            self.raw_config = config.raw_config
            self._load_from_dict(self.raw_config)
        elif isinstance(config, dict):
            self.raw_config = config
            self._load_from_dict(config)
        elif isinstance(config, (str, Path)):
            self.raw_config = self._read_json_file(config)
            self._load_from_dict(self.raw_config)
        else:
            raise TypeError("Config must be a dict, Path, str, or Configuration object.")

    @staticmethod
    def _read_json_file(file_path: Union[str, Path]) -> dict:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise ConfigurationError(f"Configuration file not found: {file_path}")
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in configuration file '{file_path}': {e}")
        except Exception as e:
            raise ConfigurationError(f"Error reading configuration file '{file_path}': {e}")

    def _load_from_dict(self, config: dict) -> None:
        # Perform comprehensive pretest
        errors = list(pretest(config, raise_on_error=False))
        if errors:
            error_msgs = [f"{err.field}: {err.message}" for err in errors]
            raise ValidationError("Configuration validation failed:\n" + "\n".join(error_msgs))

        try:
            self.characters = config["characters"]
            setting = config["setting"]
            
            # Normalize sequence_of_rotor: could be "r1>r2>r3" or ["r1", "r2", "r3"]
            seq = setting["sequence_of_rotor"]
            if isinstance(seq, str):
                self.sequence_of_rotor = seq.split(">")
            elif isinstance(seq, list):
                self.sequence_of_rotor = seq
            else:
                raise ConfigurationError("sequence_of_rotor must be a string (e.g. 'r1>r2') or list of strings")

            self.number_of_rotors = setting.get("number_of_rotors", len(self.sequence_of_rotor))
            self.iteration = setting["iteration"]
            self.rotation_factor = setting["rotation_factor"]
            self.plugs = setting["plugs"]
            self.rotors: Dict[str, List[int]] = {key: config[key] for key in self.sequence_of_rotor}
            self.number_of_characters = len(self.characters)
        except KeyError as e:
            raise ConfigurationError(f"Missing required configuration field: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading configuration: {e}")

    @staticmethod
    def metadata(config: dict) -> Iterator[InvalidValue]:
        """Validate metadata fields in configuration dictionary."""
        if not isinstance(config, dict):
            yield InvalidValue(field="config", message="Configuration must be a dictionary")
            return

        if "characters" not in config or not config["characters"]:
            yield InvalidValue(field="characters", message="Character list is missing or empty")

        if "setting" not in config or not isinstance(config["setting"], dict):
            yield InvalidValue(field="setting", message="'setting' dictionary missing from configuration")
            return

        setting = config["setting"]
        for required_key in ["sequence_of_rotor", "iteration", "rotation_factor", "plugs"]:
            if required_key not in setting:
                yield InvalidValue(field=f"setting.{required_key}", message=f"Missing setting key '{required_key}'")

        seq = setting.get("sequence_of_rotor")
        if isinstance(seq, str):
            rotor_names = seq.split(">")
        elif isinstance(seq, list):
            rotor_names = seq
        else:
            rotor_names = []
            yield InvalidValue(field="setting.sequence_of_rotor", message="Invalid sequence_of_rotor format")

        for rname in rotor_names:
            if rname not in config:
                yield InvalidValue(field=rname, message=f"Rotor configuration for '{rname}' missing from config")

    @staticmethod
    def character_list_test(characters: List[str]) -> Iterator[InvalidValue]:
        """Validate character list for duplicates and valid single-char elements."""
        if not isinstance(characters, list):
            yield InvalidValue(field="characters", message="Characters must be a list")
            return

        unique_characters = set(characters)
        if len(characters) != len(unique_characters):
            duplicates = [char for char in unique_characters if characters.count(char) > 1]
            yield InvalidValue(field="characters", message="Duplicate characters found", extra_info=duplicates)

        non_single_chars = [char for char in characters if not isinstance(char, str) or len(char) != 1]
        if non_single_chars:
            yield InvalidValue(field="characters", message="Non-single character elements found", extra_info=non_single_chars)

    @staticmethod
    def plug_test(plugs: List[str]) -> Iterator[InvalidValue]:
        """Validate plugboard configuration."""
        yield from Plugboard.test(plugs)

    @staticmethod
    def rotor_test(n: int, rotors: Dict[str, List[int]]) -> Iterator[InvalidValue]:
        """Validate all rotors in dictionary against size n."""
        for rname, wiring in rotors.items():
            yield from Rotor.test(wiring, n)

    def add_rotor(
        self,
        name: str,
        wiring: Union[List[int], Rotor],
        add_to_sequence: bool = True,
        position: Optional[int] = None
    ) -> Rotor:
        """
        Directly add a rotor to the configuration.
        
        Args:
            name (str): Name/identifier of the rotor (e.g. 'r4').
            wiring (Union[List[int], Rotor]): Permutation array of indices or a Rotor instance.
            add_to_sequence (bool): Whether to include this rotor in sequence_of_rotor. Defaults to True.
            position (Optional[int]): Position in sequence to insert rotor. Defaults to end.
            
        Returns:
            Rotor: The instantiated reusable Rotor object.
            
        Raises:
            ValidationError: If rotor wiring fails validation.
        """
        if isinstance(wiring, Rotor):
            rotor_obj = wiring
            wiring_list = rotor_obj.rotor
            if rotor_obj.size != self.number_of_characters:
                raise ValidationError(
                    f"Rotor size ({rotor_obj.size}) does not match character set size ({self.number_of_characters})"
                )
        else:
            wiring_list = list(wiring)
            rotor_obj = Rotor(wiring_list, size=self.number_of_characters, name=name)

        self.rotors[name] = wiring_list
        self.raw_config[name] = wiring_list

        if add_to_sequence:
            if name in self.sequence_of_rotor:
                self.sequence_of_rotor.remove(name)
            if position is None or position >= len(self.sequence_of_rotor):
                self.sequence_of_rotor.append(name)
            else:
                self.sequence_of_rotor.insert(position, name)

            self.number_of_rotors = len(self.sequence_of_rotor)
            self.raw_config["setting"]["sequence_of_rotor"] = ">".join(self.sequence_of_rotor)
            self.raw_config["setting"]["number_of_rotors"] = self.number_of_rotors

        return rotor_obj

    def to_dict(self) -> dict:
        """Return the configuration dictionary representation."""
        return self.raw_config

    def save(self, file_path: Union[str, Path]) -> None:
        """Save configuration dictionary to a JSON file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.raw_config, f, indent=4)


def pretest(config: Union[dict, str, Path], raise_on_error: bool = False) -> List[InvalidValue]:
    """
    Comprehensive configuration validation.
    
    Args:
        config (Union[dict, str, Path]): Configuration dict or file path.
        raise_on_error (bool): If True, raises ValidationError when errors are found.
        
    Returns:
        List[InvalidValue]: List of validation errors encountered.
    """
    if isinstance(config, (str, Path)):
        try:
            with open(config, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception as e:
            err = InvalidValue(field="file", message=f"Failed to load JSON configuration file: {e}")
            if raise_on_error:
                raise ValidationError(err.message)
            return [err]

    errors: List[InvalidValue] = []

    # Run checks
    errors.extend(Configuration.metadata(config))
    if "characters" in config and isinstance(config["characters"], list):
        errors.extend(Configuration.character_list_test(config["characters"]))
        n = len(config["characters"])
    else:
        n = 0

    if "setting" in config and isinstance(config["setting"], dict):
        plugs = config["setting"].get("plugs", [])
        if isinstance(plugs, list):
            errors.extend(Configuration.plug_test(plugs))

        seq = config["setting"].get("sequence_of_rotor")
        rotor_names = []
        if isinstance(seq, str):
            rotor_names = seq.split(">")
        elif isinstance(seq, list):
            rotor_names = seq

        if n > 0:
            for rname in rotor_names:
                if rname in config and isinstance(config[rname], list):
                    errors.extend(Rotor.test(config[rname], n))

    if errors and raise_on_error:
        for err in errors:
            logger.error(f"Validation error: {err.field} - {err.message} - Extra: {err.extra_info}")
        raise ValidationError("Configuration validation failed. See logs for details.")

    return errors


def check_type(config: Union[dict, str, Path, Configuration]) -> dict:
    """
    Load configuration dict from dict, file path, Path object, or Configuration instance.
    """
    if isinstance(config, Configuration):
        return config.raw_config
    elif isinstance(config, dict):
        return config
    elif isinstance(config, (str, Path)):
        try:
            with open(config, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise ConfigurationError(f"Configuration file not found: {config}")
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in configuration file '{config}': {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading configuration file '{config}': {e}")
    else:
        raise TypeError("Config must be a dict, Path, str, or Configuration object.")


# Backwards compatibility wrappers
def plug_test(plugs: List[str]) -> bool:
    errors = list(Plugboard.test(plugs))
    return len(errors) == 0


def rotor_test(n: int, rotor: Union[List[int], Dict[str, List[int]]]) -> bool:
    if isinstance(rotor, dict):
        errors = list(Configuration.rotor_test(n, rotor))
    else:
        errors = list(Rotor.test(rotor, n))
    return len(errors) == 0


# ============================================================================
# Main Controller: Enigma
# ============================================================================

class Enigma:
    """
    Main Enigma machine class orchestrating rotors, plugboard, and character encoding.
    Decoupled architecture supporting direct injection of reusable component objects.
    """
    def __new__(cls, file_or_config: Optional[Union[str, Path, dict, Configuration]] = None, **kwargs) -> 'Enigma':
        """
        Validate configuration before creating an Enigma instance if configuration file/dict is provided.
        """
        if file_or_config is not None:
            config_dict = check_type(file_or_config)
            pretest(config_dict, raise_on_error=True)

        return super().__new__(cls)

    def __init__(
        self,
        file_or_config: Optional[Union[str, Path, dict, Configuration]] = None,
        *,
        characters: Optional[List[str]] = None,
        rotor_states: Optional[List[RotorState]] = None,
        rotors: Optional[Dict[str, Rotor]] = None,
        sequence: Optional[List[str]] = None,
        plugboard: Optional[Plugboard] = None,
        iteration: int = 0,
        rotation_factor: int = 0
    ) -> None:
        """
        Initialize Enigma machine from a configuration file/dict, OR via direct component injection.
        """
        logger.debug("Initializing Enigma machine components")

        if file_or_config is not None:
            self._init_from_config(file_or_config)
        else:
            self._init_from_components(
                characters=characters,
                rotor_states=rotor_states,
                rotors=rotors,
                sequence=sequence,
                plugboard=plugboard,
                iteration=iteration,
                rotation_factor=rotation_factor
            )

        # Log initialization
        logger.info(
            f"Enigma initialized with {self.number_of_rotors} rotors, "
            f"{len(self.characters)} characters, iteration {self.iteration}"
        )

    def _init_from_config(self, file_or_config: Union[str, Path, dict, Configuration]) -> None:
        """Initialize Enigma instance from configuration dict/file."""
        cfg = Configuration(file_or_config)

        self.characters = cfg.characters
        self.char_to_idx = {char: i for i, char in enumerate(self.characters)}
        self.idx_to_char = {i: char for i, char in enumerate(self.characters)}

        self.number_of_rotors = cfg.number_of_rotors
        self.initial_iteration = cfg.iteration
        self.iteration = cfg.iteration
        self.rotation_factor = cfg.rotation_factor

        num_chars = len(self.characters)
        self.rotation_base = num_chars if cfg.rotation_factor == 0 else cfg.rotation_factor

        # Instantiate reusable Rotor objects
        self.rotors: Dict[str, Rotor] = {}
        for rname, wiring in cfg.rotors.items():
            self.rotors[rname] = Rotor(wiring, size=num_chars, name=rname)

        # Instantiate reusable RotorState objects for active sequence
        self.rotor_states: List[RotorState] = []
        for pos, rname in enumerate(cfg.sequence_of_rotor):
            rotor_obj = self.rotors[rname]
            rstate = RotorState(
                rotor=rotor_obj,
                position=pos,
                rotation_base=self.rotation_base,
                name=rname
            )
            rstate.update_pointer(self.iteration, self.rotation_base)
            self.rotor_states.append(rstate)

        # Instantiate reusable Plugboard
        self.plugboard = Plugboard(cfg.plugs)

    def _init_from_components(
        self,
        characters: Optional[List[str]],
        rotor_states: Optional[List[RotorState]],
        rotors: Optional[Dict[str, Rotor]],
        sequence: Optional[List[str]],
        plugboard: Optional[Plugboard],
        iteration: int,
        rotation_factor: int
    ) -> None:
        """Initialize Enigma instance via direct component injection."""
        if not characters:
            raise ValidationError("Character set must be provided when initializing Enigma directly.")

        self.characters = list(characters)
        self.char_to_idx = {char: i for i, char in enumerate(self.characters)}
        self.idx_to_char = {i: char for i, char in enumerate(self.characters)}
        num_chars = len(self.characters)

        self.initial_iteration = iteration
        self.iteration = iteration
        self.rotation_factor = rotation_factor
        self.rotation_base = num_chars if rotation_factor == 0 else rotation_factor

        self.plugboard = plugboard or Plugboard()

        if rotor_states is not None:
            self.rotor_states = list(rotor_states)
            self.number_of_rotors = len(self.rotor_states)
            self.rotors = {rstate.name: rstate.rotor for rstate in self.rotor_states}
            for pos, rstate in enumerate(self.rotor_states):
                rstate.position = pos
                rstate.rotation_base = self.rotation_base
                rstate.update_pointer(self.iteration, self.rotation_base)
        elif rotors is not None and sequence is not None:
            self.rotors = dict(rotors)
            self.rotor_states = []
            for pos, rname in enumerate(sequence):
                rotor_obj = self.rotors[rname]
                rstate = RotorState(
                    rotor=rotor_obj,
                    position=pos,
                    rotation_base=self.rotation_base,
                    name=rname
                )
                rstate.update_pointer(self.iteration, self.rotation_base)
                self.rotor_states.append(rstate)
            self.number_of_rotors = len(self.rotor_states)
        else:
            raise ValidationError("Either rotor_states or (rotors + sequence) must be provided.")

    def step_rotors(self) -> None:
        """Advance machine iteration and update rotor pointers."""
        self.iteration += 1
        for rstate in self.rotor_states:
            rstate.update_pointer(self.iteration, self.rotation_base)

    def main(self, char: str) -> str:
        """
        Encode/Decode a single character using the Enigma machine logic and step the machine.
        
        Args:
            char (str): Character to encode or decode.
            
        Returns:
            str: Encoded or decoded character.
            
        Raises:
            InvalidCharacterError: If character is not in configured character set.
        """
        if char not in self.char_to_idx:
            logger.error(f"Invalid character '{char}' not in character set")
            raise InvalidCharacterError(f"Character '{char}' is not in the configured character set")

        # 1. Plugboard forward mapping
        c1 = self.plugboard.fplug(char)

        # 2. Convert character to index
        idx = self.char_to_idx[c1]

        # 3. Pass forward through rotor states (from position 0 to N-1)
        for rstate in self.rotor_states:
            idx = rstate.fcode(idx)

        # 4. Reflector pass (reverses signal)
        idx = (len(self.characters) - 1) - idx

        # 5. Pass backward through rotor states (from position N-1 down to 0)
        for rstate in reversed(self.rotor_states):
            idx = rstate.bcode(idx)

        # 6. Convert index back to character
        c2 = self.idx_to_char[idx]

        # 7. Plugboard backward mapping
        final_char = self.plugboard.bplug(c2)

        # 8. Step rotors for next character
        self.step_rotors()

        return final_char

    def encode(self, text: str) -> str:
        """Encode an entire text string."""
        return ''.join(self.main(c) for c in text)

    def decode(self, text: str) -> str:
        """Decode an entire text string (alias for encode)."""
        return self.encode(text)

    def reset(self, iteration: Optional[int] = None) -> None:
        """Reset machine iteration and rotor pointers."""
        target_iter = iteration if iteration is not None else self.initial_iteration
        self.iteration = target_iter
        for rstate in self.rotor_states:
            rstate.update_pointer(self.iteration, self.rotation_base)

    def add_rotor(
        self,
        rotor_or_wiring: Union[Rotor, List[int]],
        name: Optional[str] = None,
        add_to_sequence: bool = True,
        position: Optional[int] = None
    ) -> RotorState:
        """
        Directly add a rotor to the Enigma machine instance.
        
        Args:
            rotor_or_wiring (Union[Rotor, List[int]]): A Rotor object or wiring list.
            name (Optional[str]): Name of the rotor. Required if rotor_or_wiring is a list.
            add_to_sequence (bool): Whether to activate rotor in active sequence.
            position (Optional[int]): Position in sequence to insert. Defaults to appending at end.
            
        Returns:
            RotorState: The created RotorState object for the active sequence.
        """
        if isinstance(rotor_or_wiring, Rotor):
            rotor_obj = rotor_or_wiring
            rotor_name = name or rotor_obj.name
            if rotor_obj.size != len(self.characters):
                raise ValidationError(
                    f"Rotor size ({rotor_obj.size}) does not match character set size ({len(self.characters)})"
                )
        elif isinstance(rotor_or_wiring, list):
            rotor_name = name or f"r{len(self.rotors) + 1}"
            rotor_obj = Rotor(rotor_or_wiring, size=len(self.characters), name=rotor_name)
        else:
            raise TypeError("rotor_or_wiring must be a Rotor object or a list of integer wiring indices.")

        self.rotors[rotor_name] = rotor_obj
        rstate = RotorState(rotor=rotor_obj, name=rotor_name)

        if add_to_sequence:
            if position is None or position >= len(self.rotor_states):
                self.rotor_states.append(rstate)
            else:
                self.rotor_states.insert(position, rstate)

            self._refresh_rotor_states()

        return rstate

    def _refresh_rotor_states(self) -> None:
        """Re-index rotor positions and update pointers for active rotor sequence."""
        self.number_of_rotors = len(self.rotor_states)
        for pos, rstate in enumerate(self.rotor_states):
            rstate.position = pos
            rstate.rotation_base = self.rotation_base
            rstate.update_pointer(self.iteration, self.rotation_base)
