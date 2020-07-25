# pylint: disable=too-few-public-methods

import base64
import gzip
import zlib
from pathlib import Path
from typing import Any, Callable, List, Optional, Union

import attr
from typing_extensions import TypedDict

from . import properties as properties_
from . import tiled_object
from .common_types import Color, OrderedPair, Size


@attr.s(auto_attribs=True, kw_only=True)
class Layer:
    # FIXME:this docstring appears to be innacurate
    """Class that all layers inherit from.

    Args:
        id: Unique ID of the layer. Each layer that added to a map gets a unique id.
            Even if a layer is deleted, no layer ever gets the same ID.
        name: The name of the layer object.
        tiled_objects: List of tiled_objects in the layer.
        offset: Rendering offset of the layer object in pixels.
        opacity: Decimal value between 0 and 1 to determine opacity. 1 is completely
            opaque, 0 is completely transparent.
        properties: Properties for the layer.
        color: The color used to display the objects in this group.
        draworder: Whether the objects are drawn according to the order of the object
            elements in the object group element ('manual'), or sorted by their
            y-coordinate ('topdown'). Defaults to 'topdown'.
            See:
            https://doc.mapeditor.org/en/stable/manual/objects/#changing-stacking-order
            for more info.
    """

    name: str
    opacity: float
    visible: bool

    coordinates: Optional[OrderedPair] = None
    id: Optional[int] = None
    size: Optional[Size] = None
    offset: Optional[OrderedPair] = None
    properties: Optional[properties_.Properties] = None


TileLayerGrid = List[List[int]]


@attr.s(auto_attribs=True)
class Chunk:
    """Chunk object for infinite maps.

    See: https://doc.mapeditor.org/en/stable/reference/tmx-map-format/#chunk

    Attributes:
        coordinates: Location of chunk in tiles.
        size: The size of the chunk in tiles.
        data: The global tile IDs in chunky according to row.
    """

    coordinates: OrderedPair
    size: Size

    data: Optional[Union[List[int], str]] = None


LayerData = Union[TileLayerGrid, List[Chunk]]
# The tile data for one layer.
#
# Either a 2 dimensional array of integers representing the global tile IDs
#     for a TileLayerGrid, or a list of chunks for an infinite map layer.


@attr.s(auto_attribs=True, kw_only=True)
class TileLayer(Layer):
    """Tile map layer containing tiles.

    See: https://doc.mapeditor.org/en/stable/reference/tmx-map-format/#layer

    Args:
        size: The width of the layer in tiles. The same as the map width unless map is
            infitite.
        data: Either an 2 dimensional array of integers representing the global tile
            IDs for the map layer, or a list of chunks for an infinite map.
    """

    encoding: str = "csv"

    compression: Optional[str] = None
    chunks: Optional[List[Chunk]] = None
    data: Optional[Union[List[int], str]] = None


@attr.s(auto_attribs=True, kw_only=True)
class ObjectLayer(Layer):
    """
    TiledObject Group Object.
    The object group is in fact a map layer, and is hence called "object layer" in
        Tiled.
    See: https://doc.mapeditor.org/en/stable/reference/tmx-map-format/#objectgroup
    Args:
        tiled_objects: List of tiled_objects in the layer.
        offset: Rendering offset of the layer object in pixels.
        color: The color used to display the objects in this group. FIXME: editor only?
        draworder: Whether the objects are drawn according to the order of the object
            elements in the object group element ('manual'), or sorted by their
            y-coordinate ('topdown'). Defaults to 'topdown'. See:
            https://doc.mapeditor.org/en/stable/manual/objects/#changing-stacking-order
            for more info.
    """

    tiled_objects: List[tiled_object.TiledObject]

    draw_order: Optional[str] = "topdown"


