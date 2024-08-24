"""Layer parsing for the JSON Map Format.
"""

import base64
import gzip
import importlib.util
import struct
import zlib
from pathlib import Path
from typing import Any, List, Optional, Union, cast

from typing_extensions import TypedDict

from pytiled_parser.common_types import OrderedPair, Size
from pytiled_parser.layer import (
    Chunk,
    ImageLayer,
    Layer,
    LayerGroup,
    ObjectLayer,
    TileLayer,
)
from pytiled_parser.parsers.json.properties import RawProperty
from pytiled_parser.parsers.json.properties import parse as parse_properties
from pytiled_parser.parsers.json.properties import serialize as serialize_properties
from pytiled_parser.parsers.json.tiled_object import RawObject
from pytiled_parser.parsers.json.tiled_object import parse as parse_object
from pytiled_parser.parsers.json.tiled_object import serialize as serialize_object
from pytiled_parser.util import parse_color, serialize_color

# This optional zstd include is basically impossible to make a sensible test
# for both ways. It's been tested manually, is unlikely to change or be effected
# so we're just excluding it from test coverage. We are only testing cases where
# zstd is not installed in the test suite, as that is the scenario for 99%
# of use cases most likely.
#
# This does mean that the test suite will fail if zstd is installed, so for
# development purposes it should only be installed when specifically manually
# testing for zstd things.
zstd_spec = importlib.util.find_spec("zstd")
if zstd_spec:  # pragma: no cover
    import zstd
else:
    zstd = None


RawChunk = TypedDict(
    "RawChunk",
    {"data": Union[List[int], str], "height": int, "width": int, "x": int, "y": int},
)
RawChunk.__doc__ = """
    The keys and their types that appear in a Tiled JSON Chunk Object.

    Tiled Doc: https://doc.mapeditor.org/en/stable/reference/json-map-format/#chunk
"""


RawLayer = TypedDict(
    "RawLayer",
    {
        "chunks": List[RawChunk],
        "compression": str,
        "data": Union[List[int], str],
        "draworder": str,
        "encoding": str,
        "height": int,
        "id": int,
        "image": str,
        "layers": List[Any],
        "name": str,
        "objects": List[RawObject],
        "offsetx": float,
        "offsety": float,
        "parallaxx": float,
        "parallaxy": float,
        "opacity": float,
        "properties": List[RawProperty],
        "startx": int,
        "starty": int,
        "tintcolor": str,
        "transparentcolor": str,
        "class": str,
        "type": str,
        "visible": bool,
        "width": int,
        "x": int,
        "y": int,
        "repeatx": bool,
        "repeaty": bool,
    },
)
RawLayer.__doc__ = """
    The keys and their types that appear in a Tiled JSON Layer Object.

    Tiled Doc: https://doc.mapeditor.org/en/stable/reference/json-map-format/#layer
"""


def _convert_raw_tile_layer_data(data: List[int], layer_width: int) -> List[List[int]]:
    """Convert raw layer data into a nested lit based on the layer width

    Args:
        data: The data to convert
        layer_width: Width of the layer

    Returns:
        List[List[int]]: A nested list containing the converted data
    """
    tile_grid: List[List[int]] = [[]]

    column_count = 0
    row_count = 0
    for item in data:
        column_count += 1
        tile_grid[row_count].append(item)
        if not column_count % layer_width and column_count < len(data):
            row_count += 1
            tile_grid.append([])

    return tile_grid


def _convert_tile_layer_data_to_raw(data: List[List[int]]) -> List[int]:
    return [i for sub in data for i in sub]


def _decode_tile_layer_data(
    data: str, compression: str, layer_width: int
) -> List[List[int]]:
    """Decode Base64 Encoded tile data. Optionally supports gzip and zlib compression.

    Args:
        data: The base64 encoded data
        compression: Either zlib, gzip, or empty. If empty no decompression is done.

    Returns:
        List[List[int]]: A nested list containing the decoded data

    Raises:
        ValueError: For an unsupported compression type.
    """
    unencoded_data = base64.b64decode(data)
    if compression == "zlib":
        unzipped_data = zlib.decompress(unencoded_data)
    elif compression == "gzip":
        unzipped_data = gzip.decompress(unencoded_data)
    elif compression == "zstd" and zstd is None:
        raise ValueError(
            "zstd compression support is not installed."
            "To install use 'pip install pytiled-parser[zstd]'"
        )
    # See above note at top of module about zstd tests
    elif compression == "zstd":  # pragma: no cover
        unzipped_data = zstd.decompress(unencoded_data)
    else:
        unzipped_data = unencoded_data

    tile_grid: List[int] = list(
        struct.unpack("<%dL" % (len(unzipped_data) / 4), unzipped_data)
    )

    return _convert_raw_tile_layer_data(tile_grid, layer_width)


