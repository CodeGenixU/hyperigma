from typing import List, Dict, Union, Optional
import json
from pathlib import Path

from ..exceptions import ConfigurationError, ValidationError
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
        errors.extend(Configuration.schemaValidate(config))
        if errors:
            error_msgs = [f"{err.field}: {err.message}" for err in errors]
            raise ValidationError("Configuration validation failed:\n" + "\n".join(error_msgs))

        self.factor = config["setting"]["factor"]
        self.iteration = config["setting"]["iteration"]

        errors.extend(CharacterSet.test(config["characters"]))
        if errors:
            error_msgs = [f"{err.field}: {err.message}" for err in errors]
            raise ValidationError("CharacterSet validation failed:\n" + "\n".join(error_msgs))
        else :
            self.add_characters(CharacterSet(config["characters"]))


        errors.extend(Plugboard.test(config["plugs"]))
        if errors:
            error_msgs = [f"{err.field}: {err.message}" for err in errors]
            raise ValidationError("Plugboard validation failed:\n" + "\n".join(error_msgs))
        else:
            self.add_plugboard(Plugboard(config["plugs"]))

        errors.extend(Shaft.test(self.size, config["setting"]["sequence"], config["rotors"]))
        if errors:
            error_msgs = [f"{err.field}: {err.message}" for err in errors]
            raise ValidationError("Shaft validation failed:\n" + "\n".join(error_msgs))
        else:
            self.add_shaft(Shaft(self.size, config["setting"]["sequence"], config["rotors"]))

    @staticmethod
    def schemaValidate(config: dict) -> List[InvalidValue]:
            """Validate configuration dictionary against expected schema."""
    
            errors = []

            required_keys = ["characters", "rotors", "setting", "plugs"]
            required_setting_keys = ["sequence", "iteration", "factor"]
            
            if not isinstance(config, dict):
                errors.append(InvalidValue(field="config", message="Configuration must be a dictionary"))
                return errors
    
            # Check for required top-level keys
            for key in required_keys:
                if key not in config:
                    errors.append(InvalidValue(field=key, message=f"Missing required key '{key}'"))

            rotors = config.get("rotors")
            if not isinstance(rotors, dict):
                errors.append(InvalidValue(field="rotors", message="'rotors' must be a dictionary"))
                        
            # Validate 'setting' structure
            setting = config.get("setting")
            if not isinstance(setting, dict):
                errors.append(InvalidValue(field="setting", message="'setting' must be a dictionary"))
            else:
                for s_key in required_setting_keys:
                    if s_key not in setting:
                        errors.append(InvalidValue(field=f"setting.{s_key}", message=f"Missing setting key '{s_key}'"))
                    elif s_key == "iteration" and not isinstance(setting[s_key], int):
                        errors.append(InvalidValue(field="setting.iteration", message="'iteration' must be an integer"))
                    elif s_key == "factor" and not isinstance(setting[s_key], int):
                        errors.append(InvalidValue(field="setting.factor", message="'factor' must be an integer"))
                    elif s_key == "sequence" and not isinstance(setting[s_key], (list, tuple)):
                        errors.append(InvalidValue(field="setting.sequence", message="'sequence' must be a list"))
                
                sequence = setting.get("sequence")
                if not isinstance(sequence, (list, tuple)) or not all(isinstance(i, str) for i in sequence):
                    errors.append(InvalidValue(field="setting.sequence", message="'sequence' must be a list"))
                elif isinstance(rotors, dict):
                    for i in sequence:
                        if i not in rotors:
                            errors.append(InvalidValue(field="setting.sequence", message=f"Rotor '{i}' not defined in 'rotors'"))
                        else:
                            wiring = rotors.get(i)
                            if not isinstance(wiring, (list, tuple)) or not all(isinstance(j, int) for j in wiring):
                                errors.append(InvalidValue(field=f"rotors.{i}", message="Rotor wiring must be a list of integers"))
                
            characters = config.get("characters")
            if not isinstance(characters, (list, tuple)) or not all(True if isinstance(i, str) and len(i) == 1 else False for i in characters):
                errors.append(InvalidValue(field="characters", message="'characters' must be a list of single character strings"))
            
                        
            
            plugs = config.get("plugs")
            if not isinstance(plugs, (list, tuple)) or not all(isinstance(i, str) for i in plugs):
                errors.append(InvalidValue(field="plugs", message="'plugs' must be a list of strings"))
            
                        
            return errors

    def add_characters(self,character: CharacterSet) -> None:
        """Add a CharacterSet to the configuration."""
        if not isinstance(character, CharacterSet):
            raise TypeError("character must be an instance of CharacterSet")
        self.characters = character
        self.size = len(character)

    def add_plugboard(self,plugboard: Plugboard) -> None:
        """Add a Plugboard to the configuration."""
        if self.characters is None:
            raise ValueError("Characters must be set before adding a plugboard.")
        if self.plugboard is not None:
            raise ValueError("Plugboard has already been set.")
        if not isinstance(plugboard, Plugboard):
            raise TypeError("plugboard must be an instance of Plugboard")
        if len(set(plugboard.characters()).difference(set(self.characters.characters))) > 0:
            raise ValueError("Plugboard contains characters not present in the CharacterSet.")
        self.plugboard = plugboard

    def add_shaft(self, shaft: Shaft) -> None:
        """Add a Shaft to the configuration."""
        if self.characters is None:
                    raise ValueError("Characters must be set before adding a shaft.")
        if self.shaft is not None:
            raise ValueError("Shaft has already been set.")
        if not isinstance(shaft, Shaft):
                    raise TypeError("shaft must be an instance of Shaft")
        if shaft.size != self.size:
            raise ValueError(f"Shaft size {shaft.size} does not match CharacterSet size {self.size}.")
        self.shaft = shaft

    def validate(self) -> bool:
        """Run comprehensive validation on the configuration."""

        if self.characters is None or isinstance(self.characters, CharacterSet) == False:
            return False
        if self.plugboard is None or isinstance(self.plugboard, Plugboard) == False:
            return False
        if self.shaft is None or isinstance(self.shaft, Shaft) == False:
            return False
        if isinstance(self.iteration, int) == False or isinstance(self.factor, int) == False:
            return False
        return True
    