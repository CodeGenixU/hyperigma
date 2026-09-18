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

from components.configuration.configuration import Configuration
from components.mechanism.axle import Axle
# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


# Exception hierarchy










class Enigma:
    """
    Main Enigma machine class orchestrating rotors, plugboard, and character encoding.
    Decoupled architecture supporting direct injection of reusable component objects.
    """

    def __init__(
        self,
        config: Configuration = None
    ) -> None:
        """
        Initialize Enigma machine from a configuration file/dict, OR via direct component injection.
        """
        logger.debug("Initializing Enigma machine components")

        if config is None:
            raise ValueError("Configuration must be provided to initialize Enigma")

        self.characterset = config.characters
        self.plugboard = config.plugboard
        self.shaft = config.shaft
        self.pointer = config.iteration
        self.size = self.characterset.size
        self.axle = Axle(self.shaft)

        # Log initialization
        logger.info(f"Enigma initialized")

    def reflector(self, index: int) -> int:
        """
        Reflector logic: reverses the signal by mapping index to its complement.
        """
        return (self.size - 1) - index
    
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
        
        # 1. Plugboard forward mapping
        c1 = self.plugboard.fplug(char)
        #print(f"Plugboard forward mapping: {char} -> {c1}")

        # 2. Convert character to index
        idx = self.characterset.fcode(c1)
        #print(f"Character to index: {c1} -> {idx}")

        # 3. Pass forward through rotor states (from position 0 to N-1)
        r1 = self.axle.fcode(idx)
        #print(f"Forward rotor mapping: {idx} -> {r1}")

        # 4. Reflector pass (reverses signal)
        refl = self.reflector(r1)
        #print(f"Reflector mapping: {r1} -> {refl}")

        # 5. Pass backward through rotor states (from position N-1 down to 0)
        r2 = self.axle.bcode(refl)
        #print(f"Backward rotor mapping: {refl} -> {r2}")

        # 6. Convert index back to character
        c2 = self.characterset.bcode(r2)
        #print(f"Index to character: {r2} -> {c2}")

        # 7. Plugboard backward mapping
        final_char = self.plugboard.bplug(c2)
        #print(f"Plugboard backward mapping: {c2} -> {final_char}")

        self.pointer += 1  # Increment pointer for next character
        # 8. Step rotors for next character
        self.axle.rotate(self.pointer)

        return final_char

    def encode(self, text: str) -> str:
        """Encode an entire text string."""
        return ''.join(self.main(c) for c in text)

    def decode(self, text: str) -> str:
        """Decode an entire text string (alias for encode)."""
        return self.encode(text)
    
if __name__ == "__main__":
    # Example usage
    config = Configuration("configure.json")
    enigma1 = Enigma(config)
    enigma2 = Enigma(config)  # Separate instance for decoding    
    message = "HELLOWORLD1234564Ukar"
    encoded_message = enigma1.encode(message)
    decoded_message = enigma2.decode(encoded_message)
    print(f"Original: {message}, Encoded: {encoded_message}, Decoded: {decoded_message}")