def _encode_tile_layer_data(
    data: List[List[int]], compression: Optional[str] = None
) -> str:
    """Encode a Base64 string of tile data. Optionally supports gzip, zlib, and zstd compression.
    Args:
        data: Tile data in the form of a 2 dimensional list of ints
        compression: Either zlib, gzip, zstd, or empty. If empty no compression is performed.
    Returns:
        str: The encoded and compressed data
    Raises:
        ValueError: For an unsupported compression type
    """
    flattened = [i for sub in data for i in sub]
    data_bytes = struct.pack("<%dL" % len(flattened), *flattened)

    if compression == "zlib":
        compressed = zlib.compress(data_bytes)
    elif compression == "gzip":
        compressed = gzip.compress(data_bytes)
    elif compression == "zstd" and zstd is None:
        raise ValueError(
            "zstd compression support is not installed."
            "To install use 'pip install pytiled-parser[zstd]'"
        )
    elif compression == "zstd":  # pragma: no cover
        compressed = zstd.compress(data_bytes)
    else:
        compressed = data_bytes

    return base64.b64encode(compressed).decode("UTF-8")


def _parse_chunk(
    raw_chunk: RawChunk,
    encoding: Optional[str] = None,
    compression: Optional[str] = None,
) -> Chunk:
    """Parse the raw_chunk to a Chunk.

    Args:
        raw_chunk: RawChunk to be parsed to a Chunk
        encoding: Encoding type. ("base64" or None)
        compression: Either zlib, gzip, or empty. If empty no decompression is done.

    Returns:
        Chunk: The Chunk created from the raw_chunk
    """
    if encoding == "base64":
        assert isinstance(compression, str)
        assert isinstance(raw_chunk["data"], str)
        data = _decode_tile_layer_data(
            raw_chunk["data"], compression, raw_chunk["width"]
        )
    else:
        data = _convert_raw_tile_layer_data(
            raw_chunk["data"], raw_chunk["width"]  # type: ignore
        )

    chunk = Chunk(
        coordinates=OrderedPair(raw_chunk["x"], raw_chunk["y"]),
        size=Size(raw_chunk["width"], raw_chunk["height"]),
        data=data,
    )

    return chunk


def _serialize_chunk(
    chunk: Chunk, encoding: Optional[str] = None, compression: Optional[str] = None
) -> RawChunk:
    if encoding == "base64":
        assert isinstance(compression, str)
        data = _encode_tile_layer_data(chunk.data, compression)
    else:
        data = _convert_tile_layer_data_to_raw(chunk.data)

    return {
        "data": data,
        "width": int(chunk.size.width),
        "height": int(chunk.size.height),
        "x": int(chunk.coordinates.x),
        "y": int(chunk.coordinates.y),
    }


def _parse_common(raw_layer: RawLayer) -> Layer:
    """Create a Layer containing all the attributes common to all layer types.

    This is to create the stub Layer object that can then be used to create the actual
        specific sub-classes of Layer.

    Args:
        raw_layer: Raw layer get common attributes from

    Returns:
        Layer: The attributes in common of all layer types
    """
    common = Layer(
        name=raw_layer["name"],
        opacity=raw_layer["opacity"],
        visible=raw_layer["visible"],
    )

    # if startx is present, starty is present
    if raw_layer.get("startx") is not None:
        common.coordinates = OrderedPair(raw_layer["startx"], raw_layer["starty"])

    if raw_layer.get("id") is not None:
        common.id = raw_layer["id"]

    # if either width or height is present, they both are
    if raw_layer.get("width") is not None:
        common.size = Size(raw_layer["width"], raw_layer["height"])

    if raw_layer.get("offsetx") is not None:
        common.offset = OrderedPair(raw_layer["offsetx"], raw_layer["offsety"])

    if raw_layer.get("properties") is not None:
        common.properties = parse_properties(raw_layer["properties"])

    if raw_layer.get("class") is not None:
        common.class_ = raw_layer["class"]

    parallax = [1.0, 1.0]

    if raw_layer.get("parallaxx") is not None:
        parallax[0] = raw_layer["parallaxx"]

    if raw_layer.get("parallaxy") is not None:
        parallax[1] = raw_layer["parallaxy"]

    common.parallax_factor = OrderedPair(parallax[0], parallax[1])

    if raw_layer.get("tintcolor") is not None:
        common.tint_color = parse_color(raw_layer["tintcolor"])

    if raw_layer.get("repeatx") is not None:
        common.repeat_x = raw_layer["repeatx"]

    if raw_layer.get("repeaty") is not None:
        common.repeat_y = raw_layer["repeaty"]

    return common