@attr.s(auto_attribs=True, kw_only=True)
class ImageLayer(Layer):
    """Map layer containing images.

    See: https://doc.mapeditor.org/en/stable/manual/layers/#image-layers

    Attributes:
        image: The image used by this layer.
        transparent_color: Color that is to be made transparent on this layer.
    """

    image: Path
    transparent_color: Optional[Color] = None


@attr.s(auto_attribs=True, kw_only=True)
class LayerGroup(Layer):
    """Layer Group.
    A LayerGroup can be thought of as a layer that contains layers
        (potentially including other LayerGroups).
    Offset and opacity recursively affect child layers.
    See: https://doc.mapeditor.org/en/stable/reference/tmx-map-format/#group
    Attributes:
        Layers: Layers in group.
    """

    layers: Optional[List[Layer]]


class RawChunk(TypedDict):
    """ The keys and their types that appear in a Chunk JSON Object."""

    data: Union[List[int], str]
    height: int
    width: int
    x: int
    y: int


class RawLayer(TypedDict):
    # FIXME Make the layers attribute function
    """ The keys and their types that appear in a Layer JSON Object."""

    chunks: List[RawChunk]
    compression: str
    data: Union[List[int], str]
    draworder: str
    encoding: str
    height: int
    id: int
    image: str
    layers: List[Any]
    name: str
    objects: List[tiled_object.RawTiledObject]
    offsetx: float
    offsety: float
    opacity: float
    properties: List[properties_.RawProperty]
    startx: int
    starty: int
    transparentcolor: str
    type: str
    visible: bool
    width: int
    x: int
    y: int


def _decode_tile_layer_data(tile_layer: TileLayer) -> TileLayer:
    """Decode Base64 Encoded Tile Data. Supports gzip and zlib compression.

    Args:
        tile_layer: The TileLayer to decode the data for

    Returns:
        TileLayer: The TileLayer with the decoded data

    Raises:
        ValueError: For an unsupported compression type.
    """
    if not isinstance(tile_layer.data, str):
        return tile_layer

    unencoded_data = base64.b64decode(tile_layer.data)
    if tile_layer.compression == "zlib":
        unzipped_data = zlib.decompress(unencoded_data)
    elif tile_layer.compression == "gzip":
        unzipped_data = gzip.decompress(unencoded_data)
    elif tile_layer.compression is None:
        unzipped_data = unencoded_data
    else:
        raise ValueError(f"Unsupported compression type: '{tile_layer.compression}'.")

    tile_grid = []

    byte_count = 0
    int_count = 0
    int_value = 0
    for byte in unzipped_data:
        int_value += byte << (byte_count * 8)
        byte_count += 1
        if not byte_count % 4:
            byte_count = 0
            int_count += 1
            tile_grid.append(int_value)
            int_value = 0

    tile_grid.pop()
    tile_layer.data = tile_grid
    return tile_layer


def _cast_chunk(raw_chunk: RawChunk) -> Chunk:
    """ Cast the raw_chunk to a Chunk.

    Args:
        raw_chunk: RawChunk to be casted to a Chunk

    Returns:
        Chunk: The Chunk created from the raw_chunk
    """

    chunk = Chunk(
        coordinates=OrderedPair(raw_chunk["x"], raw_chunk["y"]),
        size=Size(raw_chunk["width"], raw_chunk["height"]),
    )

    if raw_chunk.get("data") is not None:
        chunk.data = raw_chunk["data"]

    return chunk


def _get_common_attributes(raw_layer: RawLayer) -> Layer:
    """ Create a Layer containing all the attributes common to all layers

    Args:
        raw_layer: Raw Tiled object get common attributes from

    Returns:
        Layer: The attributes in common of all layers
    """
    common_attributes = Layer(
        name=raw_layer["name"],
        opacity=raw_layer["opacity"],
        visible=raw_layer["visible"],
    )

    if raw_layer.get("startx") is not None:
        common_attributes.coordinates = OrderedPair(
            raw_layer["startx"], raw_layer["starty"]
        )

    if raw_layer.get("id") is not None:
        common_attributes.id = raw_layer["id"]

    # if either width or height is present, they both are
    if raw_layer.get("width") is not None:
        common_attributes.size = Size(raw_layer["width"], raw_layer["height"])

    if raw_layer.get("offsetx") is not None:
        common_attributes.offset = OrderedPair(
            raw_layer["offsetx"], raw_layer["offsety"]
        )

    if raw_layer.get("properties") is not None:
        common_attributes.properties = properties_.cast(raw_layer["properties"])

    return common_attributes


