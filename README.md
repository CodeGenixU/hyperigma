# Hyperigma

Hyperigma is a dependency-free Python implementation of an Enigma-style
machine. It transforms configured characters through a plugboard, an ordered
rotor assembly, a complement reflector, and the reverse rotor path.

The machine is stateful: encoding advances the rotor positions after every
character. Decoding uses the same reversible operation, so independent
operations should use separate `Enigma` instances.

## Requirements

- Python 3

The project has no package manifest, external runtime dependencies, or
committed test suite.

## Run the example

From the repository root:

```bash
python3 Enigma.py
```

The script loads `configure.json`, encodes a message, decodes it with a
separate machine instance, and prints the original, encoded, and decoded
messages.

Check Python syntax with:

```bash
python3 -m compileall -q Enigma.py components
```

## Use the machine

```python
from Enigma import Enigma
from components.configuration.configuration import Configuration

config = Configuration("configure.json")

encoder = Enigma(config)
encoded = encoder.encode("HELLOWORLD1234564Ukar")

decoder = Enigma(config)
decoded = decoder.decode(encoded)

assert decoded == "HELLOWORLD1234564Ukar"
```

`Enigma` accepts a validated `Configuration` object. Passing the configuration
file path directly to `Enigma` is not supported; construct `Configuration`
first.

## Configuration

`configure.json` is the working configuration example. Its top-level fields
are:

```json
{
  "setting": {
    "sequence": ["a", "b", "c"],
    "iteration": 25,
    "factor": 10
  },
  "plugs": ["ABCD", "@[{()}]?", "0123456789"],
  "characters": ["..."],
  "rotors": {
    "a": ["..."],
    "b": ["..."],
    "c": ["..."]
  }
}
```

- `characters` defines the character domain used by the machine.
- `plugs` defines cyclic plug paths. Every character may belong to at most one
  path, and every plug character must exist in `characters`.
- `rotors` maps rotor names to integer wiring permutations.
- `setting.sequence` selects the rotor order.
- `setting.iteration` sets the initial machine pointer.
- `setting.factor` is an integer configuration setting stored by
  `Configuration`.

Each rotor wiring must be a permutation of the indices from `0` through
`len(characters) - 1`.

## Components

- `Configuration` loads JSON or dictionaries and assembles the machine.
- `CharacterSet` validates characters and converts between characters and
  integer indices.
- `Plug` represents one cyclic plug mapping.
- `PlugRegistry` is the mutable setup-time collection of plug cycles.
- `Plugboard` is the finalized runtime snapshot created from a registry.
- `Rotor` stores immutable forward and reverse wiring.
- `RotorState` stores a rotor's current position.
- `Shaft` validates and orders rotors.
- `Axle` links rotor states, performs forward and reverse traversal, and steps
  the rotors.
- `Enigma` coordinates the complete transformation.

## Validation and errors

Configuration and components validate their own inputs before use. Validation
failures use component-specific exception classes and structured
`InvalidValue` details. Each detail can include:

- `field`: the invalid field or component
- `code`: a machine-readable failure category
- `message`: a human-readable explanation
- `extra_info`: additional context such as conflicting values

The exception modules are under `components/exceptions/`. Independent
components can therefore be validated and used without treating every failure
as a configuration error.

## Project layout

```text
Enigma.py
configure.json
components/
├── character/
├── configuration/
├── exceptions/
├── mechanism/
├── plug/
└── rotor/
```

## License

Hyperigma is distributed under the GNU General Public License, version 3.
See [`LICENSE`](LICENSE).
