import chardet
import json
import xml.etree.ElementTree as etree
from pathlib import Path

from pytiled_parser import UnknownFormat
from pytiled_parser.parsers.json.tiled_map import parse as json_map_parse
from pytiled_parser.parsers.json.tileset import parse as json_tileset_parse
from pytiled_parser.parsers.tmx.tiled_map import parse as tmx_map_parse
from pytiled_parser.parsers.tmx.tileset import parse as tmx_tileset_parse
from pytiled_parser.tiled_map import TiledMap
from pytiled_parser.tileset import Tileset
from pytiled_parser.util import check_format
from pytiled_parser.world import World
from pytiled_parser.world import parse_world as _parse_world


def parse_map(file: Path, encoding: str = "") -> TiledMap:
    """Parse the raw Tiled map into a pytiled_parser type

    Args:
        file: Path to the map file
        encoding: The encoding of the map.

    Returns:
        TiledMap: A parsed and typed TiledMap
    """
    if not encoding:
        with open(file, "rb") as f:
            encoding = chardet.detect(f.read())["encoding"]
    parser = check_format(file, encoding=encoding)

    # The type ignores are because mypy for some reason thinks those functions return Any
    if parser == "tmx":
        return tmx_map_parse(file, encoding=encoding)  # type: ignore
    else:
        try:
            return json_map_parse(file, encoding=encoding)  # type: ignore
        except ValueError:
            raise UnknownFormat(
                "Unknown Map Format, please use either the TMX or JSON format. "
                "This message could also mean your map file is invalid or corrupted."
            )


def parse_tileset(file: Path) -> Tileset:
    """Parse the raw Tiled Tileset into a pytiled_parser type

    Args:
        file: Path to the map file

    Returns:
        Tileset: A parsed and typed Tileset
    """
    parser = check_format(file)

    if parser == "tmx":
        with open(file) as map_file:
            raw_tileset = etree.parse(map_file).getroot()
        return tmx_tileset_parse(raw_tileset, 1)
    else:
        try:
            with open(file) as my_file:
                raw_tileset = json.load(my_file)
            return json_tileset_parse(raw_tileset, 1)
        except ValueError:
            raise UnknownFormat(
                "Unknowm Tileset Format, please use either the TSX or JSON format. "
                "This message could also mean your tileset file is invalid or corrupted."
            )


def parse_world(file: Path) -> World:
    """Parse the raw world file into a pytiled_parser type

    Args:
        file: Path to the world file

    Returns:
        World: A parsed and typed World
    """
    return _parse_world(file)