def _cast_tile_layer(raw_layer: RawLayer) -> TileLayer:
    """ Cast the raw_layer to a TileLayer.

    Args:
        raw_layer: RawLayer to be casted to a TileLayer

    Returns:
        TileLayer: The TileLayer created from raw_layer
    """
    tile_layer = TileLayer(**_get_common_attributes(raw_layer).__dict__)

    tile_layer.encoding = raw_layer["encoding"]

    if raw_layer.get("compression") is not None:
        tile_layer.compression = raw_layer["compression"]

    if raw_layer.get("chunks") is not None:
        tile_layer.chunks = []
        for chunk in raw_layer["chunks"]:
            tile_layer.chunks.append(_cast_chunk(chunk))

    if raw_layer.get("data") is not None:
        tile_layer.data = raw_layer["data"]

    if tile_layer.encoding == "base64":
        _decode_tile_layer_data(tile_layer)

    return tile_layer


def _cast_object_layer(raw_layer: RawLayer) -> ObjectLayer:
    """ Cast the raw_layer to an ObjectLayer.

    Args:
        raw_layer: RawLayer to be casted to an ObjectLayer
    Returns:
        ObjectLayer: The ObjectLayer created from raw_layer
    """

    tiled_objects = []
    for tiled_object_ in raw_layer["objects"]:
        tiled_objects.append(tiled_object.cast(tiled_object_))

    return ObjectLayer(
        tiled_objects=tiled_objects,
        draw_order=raw_layer["draworder"],
        **_get_common_attributes(raw_layer).__dict__,
    )


def _cast_image_layer(raw_layer: RawLayer) -> ImageLayer:
    """ Cast the raw_layer to a ImageLayer.

    Args:
        raw_layer: RawLayer to be casted to a ImageLayer

    Returns:
        ImageLayer: The ImageLayer created from raw_layer
    """
    image_layer = ImageLayer(
        image=Path(raw_layer["image"]), **_get_common_attributes(raw_layer).__dict__
    )

    if raw_layer.get("transparentcolor") is not None:
        image_layer.transparent_color = Color(raw_layer["transparentcolor"])

    return image_layer


def _cast_group_layer(raw_layer: RawLayer) -> LayerGroup:
    """ Cast the raw_layer to a LayerGroup.

    Args:
        raw_layer: RawLayer to be casted to a LayerGroup

    Returns:
        LayerGroup: The LayerGroup created from raw_layer
    """

    layers = []

    for layer in raw_layer["layers"]:
        layers.append(cast(layer))

    return LayerGroup(layers=layers, **_get_common_attributes(raw_layer).__dict__)


def _get_caster(type_: str) -> Callable[[RawLayer], Layer]:
    """ Get the caster function for the raw layer.

    Args:
        type_: the type of the layer

    Returns:
        Callable[[RawLayer], Layer]: The caster function.
    """
    casters = {
        "tilelayer": _cast_tile_layer,
        "objectgroup": _cast_object_layer,
        "imagelayer": _cast_image_layer,
        "group": _cast_group_layer,
    }
    return casters[type_]


def cast(raw_layer: RawLayer) -> Layer:
    """ Cast the raw Tiled layer into a pytiled_parser type

    Args:
        raw_layer: Raw layer to be cast.

    Returns:
        Layer: a properly typed Layer.
    """
    caster = _get_caster(raw_layer["type"])

    return caster(raw_layer)
