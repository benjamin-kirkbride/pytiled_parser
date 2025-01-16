"""Property parsing for the JSON Map Format
"""

from pathlib import Path
from typing import List, Union, cast

from typing_extensions import TypedDict

from pytiled_parser.properties import Properties, Property
from pytiled_parser.util import parse_color

RawValue = Union[float, str, bool]


class RawProperty(TypedDict):
    """The keys and their values that appear in a Tiled JSON Property Object.

    Tiled Docs: https://doc.mapeditor.org/en/stable/reference/json-map-format/#property
    """

    name: str
    type: str
    value: RawValue


def parse(raw_properties: List[RawProperty]) -> Properties:
    """Parse a list of `RawProperty` objects into `Properties`.

    Args:
        raw_properties: The list or dict of `RawProperty` objects to parse. The dict type is supported for parsing legacy Tiled dungeon files.

    Returns:
        Properties: The parsed `Property` objects.
    """

    final: Properties = {}
    value: Property

    if isinstance(raw_properties, dict):
        for name, value in raw_properties.items():
            final[name] = value
    else:
        for raw_property in raw_properties:
            if raw_property["type"] == "file":
                value = Path(cast(str, raw_property["value"]))
            elif raw_property["type"] == "color":
                value = parse_color(cast(str, raw_property["value"]))
            elif raw_property["type"] == "int":
                value = round(cast(float, raw_property["value"]))
            else:
                value = raw_property["value"]
            final[raw_property["name"]] = value

    return final
