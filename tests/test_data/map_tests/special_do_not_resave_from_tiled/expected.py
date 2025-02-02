from pathlib import Path

from pytiled_parser import common_types, tiled_map, tileset

EXPECTED = tiled_map.TiledMap(
    map_file=None,
    infinite=False,
    layers=[],
    map_size=common_types.Size(8, 6),
    next_layer_id=2,
    next_object_id=1,
    orientation="orthogonal",
    render_order="right-down",
    tiled_version="1.9.1",
    tile_size=common_types.Size(32, 32),
    version="1.9",
    background_color=common_types.Color(255, 0, 4, 255),
    parallax_origin=common_types.OrderedPair(10, 15),
    tilesets={
        1: tileset.Tileset(
            columns=8,
            image=Path(Path(__file__).parent / "../../images/tmw_desert_spacing.png")
            .absolute()
            .resolve(),
            image_width=265,
            image_height=199,
            firstgid=1,
            margin=1,
            spacing=1,
            name="tile_set_image",
            tile_count=48,
            tiled_version="1.6.0",
            tile_height=32,
            tile_width=32,
            version="1.6",
            type="tileset",
        )
    },
    properties={
        "bool property - true": True,
        "color property": common_types.Color(73, 252, 255, 255),
        "file property": Path("../../../../../../var/log/syslog"),
        "float property": 1.23456789,
        "int property": 13,
        "broken int property": 14,
        "string property": "Hello, World!!",
    },
)