def _serialize_common(layer: Layer, layer_type: str) -> RawLayer:
    serialized: RawLayer = {
        "name": layer.name,
        "opacity": layer.opacity,
        "visible": layer.visible,
        "x": 0,
        "y": 0,
        "type": layer_type,
    }

    if layer.id:
        serialized["id"] = layer.id

    if layer.coordinates != OrderedPair(0, 0):
        serialized["startx"] = int(layer.coordinates.x)
        serialized["starty"] = int(layer.coordinates.y)

    if layer.size:
        serialized["width"] = int(layer.size.width)
        serialized["height"] = int(layer.size.height)

    if layer.offset != OrderedPair(0, 0):
        serialized["offsetx"] = layer.offset.x
        serialized["offsety"] = layer.offset.y

    if layer.properties:
        serialized["properties"] = serialize_properties(layer.properties)

    if layer.class_:
        serialized["class"] = layer.class_

    if layer.parallax_factor.x != 1.0:
        serialized["parallaxx"] = layer.parallax_factor.x

    if layer.parallax_factor.y != 1.0:
        serialized["parallaxy"] = layer.parallax_factor.y

    if layer.tint_color:
        serialized["tintcolor"] = serialize_color(layer.tint_color)

    if layer.repeat_x:
        serialized["repeatx"] = layer.repeat_x

    if layer.repeat_y:
        serialized["repeaty"] = layer.repeat_y

    return serialized


def _parse_tile_layer(raw_layer: RawLayer) -> TileLayer:
    """Parse the raw_layer to a TileLayer.

    Args:
        raw_layer: RawLayer to be parsed to a TileLayer.

    Returns:
        TileLayer: The TileLayer created from raw_layer
    """
    tile_layer = TileLayer(**_parse_common(raw_layer).__dict__)

    if raw_layer.get("chunks") is not None:
        tile_layer.chunks = []
        for chunk in raw_layer["chunks"]:
            if raw_layer.get("encoding") is not None:
                tile_layer.compression = raw_layer["compression"]
                tile_layer.encoding = raw_layer["encoding"]
                tile_layer.chunks.append(
                    _parse_chunk(chunk, raw_layer["encoding"], raw_layer["compression"])
                )
            else:
                tile_layer.chunks.append(_parse_chunk(chunk))

    if raw_layer.get("data") is not None:
        if raw_layer.get("encoding") is not None:
            tile_layer.compression = raw_layer["compression"]
            tile_layer.encoding = raw_layer["encoding"]
            tile_layer.data = _decode_tile_layer_data(
                data=cast(str, raw_layer["data"]),
                compression=raw_layer["compression"],
                layer_width=raw_layer["width"],
            )
        else:
            tile_layer.data = _convert_raw_tile_layer_data(
                raw_layer["data"], raw_layer["width"]  # type: ignore
            )

    return tile_layer


def _serialize_tile_layer(layer: TileLayer) -> RawLayer:
    serialized = _serialize_common(layer, "tilelayer")

    if layer.chunks:
        raw_chunks: List[RawChunk] = []
        for chunk in layer.chunks:
            raw_chunks.append(
                _serialize_chunk(chunk, layer.encoding, layer.compression)
            )
        serialized["chunks"] = raw_chunks

    if layer.data:
        if layer.encoding == "base64":
            raw_data = _encode_tile_layer_data(layer.data, layer.compression)
        else:
            raw_data = _convert_tile_layer_data_to_raw(layer.data)
        serialized["data"] = raw_data

    if layer.encoding != "csv":
        serialized["encoding"] = layer.encoding
        serialized["compression"] = layer.compression

    return serialized


