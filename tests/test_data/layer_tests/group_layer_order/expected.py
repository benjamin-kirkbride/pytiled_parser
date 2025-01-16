from pathlib import Path

from pytiled_parser import common_types, layer, tiled_object

EXPECTED = [
    layer.ObjectLayer(
        name="Outer 2",
        opacity=1,
        visible=True,
        id=13,
        draw_order="topdown",
        tiled_objects=[],
        parallax_factor=common_types.OrderedPair(1.0, 1.0),
    ),
    layer.LayerGroup(
        name="Outer Group",
        opacity=1,
        visible=True,
        id=4,
        parallax_factor=common_types.OrderedPair(1.0, 1.0),
        layers=[
            layer.ObjectLayer(
                name="Inner 2",
                opacity=1,
                visible=True,
                id=15,
                draw_order="topdown",
                tiled_objects=[],
                parallax_factor=common_types.OrderedPair(1.0, 1.0),
            ),
            layer.LayerGroup(
                name="Inner Group",
                id=6,
                layers=[],
                visible=True,
                opacity=1,
                parallax_factor=common_types.OrderedPair(1.0, 1.0),
            ),
            layer.ObjectLayer(
                name="Inner 1",
                opacity=1,
                visible=True,
                id=14,
                draw_order="topdown",
                tiled_objects=[],
                parallax_factor=common_types.OrderedPair(1.0, 1.0),
            ),
        ],
    ),
    layer.ObjectLayer(
        name="Outer 1",
        opacity=1,
        visible=True,
        id=12,
        draw_order="topdown",
        parallax_factor=common_types.OrderedPair(1.0, 1.0),
        tiled_objects=[],
    ),
]
