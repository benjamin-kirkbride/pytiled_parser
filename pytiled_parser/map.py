# pylint: disable=too-few-public-methods

import json
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Union
from typing import cast as typing_cast

import attr
from typing_extensions import TypedDict

from . import layer, properties, tileset
from .common_types import Color, Size
from .layer import Layer, RawLayer
from .properties import Properties, RawProperty
from .tileset import RawTileSet, TileSet

TilesetDict = Dict[int, TileSet]


@attr.s(auto_attribs=True)
class Map:
    """Object for storing a TMX with all associated layers and properties.

    See: https://doc.mapeditor.org/en/stable/reference/tmx-map-format/#map

    Attributes:
        infinite: If the map is infinite or not.
        layers: List of layer objects by draw order.
        map_size: The map width in tiles.
        next_layer_id: Stores the next available ID for new layers.
        next_object_id: Stores the next available ID for new objects.
        orientation: Map orientation. Tiled supports "orthogonal", "isometric",
            "staggered" and "hexagonal"
        render_order: The order in which tiles on tile layers are rendered. Valid values
            are right-down, right-up, left-down and left-up. In all cases, the map is
        tiled_version: The Tiled version used to save the file. May be a date (for
            snapshot builds).
            drawn row-by-row. (only supported for orthogonal maps at the moment)
        tile_size: The size of a tile.
        tilesets: Dict of Tileset where Key is the firstgid and the value is the Tileset
        version: The JSON format version.
        background_color: The background color of the map.
        properties: The properties of the Map.
        hex_side_length: Only for hexagonal maps. Determines the width or height
            (depending on the staggered axis) of the tile's edge, in pixels.
        stagger_axis: For staggered and hexagonal maps, determines which axis ("x" or
            "y") is staggered.
        stagger_index: For staggered and hexagonal maps, determines whether the "even"
            or "odd" indexes along the staggered axis are shifted.
    """

    infinite: bool
    layers: List[Layer]
    map_size: Size
    next_layer_id: Optional[int]
    next_object_id: int
    orientation: str
    render_order: str
    tiled_version: str
    tile_size: Size
    tilesets: TilesetDict
    version: float

    background_color: Optional[Color] = None
    properties: Optional[Properties] = None
    hex_side_length: Optional[int] = None
    stagger_axis: Optional[str] = None
    stagger_index: Optional[str] = None


class _RawTilesetMapping(TypedDict):
    """ The way that tilesets are stored in the Tiled JSON formatted map."""

    firstgid: int
    source: str


class _RawTiledMap(TypedDict):
    """ The keys and their types that appear in a Tiled JSON Map.

    Keys:
        compressionlevel: not documented - https://github.com/bjorn/tiled/issues/2815
        """

    backgroundcolor: str
    compressionlevel: int
    height: int
    hexsidelength: int
    infinite: bool
    layers: List[RawLayer]
    nextlayerid: int
    nextobjectid: int
    orientation: str
    properties: List[RawProperty]
    renderorder: str
    staggeraxis: str
    staggerindex: str
    tiledversion: str
    tileheight: int
    tilesets: List[_RawTilesetMapping]
    tilewidth: int
    type: str
    version: float
    width: int


def cast(file: Path) -> Map:
    """ Cast the raw Tiled map into a pytiled_parser type

    Args:
        raw_tiled_map: Raw JSON Formatted Tiled Map to be cast.

    Returns:
        TileSet: a properly typed TileSet.
    """

    with open(file) as map_file:
        raw_tiled_map = json.load(map_file)

    parent_dir = file.parent

    raw_tilesets: List[Union[RawTileSet, _RawTilesetMapping]] = raw_tiled_map[
        "tilesets"
    ]
    tilesets: TilesetDict = {}

    for raw_tileset in raw_tilesets:
        if raw_tileset.get("source") is not None:
            # Is an external Tileset
            with open(parent_dir / raw_tileset["source"]) as raw_tileset_file:
                tilesets[raw_tileset["firstgid"]] = tileset.cast(
                    json.load(raw_tileset_file)
                )
        else:
            # Is an embedded Tileset
            raw_tileset = typing_cast(RawTileSet, raw_tileset)
            tilesets[raw_tileset["firstgid"]] = tileset.cast(raw_tileset)

    # `map` is a built-in function
    map_ = Map(
        infinite=raw_tiled_map["infinite"],
        layers=[layer.cast(layer_) for layer_ in raw_tiled_map["layers"]],
        map_size=Size(raw_tiled_map["width"], raw_tiled_map["height"]),
        next_layer_id=raw_tiled_map["nextlayerid"],
        next_object_id=raw_tiled_map["nextobjectid"],
        orientation=raw_tiled_map["orientation"],
        render_order=raw_tiled_map["renderorder"],
        tiled_version=raw_tiled_map["tiledversion"],
        tile_size=Size(raw_tiled_map["tilewidth"], raw_tiled_map["tileheight"]),
        tilesets=tilesets,
        version=raw_tiled_map["version"],
    )

    if raw_tiled_map.get("backgroundcolor") is not None:
        map_.background_color = raw_tiled_map["backgroundcolor"]

    if raw_tiled_map.get("hexsidelength") is not None:
        map_.hex_side_length = raw_tiled_map["hexsidelength"]

    if raw_tiled_map.get("properties") is not None:
        map_.properties = properties.cast(raw_tiled_map["properties"])

    if raw_tiled_map.get("staggeraxis") is not None:
        map_.stagger_axis = raw_tiled_map["staggeraxis"]

    if raw_tiled_map.get("staggerindex") is not None:
        map_.stagger_index = raw_tiled_map["staggerindex"]

    return map_