def _parse_object_layer(
    raw_layer: RawLayer,
    parent_dir: Optional[Path] = None,
) -> ObjectLayer:
    """Parse the raw_layer to an ObjectLayer.

    Args:
        raw_layer: RawLayer to be parsed to an ObjectLayer.

    Returns:
        ObjectLayer: The ObjectLayer created from raw_layer
    """
    objects = []
    for object_ in raw_layer["objects"]:
        objects.append(parse_object(object_, parent_dir))

    return ObjectLayer(
        tiled_objects=objects,
        draw_order=raw_layer["draworder"],
        **_parse_common(raw_layer).__dict__,
    )


def _serialize_object_layer(layer: ObjectLayer) -> RawLayer:
    serialized = _serialize_common(layer, "objectgroup")

    objects = []
    for obj in layer.tiled_objects:
        objects.append(serialize_object(obj))
    serialized["objects"] = objects
    serialized["draworder"] = layer.draw_order

    return serialized


def _parse_image_layer(raw_layer: RawLayer) -> ImageLayer:
    """Parse the raw_layer to an ImageLayer.

    Args:
        raw_layer: RawLayer to be parsed to an ImageLayer.

    Returns:
        ImageLayer: The ImageLayer created from raw_layer
    """
    image_layer = ImageLayer(
        image=Path(raw_layer["image"]), **_parse_common(raw_layer).__dict__
    )

    if raw_layer.get("transparentcolor") is not None:
        image_layer.transparent_color = parse_color(raw_layer["transparentcolor"])

    return image_layer


def _serialize_image_layer(layer: ImageLayer) -> RawLayer:
    serialized = _serialize_common(layer, "imagelayer")

    # TODO: This is an absolute path, need to figure out how to handle
    # relative filepaths for serialization
    serialized["image"] = str(layer.image)

    if layer.transparent_color:
        serialized["transparentcolor"] = serialize_color(layer.transparent_color)

    return serialized


def _parse_group_layer(
    raw_layer: RawLayer, parent_dir: Optional[Path] = None
) -> LayerGroup:
    """Parse the raw_layer to a LayerGroup.

    Args:
        raw_layer: RawLayer to be parsed to a LayerGroup.

    Returns:
        LayerGroup: The LayerGroup created from raw_layer
    """
    layers = []

    for layer in raw_layer["layers"]:
        layers.append(parse(layer, parent_dir=parent_dir))

    return LayerGroup(layers=layers, **_parse_common(raw_layer).__dict__)


def _serialize_group_layer(layer: LayerGroup) -> RawLayer:
    serialized = _serialize_common(layer, "group")

    raw_layers: List[RawLayer] = []

    for child_layer in layer.layers:
        raw_layers.append(serialize(child_layer))

    if raw_layers:
        serialized["layers"] = raw_layers

    return serialized


def parse(
    raw_layer: RawLayer,
    parent_dir: Optional[Path] = None,
) -> Layer:
    """Parse a raw Layer into a pytiled_parser object.

    This function will determine the type of layer and parse accordingly.

    Args:
        raw_layer: Raw layer to be parsed.
        parent_dir: The parent directory that the map file is in.

    Returns:
        Layer: A parsed Layer.

    Raises:
        RuntimeError: For an invalid layer type being provided
    """
    type_ = raw_layer["type"]

    if type_ == "objectgroup":
        return _parse_object_layer(raw_layer, parent_dir)
    elif type_ == "group":
        return _parse_group_layer(raw_layer, parent_dir)
    elif type_ == "imagelayer":
        return _parse_image_layer(raw_layer)
    elif type_ == "tilelayer":
        return _parse_tile_layer(raw_layer)

    raise RuntimeError(f"An invalid layer type of {type_} was supplied")


def serialize(layer: Layer) -> RawLayer:
    if isinstance(layer, TileLayer):
        return _serialize_tile_layer(layer)
    elif isinstance(layer, ImageLayer):
        return _serialize_image_layer(layer)
    elif isinstance(layer, ObjectLayer):
        return _serialize_object_layer(layer)
    elif isinstance(layer, LayerGroup):
        return _serialize_group_layer(layer)

    raise AttributeError("Tried to serialize an unknown layer type.")
