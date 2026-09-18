from typing import List, Dict, Union, Optional, Iterator
import json
from pathlib import Path

from ..exceptions import ConfigurationError, ValidationError
from ..DTO.invalid_values import InvalidValue

from ..rotor.rotor import Rotor
from ..rotor.rotor_state import RotorState
from ..plug.plug import Plug
from ..character.character_set import CharacterSet
from ..mechanism.shaft import Shaft
from ..mechanism.axle import Axle
from ..plug.plugboard import Plugboard

SCHEMA = {
    "characters": List[str],
    "plugs": List[str],
    "rotors": Dict[str, List[int]],
    "setting": {
        "sequence_of_rotor": List[str],
        "iteration": int,
        "rotation_factor": int,
    },
}

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
        if isinstance(config, dict):
            self.raw_config = config
            self._load_from_dict(config)
        elif isinstance(config, (str, Path)):
            self.raw_config = self._read_json_file(config)
            self._load_from_dict(self.raw_config)
        else:
            raise TypeError("Config must be a dict, Path or str.")

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
        errors = []
        errors.extend(self.schemaValidate(config))
        if errors:
            error_msgs = [f"{err.field}: {err.message}" for err in errors]
            raise ValidationError("Configuration validation failed:\n" + "\n".join(error_msgs))
        errors.extend(self.component_validate(config))
        if errors:
            error_msgs = [f"{err.field}: {err.message}" for err in errors]
            raise ValidationError("Configuration validation failed:\n" + "\n".join(error_msgs))

        try:
            self.characters = CharacterSet(config["characters"])   
            self.number_of_characters = len(self.characters)
            self.plugboard = Plugboard(config["plugs"])
            setting = config["setting"]
            self.sequence_of_rotor = setting["sequence_of_rotor"]
            self.iteration = setting["iteration"]
            self.rotation_factor = setting["rotation_factor"]
            self.rotors: Dict[str, List[int]] = {key: config["rotors"][key] for key in self.sequence_of_rotor}
            self.shaft = Shaft(self.number_of_characters, self.sequence_of_rotor, self.rotors)
        except KeyError as e:
            raise ConfigurationError(f"Missing required configuration field: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading configuration: {e}")

    def schemaValidate(self, config: dict) -> List[InvalidValue]:
        """Validate configuration dictionary against expected schema."""
        errors = []
        if not isinstance(config, dict):
            errors.append(InvalidValue(field="config", message="Configuration must be a dictionary"))
            return errors

        # Check for required top-level keys
        required_keys = ["characters", "rotors", "setting", "plugs"]
        for key in required_keys:
            if key not in config:
                errors.append(InvalidValue(field=key, message=f"Missing required key '{key}'"))

        # Validate 'setting' structure
        setting = config.get("setting", {})
        if not isinstance(setting, dict):
            errors.append(InvalidValue(field="setting", message="'setting' must be a dictionary"))
        else:
            required_setting_keys = ["sequence_of_rotor", "iteration", "rotation_factor"]
            for s_key in required_setting_keys:
                if s_key not in setting:
                    errors.append(InvalidValue(field=f"setting.{s_key}", message=f"Missing setting key '{s_key}'"))

        rotors = config.get("rotors", {})
        if not isinstance(rotors, dict):
            errors.append(InvalidValue(field="rotors", message="'rotors' must be a dictionary"))
        else:
            for wiring in rotors.values():
                if not isinstance(wiring, list):
                    errors.append(InvalidValue(field=f"rotors.{rname}", message="Rotor wiring must be a list of integers"))

        rotor_sequence = setting.get("sequence_of_rotor")
        if not isinstance(rotor_sequence, list):
            errors.append(InvalidValue(field="setting.sequence_of_rotor", message="'sequence_of_rotor' must be a list"))
        else:
            for i in rotor_sequence:
                if i not in rotors:
                    errors.append(InvalidValue(field="setting.sequence_of_rotor", message=f"Rotor '{i}' not defined in 'rotors'"))
                    
        return errors

    @staticmethod
    def character_list_validate(characters: List[str]) -> List[InvalidValue]:
        """Validate character list for duplicates and valid single-char elements."""
        return CharacterSet.test(characters)

    @staticmethod
    def plug_validate(plugs: List[str]) -> Iterator[InvalidValue]:
        """Validate plugboard configuration."""
        return Plug.test(plugs)

    @staticmethod
    def rotor_validate(n: int, rotor: List[int]) -> Iterator[InvalidValue]:
        """Validate all rotors in dictionary against size n."""
        return Rotor.test(rotor, n)

    @staticmethod
    def plugboard_validate(plugs: List[str]) -> List[InvalidValue]:
        """Validate plugboard configuration for duplicates and conflicts."""
        return Plugboard.test(plugs)

    @staticmethod
    def component_validate(config: dict) -> List[InvalidValue]:
        """Validate all components of the configuration."""
        errors = []
        errors.extend(Configuration.character_list_validate(config.get("characters", [])))
        errors.extend(Configuration.plugboard_validate(config.get("plugs", [])))

        n = len(config.get("characters", []))
        rotors = config.get("rotors", {})
        
        
        return errors


    def validate(self) -> List[InvalidValue]:
        """Run comprehensive validation on the configuration."""
        errors = []
        errors.extend(CharacterSet.test(self.characters.characters))
        errors.extend(Plugboard.test(self.plugboard.plugs ))
        for i in self.sequence_of_rotor:
            if i in self.rotors:
                errors.extend(Rotor.test(self.rotors[i], self.number_of_characters))
            else:
                errors.append(InvalidValue(field="rotors", message=f"Rotor '{i}' not defined in configuration"))
        errors.extend(self.component_validate(self.raw_config))
        return errors
