import xml.etree.ElementTree as etree
from pathlib import Path

from pytiled_parser.properties import Properties, Property
from pytiled_parser.util import parse_color


def parse(raw_properties: etree.Element) -> Properties:
    final: Properties = {}
    value: Property

    for raw_property in raw_properties.findall("property"):
        type_ = raw_property.attrib.get("type")

        value_ = raw_property.attrib.get("value", raw_property.text)
        if value_ is None:
            continue

        if type_ == "file":
            value = Path(value_)
        elif type_ == "color":
            value = parse_color(value_)
        elif type_ == "int":
            value = round(float(value_))
        elif type_ == "float":
            value = float(value_)
        elif type_ == "bool":
            if value_ == "true":
                value = True
            else:
                value = False
        else:
            value = value_
        final[raw_property.attrib["name"]] = value

    return final
