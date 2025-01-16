# pytiled-parser

PyTiled Parser is a Python Library for parsing [Tiled Map Editor](https://www.mapeditor.org/) maps and tilesets to be used as maps and levels for 2D top-down (orthogonal, hexogonal, or isometric) or side-scrolling games in a strictly typed fashion.

PyTiled Parser is not tied to any particular graphics library or game engine. It parses map files and returns arbitrary Python types(like `Path` objects for image files rather than a `Sprite` from any particular engine). This means it can be used to aide in implementing Tiled support into a wide variety of tools.

- Documentation available at: https://pytiled-parser.readthedocs.io/
- GitHub project at: https://github.com/pythonarcade/pytiled_parser
- PyPi: https://pypi.org/project/pytiled-parser/

The [Arcade](https://api.arcade.academy) library has
[supporting code](https://api.arcade.academy/en/latest/api/tilemap.html) to
integrate PyTiled Parser and [example code](https://api.arcade.academy/en/latest/examples/index.html#using-tiled-map-editor-to-create-maps) showing its use.

## Supported Python Versions

pytiled-parser works on Python 3.6 - 3.13(and should continue to work on new versions). However we are not actively testing on Python 3.6 and 3.7 due to other development tooling not supporting them, however as long as it remains tenable to do so, we will support these versions and fix problems for them.

## Installation

Simply install with pip:

```
pip install pytiled-parser
```

## Loading a Map

**NOTE:** All map paths should ideally be `Path` objects from Python's `pathlib` module. However a string will work in many cases.

```python
from pathlib import Path

import pytiled_parser

map_file = Path("assets/maps/my_map.tmx")
my_map = pytiled_parser.parse_map(map_file)
```

In order to fully understand the pytiled-parser API, it is suggested that you have a solid understanding of the [Tiled Map Editor](https://doc.mapeditor.org/en/stable/), and it's [JSON format](https://doc.mapeditor.org/en/stable/reference/json-map-format/). An effort was made to keep the API that pytiled-parser provides as close as possible with the JSON format directly. Only small variations are made at certain points for ease of use with integrating to a game or engine.

## Working With Layers

Layers are loaded as an ordered list of `Layer` objects within the map. They can be accessed via the `layers` attribute of a map. There has been debate about wether or not these should be loaded in as a Dictionary, with the keys being the name of the layer. The decision was ultimately made to leave them as a list, as there is no guarantee, and beyond that is considered acceptable use to have duplicate layer names in Tiled.

Thus the decision to allow duplicate layer names is up to the implementation, as an example, [Arcade](https://arcade.academy) does not allow duplicate layer names, as it re-roganizes layers into dictionaries based on the name.

## Development

To develop pytiled parser, clone the repo, create a `venv` using a supported Python version, and activate it. Then install the package as well as all testing, linting, and formatting dependencies with the command `python -m pip install -e ".[dev]"`.

### Linting and Formatting

flake8, mypy, black, and isort should all be used during development. These should ideally all pass before committing. Some work is under way to have a pre-commit hook for these or do checks in CI.

### Testing

Run `pytest --cov=pytiled_parser` to run the test harness and report coverage.

### Docs

Install Docs dependencies with the command `python -m pip install ".[docs]"`

To serve the docs locally:

```
mkdocs serve
```

They can then be accessed on http://localhost:8000

## Credits

Original module created by [Benjamin Kirkbride](https://github.com/benjamin-kirkbride).

Currently maintained by [Cleptomania](https://github.com/cleptomania)

Special thanks for contributions from [pvcraven](https://github.com/pvcraven) and the contributors that create Tiled, without which this library wouldn't exist.
