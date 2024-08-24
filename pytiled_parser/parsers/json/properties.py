"""Property parsing for the JSON Map Format
"""

from pathlib import Path
from typing import List, Union, cast

from typing_extensions import TypedDict

from pytiled_parser.common_types import Color
from pytiled_parser.properties import Properties, Property
from pytiled_parser.util import parse_color, serialize_color

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
            else:
                value = raw_property["value"]
            final[raw_property["name"]] = value

    return final


def serialize(properties: Properties) -> List[RawProperty]:
    """Serialize a Properties object into a list of RawProperty objects.

    Args:
        properties: The properties to be serialized.

    Returns:
        List[RawProperty]: The serialized RawProperty list
    """

    final: List[RawProperty] = []

    for name, prop in properties.items():
        prop_type = ""
        if isinstance(prop, Path):
            prop_type = "file"
            prop = str(prop)
        elif isinstance(prop, Color):
            prop_type = "color"
            prop = serialize_color(prop)
        elif isinstance(prop, str):
            prop_type = "string"
        elif isinstance(prop, float):
            prop_type = "float"
        elif isinstance(prop, int):
            prop_type = "int"
        elif isinstance(prop, bool):
            prop_type = "bool"

        raw: RawProperty = {"name": name, "type": prop_type, "value": prop}
        final.append(raw)

    return final
