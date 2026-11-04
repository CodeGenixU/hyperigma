"""Load, validate, and assemble Enigma machine configuration."""

from typing import List, Dict, Union, Optional
import json
from pathlib import Path

from ..exceptions import (
    CharacterSetValidationError,
    ConfigurationLoadError,
    ConfigurationValidationError,
    PlugboardValidationError,
    ShaftValidationError,
)
from ..DTO.invalid_values import InvalidValue

from ..character.character_set import CharacterSet
from ..mechanism.shaft import Shaft
from ..plug.plugboard import Plugboard

SCHEMA = {
    "characters": List[str],
    "plugs": List[str],
    "rotors": Dict[str, List[int]],
    "setting": {
        "sequence": List[str],
        "iteration": int,
        "factor": int,
    },
}


class Configuration:
    """
    Data structure for loading, parsing, and validating Enigma machine configuration.
    """
    def __init__(self, config: Optional[Union[dict, str, Path]] = None) -> None:
        """
        Initialize Configuration from a dictionary or JSON file path.
        
        Args:
            config (Union[dict, str, Path]): Config dict or file path.
        """
        
        self.characters: CharacterSet = None   
        self.plugboard: Plugboard = None
        self.shaft: Shaft = None

        self.iteration: int = None
        self.factor: int = None
        
        self.size: int = None

        if config is not None:
            if isinstance(config, dict):
                self._load_from_dict(config)
            elif isinstance(config, (str, Path)):
                self._load_from_dict(self._read_json_file(config))
            else:
                raise TypeError("Config must be a dict, Path or str.")

    @staticmethod
    def _read_json_file(file_path: Union[str, Path]) -> dict:
        """Read a JSON configuration file.

        Args:
            file_path: Path to the JSON configuration file.

        Returns:
            The decoded configuration dictionary.

        Raises:
            ConfigurationError: If the file cannot be read or decoded.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise ConfigurationLoadError(f"Configuration file not found: {file_path}")
        except json.JSONDecodeError as e:
            raise ConfigurationLoadError(
                f"Invalid JSON in configuration file '{file_path}' "
                f"(line {e.lineno}, column {e.colno})"
            ) from e
        except OSError as e:
            raise ConfigurationLoadError(f"Could not read configuration file '{file_path}': {e}") from e

    def _load_from_dict(self, config: dict) -> None:
        """Load and validate configuration data from a dictionary.

        Args:
            config: Configuration dictionary to load.

        Raises:
            ValidationError: If any configuration component is invalid.
        """
        # Perform comprehensive pretest
        
        errors = []
        errors.extend(Configuration.schemaValidate(config))
        if errors:
            raise ConfigurationValidationError("Invalid configuration", errors=errors)

        self.factor = config["setting"]["factor"]
        self.iteration = config["setting"]["iteration"]

        errors.extend(CharacterSet.test(config["characters"]))
        if errors:
            raise CharacterSetValidationError("Invalid character set", errors=errors)
        else :
            self.add_characters(CharacterSet(config["characters"]))


        errors.extend(Plugboard.test(config["plugs"]))
        if errors:
            raise PlugboardValidationError("Invalid plugboard", errors=errors)
        else:
            self.add_plugboard(Plugboard(config["plugs"]))

        errors.extend(Shaft.test(self.size, config["setting"]["sequence"], config["rotors"]))
        if errors:
            raise ShaftValidationError("Invalid rotor assembly", errors=errors)
        else:
            self.add_shaft(Shaft(self.size, config["setting"]["sequence"], config["rotors"]))

    @staticmethod
    def schemaValidate(config: dict) -> List[InvalidValue]:
            """Validate a configuration dictionary against the expected schema.

            Args:
                config: Configuration dictionary to validate.

            Returns:
                Validation errors, or an empty list when valid.
            """
    
            errors = []

            required_keys = ["characters", "rotors", "setting", "plugs"]
            required_setting_keys = ["sequence", "iteration", "factor"]
            
            if not isinstance(config, dict):
                errors.append(InvalidValue(
                    field="config",
                    code="invalid_type",
                    message="Configuration must be a dictionary",
                ))
                return errors
    
            # Check for required top-level keys
            for key in required_keys:
                if key not in config:
                    errors.append(InvalidValue(
                        field=key,
                        code="missing_key",
                        message=f"Missing required key '{key}'",
                    ))
            if errors:
                return errors

            rotors = config.get("rotors")
            if not isinstance(rotors, dict):
                errors.append(InvalidValue(
                    field="rotors",
                    code="invalid_type",
                    message="'rotors' must be a dictionary",
                ))
                        
            # Validate 'setting' structure
            setting = config.get("setting")
            if not isinstance(setting, dict):
                errors.append(InvalidValue(
                    field="setting",
                    code="invalid_type",
                    message="'setting' must be a dictionary",
                ))
            else:
                for s_key in required_setting_keys:
                    if s_key not in setting:
                        errors.append(InvalidValue(
                            field=f"setting.{s_key}",
                            code="missing_key",
                            message=f"Missing setting key '{s_key}'",
                        ))
                    elif s_key == "iteration" and not isinstance(setting[s_key], int):
                        errors.append(InvalidValue(
                            field="setting.iteration",
                            code="invalid_type",
                            message="'iteration' must be an integer",
                        ))
                    elif s_key == "factor" and not isinstance(setting[s_key], int):
                        errors.append(InvalidValue(
                            field="setting.factor",
                            code="invalid_type",
                            message="'factor' must be an integer",
                        ))
                    elif s_key == "sequence" and not isinstance(setting[s_key], (list, tuple)):
                        errors.append(InvalidValue(
                            field="setting.sequence",
                            code="invalid_type",
                            message="'sequence' must be a list",
                        ))
                
                sequence = setting.get("sequence")
                if not isinstance(sequence, (list, tuple)) or not all(isinstance(i, str) for i in sequence):
                    errors.append(InvalidValue(
                        field="setting.sequence",
                        code="invalid_type",
                        message="'sequence' must be a list",
                    ))
                elif isinstance(rotors, dict):
                    for i in sequence:
                        if i not in rotors:
                            errors.append(InvalidValue(
                                field=f"setting.sequence[{i}]",
                                code="unknown_rotor",
                                message=f"Rotor '{i}' not defined in 'rotors'",
                            ))
                        else:
                            wiring = rotors.get(i)
                            if not isinstance(wiring, (list, tuple)) or not all(isinstance(j, int) for j in wiring):
                                errors.append(InvalidValue(
                                    field=f"rotors.{i}",
                                    code="invalid_type",
                                    message="Rotor wiring must be a list of integers",
                                ))
                
            characters = config.get("characters")
            if not isinstance(characters, (list, tuple)) or not all(True if isinstance(i, str) and len(i) == 1 else False for i in characters):
                errors.append(InvalidValue(
                    field="characters",
                    code="invalid_type",
                    message="'characters' must be a list of single character strings",
                ))
            
                        
            
            plugs = config.get("plugs")
            if not isinstance(plugs, (list, tuple)) or not all(isinstance(i, str) for i in plugs):
                errors.append(InvalidValue(
                    field="plugs",
                    code="invalid_type",
                    message="'plugs' must be a list of strings",
                ))
            
                        
            return errors

    def add_characters(self,character: CharacterSet) -> None:
        """Add a character set to the configuration.

        Args:
            character: Character set to add.
        """
        if not isinstance(character, CharacterSet):
            raise CharacterSetValidationError(
                "Invalid character set",
                errors=[InvalidValue(
                    field="characters",
                    code="invalid_type",
                    message="Expected a CharacterSet instance",
                )],
            )
        self.characters = character
        self.size = len(character)

    def add_plugboard(self,plugboard: Plugboard) -> None:
        """Add a plugboard to the configuration.

        Args:
            plugboard: Plugboard to add.
        """
        if self.characters is None:
            raise PlugboardValidationError(
                "Invalid plugboard",
                errors=[InvalidValue(
                    field="characters",
                    code="missing_dependency",
                    message="CharacterSet must be set before adding a plugboard",
                )],
            )
        if self.plugboard is not None:
            raise PlugboardValidationError(
                "Invalid plugboard",
                errors=[InvalidValue(
                    field="plugboard",
                    code="already_set",
                    message="Plugboard has already been set",
                )],
            )
        if not isinstance(plugboard, Plugboard):
            raise PlugboardValidationError(
                "Invalid plugboard",
                errors=[InvalidValue(
                    field="plugboard",
                    code="invalid_type",
                    message="Expected a Plugboard instance",
                )],
            )
        unknown = set(plugboard.characters()).difference(self.characters.characters)
        if unknown:
            raise PlugboardValidationError(
                "Invalid plugboard",
                errors=[InvalidValue(
                    field="plugs",
                    code="unknown_character",
                    message="Contains characters outside the configured character set",
                    extra_info=sorted(unknown),
                )],
            )
        self.plugboard = plugboard

    def add_shaft(self, shaft: Shaft) -> None:
        """Add a rotor shaft to the configuration.

        Args:
            shaft: Shaft to add.
        """
        if self.characters is None:
                    raise ShaftValidationError(
                        "Invalid rotor shaft",
                        errors=[InvalidValue(
                            field="characters",
                            code="missing_dependency",
                            message="CharacterSet must be set before adding a shaft",
                        )],
                    )
        if self.shaft is not None:
            raise ShaftValidationError(
                "Invalid rotor shaft",
                errors=[InvalidValue(
                    field="shaft",
                    code="already_set",
                    message="Shaft has already been set",
                )],
            )
        if not isinstance(shaft, Shaft):
                    raise ShaftValidationError(
                        "Invalid rotor shaft",
                        errors=[InvalidValue(
                            field="shaft",
                            code="invalid_type",
                            message="Expected a Shaft instance",
                        )],
                    )
        if shaft.size != self.size:
            raise ShaftValidationError(
                "Invalid rotor assembly",
                errors=[InvalidValue(
                    field="rotors",
                    code="size_mismatch",
                    message=f"Rotor size {shaft.size} does not match character set size {self.size}",
                )],
            )
        self.shaft = shaft

    def validate(self) -> bool:
        """Validate that all required components are configured.

        Returns:
            True when the configuration is complete and valid.
        """

        if self.characters is None or isinstance(self.characters, CharacterSet) == False:
            return False
        if self.plugboard is None or isinstance(self.plugboard, Plugboard) == False:
            return False
        if self.shaft is None or isinstance(self.shaft, Shaft) == False:
            return False
        if isinstance(self.iteration, int) == False or isinstance(self.factor, int) == False:
            return False
        return True
